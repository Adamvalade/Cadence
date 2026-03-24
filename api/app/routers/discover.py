import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_optional_user
from app.models.album import Album
from app.models.follow import Follow
from app.models.like import Like
from app.models.review import Review
from app.models.user import User
from app.schemas.album import AlbumResponse
from app.schemas.review import ReviewResponse

router = APIRouter()


class UserSearchResult(BaseModel):
    id: str
    username: str
    display_name: str
    avatar_url: str | None = None
    review_count: int = 0


@router.get("/trending-albums", response_model=list[AlbumResponse])
async def trending_albums(
    limit: int = Query(default=10, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Albums with the most reviews in the last 30 days."""
    subquery = (
        select(Review.album_id, func.count().label("cnt"))
        .group_by(Review.album_id)
        .order_by(func.count().desc())
        .limit(limit)
        .subquery()
    )

    result = await db.execute(
        select(Album, subquery.c.cnt)
        .join(subquery, Album.id == subquery.c.album_id)
        .order_by(subquery.c.cnt.desc())
    )
    rows = result.all()

    items = []
    for album, review_count in rows:
        avg = await db.execute(
            select(func.avg(Review.rating)).where(Review.album_id == album.id)
        )
        avg_val = avg.scalar()
        items.append(AlbumResponse(
            id=str(album.id),
            spotify_id=album.spotify_id,
            title=album.title,
            artist=album.artist,
            release_year=album.release_year,
            cover_image_url=album.cover_image_url,
            genre=album.genre,
            created_at=album.created_at,
            avg_rating=round(float(avg_val), 1) if avg_val else None,
            review_count=review_count,
        ))
    return items


@router.get("/popular-reviews", response_model=list[ReviewResponse])
async def popular_reviews(
    limit: int = Query(default=10, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Reviews with the most likes."""
    subquery = (
        select(Like.review_id, func.count().label("cnt"))
        .group_by(Like.review_id)
        .order_by(func.count().desc())
        .limit(limit)
        .subquery()
    )

    result = await db.execute(
        select(Review, subquery.c.cnt)
        .join(subquery, Review.id == subquery.c.review_id)
        .order_by(subquery.c.cnt.desc())
    )
    rows = result.all()

    items = []
    for review, like_count in rows:
        liked_by_me = False
        if current_user:
            liked = await db.execute(
                select(Like).where(Like.review_id == review.id, Like.user_id == current_user.id)
            )
            liked_by_me = liked.scalar_one_or_none() is not None

        items.append(ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            album_id=str(review.album_id),
            rating=review.rating,
            body=review.body,
            is_relisten=review.is_relisten,
            created_at=review.created_at,
            updated_at=review.updated_at,
            like_count=like_count,
            liked_by_me=liked_by_me,
            username=review.user.username if review.user else "",
            user_avatar_url=review.user.avatar_url if review.user else None,
            album_title=review.album.title if review.album else "",
            album_artist=review.album.artist if review.album else "",
            album_cover_url=review.album.cover_image_url if review.album else None,
        ))
    return items


@router.get("/recent-reviews", response_model=list[ReviewResponse])
async def recent_reviews(
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Most recent reviews from all users."""
    result = await db.execute(
        select(Review).order_by(Review.created_at.desc()).limit(limit)
    )
    reviews = result.scalars().all()

    items = []
    for review in reviews:
        like_count = (await db.execute(
            select(func.count()).where(Like.review_id == review.id)
        )).scalar() or 0

        liked_by_me = False
        if current_user:
            liked = await db.execute(
                select(Like).where(Like.review_id == review.id, Like.user_id == current_user.id)
            )
            liked_by_me = liked.scalar_one_or_none() is not None

        items.append(ReviewResponse(
            id=str(review.id),
            user_id=str(review.user_id),
            album_id=str(review.album_id),
            rating=review.rating,
            body=review.body,
            is_relisten=review.is_relisten,
            created_at=review.created_at,
            updated_at=review.updated_at,
            like_count=like_count,
            liked_by_me=liked_by_me,
            username=review.user.username if review.user else "",
            user_avatar_url=review.user.avatar_url if review.user else None,
            album_title=review.album.title if review.album else "",
            album_artist=review.album.artist if review.album else "",
            album_cover_url=review.album.cover_image_url if review.album else None,
        ))
    return items


@router.get("/users", response_model=list[UserSearchResult])
async def search_users(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Search users by username or display name."""
    pattern = f"%{q}%"
    result = await db.execute(
        select(User)
        .where(User.username.ilike(pattern) | User.display_name.ilike(pattern))
        .limit(limit)
    )
    users = result.scalars().all()

    items = []
    for user in users:
        review_count = (await db.execute(
            select(func.count()).where(Review.user_id == user.id)
        )).scalar() or 0
        items.append(UserSearchResult(
            id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            review_count=review_count,
        ))
    return items


@router.get("/active-users", response_model=list[UserSearchResult])
async def active_users(
    limit: int = Query(default=16, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Users who have reviewed recently — entry points for the social graph."""
    latest_per_user = (
        select(Review.user_id, func.max(Review.created_at).label("last_review"))
        .group_by(Review.user_id)
        .subquery()
    )
    result = await db.execute(
        select(User)
        .join(latest_per_user, User.id == latest_per_user.c.user_id)
        .order_by(latest_per_user.c.last_review.desc())
        .limit(limit)
    )
    users = result.scalars().all()

    items = []
    for user in users:
        review_count = (await db.execute(
            select(func.count()).where(Review.user_id == user.id)
        )).scalar() or 0
        items.append(UserSearchResult(
            id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            review_count=review_count,
        ))
    return items
