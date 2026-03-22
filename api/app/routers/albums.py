import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.album import Album
from app.models.review import Review
from app.models.user import User
from app.schemas.album import AlbumCreate, AlbumResponse, AlbumSearchResult
from app.services.spotify import SpotifyService

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
    spotify = SpotifyService()
    results = spotify.search_albums(q)

    spotify_ids = [r.spotify_id for r in results]
    existing = await db.execute(select(Album).where(Album.spotify_id.in_(spotify_ids)))
    existing_map = {a.spotify_id: str(a.id) for a in existing.scalars().all()}

    for r in results:
        r.existing_id = existing_map.get(r.spotify_id)

    return results


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
    _current_user: User = Depends(get_current_user),
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
