import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, get_optional_user
from app.models.album import Album
from app.models.like import Like
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate

router = APIRouter()


def _review_response(review: Review, like_count: int = 0, liked_by_me: bool = False) -> ReviewResponse:
    return ReviewResponse(
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


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album_result = await db.execute(select(Album).where(Album.id == uuid.UUID(body.album_id)))
    if not album_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")

    existing = await db.execute(
        select(Review).where(Review.user_id == current_user.id, Review.album_id == uuid.UUID(body.album_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already reviewed this album")

    review = Review(
        user_id=current_user.id,
        album_id=uuid.UUID(body.album_id),
        rating=body.rating,
        body=body.body,
        is_relisten=body.is_relisten,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return _review_response(review)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    result = await db.execute(select(Review).where(Review.id == uuid.UUID(review_id)))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    like_count = (await db.execute(select(func.count()).where(Like.review_id == review.id))).scalar() or 0
    liked_by_me = False
    if current_user:
        liked = await db.execute(
            select(Like).where(Like.review_id == review.id, Like.user_id == current_user.id)
        )
        liked_by_me = liked.scalar_one_or_none() is not None

    return _review_response(review, like_count=like_count, liked_by_me=liked_by_me)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    body: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Review).where(Review.id == uuid.UUID(review_id)))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your review")

    if body.rating is not None:
        review.rating = body.rating
    if body.body is not None:
        review.body = body.body
    if body.is_relisten is not None:
        review.is_relisten = body.is_relisten

    await db.commit()
    await db.refresh(review)
    return _review_response(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Review).where(Review.id == uuid.UUID(review_id)))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your review")

    await db.delete(review)
    await db.commit()


@router.get("", response_model=list[ReviewResponse])
async def get_user_reviews(
    username: str = Query(...),
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.username == username))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(Review)
        .where(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    reviews = result.scalars().all()
    return [_review_response(r) for r in reviews]


@router.post("/{review_id}/like", status_code=status.HTTP_201_CREATED)
async def like_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review_result = await db.execute(select(Review).where(Review.id == uuid.UUID(review_id)))
    if not review_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    existing = await db.execute(
        select(Like).where(Like.review_id == uuid.UUID(review_id), Like.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already liked")

    like = Like(user_id=current_user.id, review_id=uuid.UUID(review_id))
    db.add(like)
    await db.commit()
    return {"message": "Liked"}


@router.delete("/{review_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Like).where(Like.review_id == uuid.UUID(review_id), Like.user_id == current_user.id)
    )
    like = result.scalar_one_or_none()
    if not like:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found")

    await db.delete(like)
    await db.commit()
