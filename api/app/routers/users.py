import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.album import Album
from app.models.follow import Follow
from app.models.review import Review
from app.models.track import Track
from app.models.track_rating import TrackRating
from app.models.user import User
from app.models.user_featured_track import UserFeaturedTrack
from app.schemas.user import (
    FeaturedTrackPublic,
    FeaturedTracksUpdate,
    UserProfile,
    UserRatingStats,
    UserTrackRatingPublic,
    UserUpdate,
)
from app.services.spotify import SpotifyService

router = APIRouter()


async def _rating_stats_for_user(db: AsyncSession, user_id: uuid.UUID) -> UserRatingStats:
    rev_q = await db.execute(select(Review.rating).where(Review.user_id == user_id))
    rev = [row[0] for row in rev_q.all()]
    tr_q = await db.execute(select(TrackRating.rating).where(TrackRating.user_id == user_id))
    tr = [row[0] for row in tr_q.all()]

    dist = {str(i): 0 for i in range(1, 11)}
    for r in rev + tr:
        k = str(int(r))
        if k in dist:
            dist[k] += 1

    def avg(vals: list[int]) -> float | None:
        return round(sum(vals) / len(vals), 1) if vals else None

    return UserRatingStats(
        album_ratings_count=len(rev),
        album_ratings_average=avg(rev),
        song_ratings_count=len(tr),
        song_ratings_average=avg(tr),
        combined_rating_distribution=dist,
    )


async def _featured_public_list(db: AsyncSession, user_id: uuid.UUID) -> list[FeaturedTrackPublic]:
    r = await db.execute(
        select(UserFeaturedTrack)
        .where(UserFeaturedTrack.user_id == user_id)
        .order_by(UserFeaturedTrack.slot)
    )
    rows = list(r.scalars().all())
    return [
        FeaturedTrackPublic(
            slot=x.slot,
            spotify_track_id=x.spotify_track_id,
            title=x.title,
            artist=x.artist,
            album_title=x.album_title,
            cover_image_url=x.cover_image_url,
            open_url=f"https://open.spotify.com/track/{x.spotify_track_id}",
        )
        for x in rows
    ]


async def build_user_profile(db: AsyncSession, user: User) -> UserProfile:
    review_count = (await db.execute(select(func.count()).where(Review.user_id == user.id))).scalar() or 0
    follower_count = (
        await db.execute(select(func.count()).where(Follow.following_id == user.id))
    ).scalar() or 0
    following_count = (
        await db.execute(select(func.count()).where(Follow.follower_id == user.id))
    ).scalar() or 0
    stats = await _rating_stats_for_user(db, user.id)
    featured = await _featured_public_list(db, user.id)

    return UserProfile(
        id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        created_at=user.created_at,
        review_count=review_count,
        follower_count=follower_count,
        following_count=following_count,
        rating_stats=stats,
        featured_tracks=featured,
    )


@router.get("/{username}/track-ratings", response_model=list[UserTrackRatingPublic])
async def list_user_track_ratings(
    username: str,
    album_id: str | None = Query(default=None, description="Limit to one album (album UUID)"),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Public list of a user’s per-track ratings; optional filter by album."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stmt = (
        select(TrackRating, Track, Album)
        .join(Track, Track.id == TrackRating.track_id)
        .join(Album, Album.id == Track.album_id)
        .where(TrackRating.user_id == user.id)
    )
    if album_id:
        try:
            aid = uuid.UUID(album_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid album_id") from e
        stmt = stmt.where(Album.id == aid)
        stmt = stmt.order_by(Track.disc_number, Track.track_number, Track.title)
    else:
        stmt = stmt.order_by(TrackRating.updated_at.desc())

    rows = (await db.execute(stmt.limit(limit))).all()
    return [
        UserTrackRatingPublic(
            track_id=str(track.id),
            spotify_track_id=track.spotify_track_id,
            title=track.title,
            disc_number=track.disc_number,
            track_number=track.track_number,
            rating=tr.rating,
            album_id=str(album.id),
            album_title=album.title,
            album_artist=album.artist,
        )
        for tr, track, album in rows
    ]


@router.get("/{username}", response_model=UserProfile)
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await build_user_profile(db, user)


@router.patch("/me", response_model=UserProfile)
async def update_my_profile(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.display_name is not None:
        current_user.display_name = body.display_name
    if body.bio is not None:
        current_user.bio = body.bio
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url

    await db.commit()
    await db.refresh(current_user)

    return await build_user_profile(db, current_user)


@router.put("/me/featured-tracks", response_model=UserProfile)
async def update_my_featured_tracks(
    body: FeaturedTracksUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(delete(UserFeaturedTrack).where(UserFeaturedTrack.user_id == current_user.id))

    spotify = SpotifyService()
    for slot, spotify_id in enumerate(body.slots):
        if slot > 4:
            break
        if not spotify_id or not str(spotify_id).strip():
            continue
        sid = str(spotify_id).strip()
        meta = spotify.get_track_public_meta(sid)
        if not meta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not load track from Spotify: {sid}",
            )
        at = meta.get("album_title")
        album_title = (at[:300] if isinstance(at, str) and at.strip() else None)
        cu = meta.get("cover_image_url")
        cover = (cu[:500] if isinstance(cu, str) and cu.strip() else None)
        db.add(
            UserFeaturedTrack(
                user_id=current_user.id,
                slot=slot,
                spotify_track_id=meta["spotify_track_id"],
                title=(meta["title"] or "Unknown")[:500],
                artist=(meta["artist"] or "Unknown")[:300],
                album_title=album_title,
                cover_image_url=cover,
            )
        )

    await db.commit()

    return await build_user_profile(db, current_user)
