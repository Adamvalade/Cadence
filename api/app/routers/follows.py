import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.follow import Follow
from app.models.user import User
from app.schemas.auth import UserBrief

router = APIRouter()


@router.post("/users/{user_id}/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = uuid.UUID(user_id)
    if target_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")

    target = await db.execute(select(User).where(User.id == target_id))
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already following")

    follow = Follow(follower_id=current_user.id, following_id=target_id)
    db.add(follow)
    await db.commit()
    return {"message": "Followed"}


@router.delete("/users/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = uuid.UUID(user_id)
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target_id)
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not following this user")

    await db.delete(follow)
    await db.commit()


@router.get("/users/{user_id}/follow/status")
async def follow_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = uuid.UUID(user_id)
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target_id)
    )
    return {"following": result.scalar_one_or_none() is not None}


@router.get("/users/{username}/followers", response_model=list[UserBrief])
async def get_followers(
    username: str,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.username == username))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user.id)
        .limit(limit)
        .offset(offset)
    )
    followers = result.scalars().all()
    return [
        UserBrief(id=str(u.id), email=u.email, username=u.username, display_name=u.display_name, avatar_url=u.avatar_url)
        for u in followers
    ]


@router.get("/users/{username}/following", response_model=list[UserBrief])
async def get_following(
    username: str,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.username == username))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user.id)
        .limit(limit)
        .offset(offset)
    )
    following = result.scalars().all()
    return [
        UserBrief(id=str(u.id), email=u.email, username=u.username, display_name=u.display_name, avatar_url=u.avatar_url)
        for u in following
    ]
