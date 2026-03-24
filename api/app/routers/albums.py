import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_optional_user
from app.models.album import Album
from app.models.review import Review
from app.models.track import Track
from app.models.track_rating import TrackRating
from app.models.user import User
from app.schemas.album import AlbumCreate, AlbumResponse, AlbumSearchResult
from app.schemas.track import AlbumTrackResponse, AlbumTracksPayload, TrackRatingUpsert
from app.services.spotify import SpotifyService

logger = logging.getLogger(__name__)

router = APIRouter()


def _album_response(album: Album, avg_rating: float | None = None, review_count: int = 0) -> AlbumResponse:
    return AlbumResponse(
        id=str(album.id),
        spotify_id=album.spotify_id,
        title=album.title,
        artist=album.artist,
        release_year=album.release_year,
        cover_image_url=album.cover_image_url,
        genre=album.genre,
        created_at=album.created_at,
        avg_rating=avg_rating,
        review_count=review_count,
    )


@router.get("/search", response_model=list[AlbumSearchResult])
async def search_albums(q: str = Query(min_length=1), db: AsyncSession = Depends(get_db)):
    try:
        spotify = SpotifyService()
        results = spotify.search_albums(q)
    except Exception:
        logger.exception("Spotify search failed for query=%r", q)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spotify search is temporarily unavailable. Check API credentials and try again.",
        ) from None

    if not results:
        return results

    spotify_ids = [r.spotify_id for r in results if r.spotify_id]
    if not spotify_ids:
        return results

    try:
        existing = await db.execute(select(Album).where(Album.spotify_id.in_(spotify_ids)))
        existing_map = {a.spotify_id: str(a.id) for a in existing.scalars().all()}
    except Exception:
        logger.exception("Database lookup failed during album search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not look up albums in the database.",
        ) from None

    for r in results:
        r.existing_id = existing_map.get(r.spotify_id)

    return results


async def _ensure_tracks_synced(db: AsyncSession, album: Album, album_pk: uuid.UUID) -> None:
    """Use album_pk for FK filters — album may expire after commit(); lazy-loading album.id breaks async."""
    existing_count = await db.scalar(select(func.count()).select_from(Track).where(Track.album_id == album_pk))
    if existing_count and existing_count > 0:
        return

    if album.tracks_synced_at is not None:
        return

    now = datetime.now(timezone.utc)

    if not album.spotify_id:
        album.tracks_synced_at = now
        await db.commit()
        await db.refresh(album)
        return

    spotify = SpotifyService()
    try:
        raw = spotify.get_album_tracks(album.spotify_id)
    except Exception:
        logger.exception("Spotify album_tracks failed for album id=%s", album_pk)
        return

    if not raw:
        album.tracks_synced_at = now
        await db.commit()
        await db.refresh(album)
        return

    for t in raw:
        db.add(
            Track(
                album_id=album_pk,
                spotify_track_id=t["spotify_track_id"],
                title=(t["title"] or "Unknown")[:500],
                disc_number=t["disc_number"],
                track_number=t["track_number"],
            )
        )
    album.tracks_synced_at = now
    try:
        await db.commit()
        await db.refresh(album)
    except IntegrityError:
        await db.rollback()


@router.get("/{album_id}/tracks", response_model=AlbumTracksPayload)
async def get_album_tracks(
    album_id: str,
    refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    # Capture before any commit() — commits expire ORM instances; accessing current_user.id later can
    # trigger a sync lazy load and raise MissingGreenlet in async SQLAlchemy.
    viewer_id: uuid.UUID | None = current_user.id if current_user else None

    aid = uuid.UUID(album_id)
    result = await db.execute(select(Album).where(Album.id == aid))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")

    if refresh:
        await db.execute(delete(Track).where(Track.album_id == aid))
        album.tracks_synced_at = None
        await db.commit()
        await db.refresh(album)

    await _ensure_tracks_synced(db, album, aid)

    tracks_result = await db.execute(
        select(Track)
        .where(Track.album_id == aid)
        .order_by(Track.disc_number, Track.track_number, Track.title)
    )
    track_list = list(tracks_result.scalars().all())

    ratings_map: dict[uuid.UUID, int] = {}
    if viewer_id is not None and track_list:
        ids = [t.id for t in track_list]
        ratings_rows = await db.execute(
            select(TrackRating).where(
                TrackRating.user_id == viewer_id,
                TrackRating.track_id.in_(ids),
            )
        )
        for tr in ratings_rows.scalars().all():
            ratings_map[tr.track_id] = tr.rating

    items = [
        AlbumTrackResponse(
            id=str(t.id),
            spotify_track_id=t.spotify_track_id,
            title=t.title,
            disc_number=t.disc_number,
            track_number=t.track_number,
            my_rating=ratings_map.get(t.id),
        )
        for t in track_list
    ]
    rated_values = [ratings_map[t.id] for t in track_list if t.id in ratings_map]
    my_avg = round(sum(rated_values) / len(rated_values), 1) if rated_values else None

    return AlbumTracksPayload(
        tracks=items,
        track_count=len(items),
        my_rated_count=len(rated_values),
        my_track_average=my_avg,
    )


@router.put("/{album_id}/tracks/{track_id}/rating", response_model=AlbumTrackResponse)
async def upsert_track_rating(
    album_id: str,
    track_id: str,
    body: TrackRatingUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.id
    album_result = await db.execute(select(Album).where(Album.id == uuid.UUID(album_id)))
    if not album_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")

    track_result = await db.execute(select(Track).where(Track.id == uuid.UUID(track_id)))
    track = track_result.scalar_one_or_none()
    aid = uuid.UUID(album_id)
    if not track or track.album_id != aid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    existing = await db.execute(
        select(TrackRating).where(
            TrackRating.user_id == uid,
            TrackRating.track_id == track.id,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.rating = body.rating
    else:
        row = TrackRating(user_id=uid, track_id=track.id, rating=body.rating)
        db.add(row)
    await db.commit()
    await db.refresh(row)

    return AlbumTrackResponse(
        id=str(track.id),
        spotify_track_id=track.spotify_track_id,
        title=track.title,
        disc_number=track.disc_number,
        track_number=track.track_number,
        my_rating=row.rating,
    )


@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(album_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Album).where(Album.id == uuid.UUID(album_id)))
    album = result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")

    stats = await db.execute(
        select(func.avg(Review.rating), func.count()).where(Review.album_id == album.id)
    )
    row = stats.one()
    avg_rating = round(float(row[0]), 1) if row[0] else None

    return _album_response(album, avg_rating=avg_rating, review_count=row[1])


@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def create_album(
    body: AlbumCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    album = Album(
        title=body.title,
        artist=body.artist,
        release_year=body.release_year,
        cover_image_url=body.cover_image_url,
        genre=body.genre,
    )
    db.add(album)
    await db.commit()
    await db.refresh(album)
    return _album_response(album)


@router.post("/import/{spotify_id}", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def import_from_spotify(
    spotify_id: str,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Album).where(Album.spotify_id == spotify_id))
    album = existing.scalar_one_or_none()
    if album:
        return _album_response(album)

    spotify = SpotifyService()
    album_data = spotify.get_album(spotify_id)
    if not album_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found on Spotify")

    album = Album(
        spotify_id=album_data["spotify_id"],
        title=album_data["title"],
        artist=album_data["artist"],
        release_year=album_data.get("release_year"),
        cover_image_url=album_data.get("cover_image_url"),
        genre=album_data.get("genre"),
    )
    db.add(album)
    await db.commit()
    await db.refresh(album)
    return _album_response(album)
