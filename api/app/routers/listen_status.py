import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.album import Album
from app.models.listen_status import ListenStatus
from app.models.user import User

router = APIRouter()

VALID_STATUSES = {"want_to_listen", "listening", "listened"}


class ListenStatusSet(BaseModel):
    album_id: str
    status: str = Field(pattern="^(want_to_listen|listening|listened)$")


class ListenStatusResponse(BaseModel):
    id: str
    album_id: str
    status: str
    album_title: str
    album_artist: str
    album_cover_url: str | None = None
    created_at: str
    updated_at: str


@router.put("", response_model=ListenStatusResponse)
async def set_listen_status(
    body: ListenStatusSet,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    album_id = uuid.UUID(body.album_id)
    album_result = await db.execute(select(Album).where(Album.id == album_id))
    album = album_result.scalar_one_or_none()
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")

    result = await db.execute(
        select(ListenStatus).where(
            ListenStatus.user_id == current_user.id,
            ListenStatus.album_id == album_id,
        )
    )
    ls = result.scalar_one_or_none()

    if ls:
        ls.status = body.status
    else:
        ls = ListenStatus(user_id=current_user.id, album_id=album_id, status=body.status)
        db.add(ls)

    await db.commit()
    await db.refresh(ls)

    return ListenStatusResponse(
        id=str(ls.id),
        album_id=str(ls.album_id),
        status=ls.status,
        album_title=album.title,
        album_artist=album.artist,
        album_cover_url=album.cover_image_url,
        created_at=ls.created_at.isoformat(),
        updated_at=ls.updated_at.isoformat(),
    )


@router.get("", response_model=list[ListenStatusResponse])
async def get_listen_statuses(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ListenStatus).where(ListenStatus.user_id == current_user.id)
    if status_filter and status_filter in VALID_STATUSES:
        query = query.where(ListenStatus.status == status_filter)
    query = query.order_by(ListenStatus.updated_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        ListenStatusResponse(
            id=str(ls.id),
            album_id=str(ls.album_id),
            status=ls.status,
            album_title=ls.album.title if ls.album else "",
            album_artist=ls.album.artist if ls.album else "",
            album_cover_url=ls.album.cover_image_url if ls.album else None,
            created_at=ls.created_at.isoformat(),
            updated_at=ls.updated_at.isoformat(),
        )
        for ls in items
    ]


@router.get("/{album_id}")
async def get_album_listen_status(
    album_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ListenStatus).where(
            ListenStatus.user_id == current_user.id,
            ListenStatus.album_id == uuid.UUID(album_id),
        )
    )
    ls = result.scalar_one_or_none()
    if not ls:
        return {"status": None}
    return {"status": ls.status}


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_listen_status(
    album_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ListenStatus).where(
            ListenStatus.user_id == current_user.id,
            ListenStatus.album_id == uuid.UUID(album_id),
        )
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")
    await db.delete(ls)
    await db.commit()
