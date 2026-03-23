import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.album import Album
from app.models.list import List, ListItem
from app.models.user import User
from pydantic import BaseModel, Field

router = APIRouter()


class ListCreate(BaseModel):
    title: str = Field(max_length=200)
    description: str | None = None
    is_public: bool = True


class ListItemAdd(BaseModel):
    album_id: str
    position: int = 0


class ListItemResponse(BaseModel):
    id: str
    album_id: str
    position: int
    album_title: str = ""
    album_artist: str = ""
    album_cover_url: str | None = None

    model_config = {"from_attributes": True}


class ListResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None = None
    is_public: bool
    created_at: str
    items: list[ListItemResponse] = []

    model_config = {"from_attributes": True}


@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    body: ListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_list = List(user_id=current_user.id, title=body.title, description=body.description, is_public=body.is_public)
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    return ListResponse(
        id=str(new_list.id),
        user_id=str(new_list.user_id),
        title=new_list.title,
        description=new_list.description,
        is_public=new_list.is_public,
        created_at=new_list.created_at.isoformat(),
    )


@router.get("/{list_id}", response_model=ListResponse)
async def get_list(list_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(List).where(List.id == uuid.UUID(list_id)))
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    items_result = await db.execute(
        select(ListItem).where(ListItem.list_id == lst.id).order_by(ListItem.position)
    )
    items = items_result.scalars().all()

    item_responses = []
    for item in items:
        album_result = await db.execute(select(Album).where(Album.id == item.album_id))
        album = album_result.scalar_one_or_none()
        item_responses.append(
            ListItemResponse(
                id=str(item.id),
                album_id=str(item.album_id),
                position=item.position,
                album_title=album.title if album else "",
                album_artist=album.artist if album else "",
                album_cover_url=album.cover_image_url if album else None,
            )
        )

    return ListResponse(
        id=str(lst.id),
        user_id=str(lst.user_id),
        title=lst.title,
        description=lst.description,
        is_public=lst.is_public,
        created_at=lst.created_at.isoformat(),
        items=item_responses,
    )


@router.post("/{list_id}/items", status_code=status.HTTP_201_CREATED)
async def add_to_list(
    list_id: str,
    body: ListItemAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(List).where(List.id == uuid.UUID(list_id)))
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    if lst.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your list")

    item = ListItem(list_id=lst.id, album_id=uuid.UUID(body.album_id), position=body.position)
    db.add(item)
    await db.commit()
    return {"message": "Added to list"}


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(List).where(List.id == uuid.UUID(list_id)))
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    if lst.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your list")

    await db.delete(lst)
    await db.commit()


@router.get("/mine", response_model=list[ListResponse])
async def get_my_lists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(List).where(List.user_id == current_user.id).order_by(List.created_at.desc())
    )
    lists = result.scalars().all()
    return [
        ListResponse(
            id=str(lst.id),
            user_id=str(lst.user_id),
            title=lst.title,
            description=lst.description,
            is_public=lst.is_public,
            created_at=lst.created_at.isoformat(),
        )
        for lst in lists
    ]


@router.get("", response_model=list[ListResponse])
async def get_user_lists(
    username: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.username == username))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(List).where(List.user_id == user.id, List.is_public.is_(True)).order_by(List.created_at.desc())
    )
    lists = result.scalars().all()
    return [
        ListResponse(
            id=str(lst.id),
            user_id=str(lst.user_id),
            title=lst.title,
            description=lst.description,
            is_public=lst.is_public,
            created_at=lst.created_at.isoformat(),
        )
        for lst in lists
    ]
