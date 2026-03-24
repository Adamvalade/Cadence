from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    album_id: str
    rating: int = Field(ge=1, le=10)
    body: str | None = None
    is_relisten: bool = False


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=10)
    body: str | None = None
    is_relisten: bool | None = None


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    album_id: str
    rating: int
    body: str | None = None
    is_relisten: bool
    created_at: datetime
    updated_at: datetime
    like_count: int = 0
    liked_by_me: bool = False

    username: str = ""
    user_avatar_url: str | None = None
    album_title: str = ""
    album_artist: str = ""
    album_cover_url: str | None = None

    # Same reviewer’s per-track ratings on this album (if any).
    album_track_rating_count: int = 0
    album_track_rating_average: float | None = None

    model_config = {"from_attributes": True}
