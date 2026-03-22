from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    id: str
    username: str
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime
    review_count: int = 0
    follower_count: int = 0
    following_count: int = 0

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
