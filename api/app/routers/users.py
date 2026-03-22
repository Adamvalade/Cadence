from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.follow import Follow
from app.models.review import Review
from app.models.user import User
from app.schemas.user import UserProfile, UserUpdate

router = APIRouter()


@router.get("/{username}", response_model=UserProfile)
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    review_count = (await db.execute(select(func.count()).where(Review.user_id == user.id))).scalar() or 0
    follower_count = (
        await db.execute(select(func.count()).where(Follow.following_id == user.id))
    ).scalar() or 0
    following_count = (
        await db.execute(select(func.count()).where(Follow.follower_id == user.id))
    ).scalar() or 0

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
    )


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

    review_count = (await db.execute(select(func.count()).where(Review.user_id == current_user.id))).scalar() or 0
    follower_count = (
        await db.execute(select(func.count()).where(Follow.following_id == current_user.id))
    ).scalar() or 0
    following_count = (
        await db.execute(select(func.count()).where(Follow.follower_id == current_user.id))
    ).scalar() or 0

    return UserProfile(
        id=str(current_user.id),
        username=current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        bio=current_user.bio,
        created_at=current_user.created_at,
        review_count=review_count,
        follower_count=follower_count,
        following_count=following_count,
    )
