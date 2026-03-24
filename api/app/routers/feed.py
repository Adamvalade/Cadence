from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.feed import FeedResponse
from app.services.feed import get_feed_items

router = APIRouter()


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    limit: int = Query(default=20, le=50),
    cursor: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, has_more, next_cursor = await get_feed_items(db, current_user.id, limit=limit, cursor=cursor)
    return FeedResponse(items=items, has_more=has_more, next_cursor=next_cursor)
