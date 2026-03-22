from datetime import datetime

from pydantic import BaseModel, Field


class AlbumCreate(BaseModel):
    title: str = Field(max_length=300)
    artist: str = Field(max_length=300)
    release_year: int | None = None
    cover_image_url: str | None = None
    genre: str | None = None


class AlbumResponse(BaseModel):
    id: str
    spotify_id: str | None = None
    title: str
    artist: str
    release_year: int | None = None
    cover_image_url: str | None = None
    genre: str | None = None
    created_at: datetime
    avg_rating: float | None = None
    review_count: int = 0

    model_config = {"from_attributes": True}


class AlbumSearchResult(BaseModel):
    spotify_id: str
    title: str
    artist: str
    release_year: int | None = None
    cover_image_url: str | None = None
    existing_id: str | None = None
