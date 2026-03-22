import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow
from app.models.like import Like
from app.models.review import Review
from app.schemas.review import ReviewResponse


async def get_feed_items(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[ReviewResponse], bool, str | None]:
    following_ids = select(Follow.following_id).where(Follow.follower_id == user_id)

    query = (
        select(Review)
        .where(Review.user_id.in_(following_ids))
        .order_by(Review.created_at.desc())
    )

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Review.created_at < cursor_dt)
        except ValueError:
            pass

    query = query.limit(limit + 1)

    result = await db.execute(query)
    reviews = list(result.scalars().all())

    has_more = len(reviews) > limit
    if has_more:
        reviews = reviews[:limit]

    next_cursor = reviews[-1].created_at.isoformat() if has_more and reviews else None

    items = []
    for review in reviews:
        like_count = (await db.execute(select(func.count()).where(Like.review_id == review.id))).scalar() or 0
        liked = await db.execute(
            select(Like).where(Like.review_id == review.id, Like.user_id == user_id)
        )
        liked_by_me = liked.scalar_one_or_none() is not None

        items.append(
            ReviewResponse(
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
            )
        )

    return items, has_more, next_cursor
