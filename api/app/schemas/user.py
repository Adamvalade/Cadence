from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UserRatingStats(BaseModel):
    album_ratings_count: int = 0
    album_ratings_average: float | None = None
    song_ratings_count: int = 0
    song_ratings_average: float | None = None
    combined_rating_distribution: dict[str, int] = Field(
        default_factory=lambda: {str(i): 0 for i in range(1, 11)}
    )


class UserTrackRatingPublic(BaseModel):
    """A single track rating shown on a user profile or review expand."""

    track_id: str
    spotify_track_id: str
    title: str
    disc_number: int
    track_number: int
    rating: int
    album_id: str
    album_title: str
    album_artist: str


class FeaturedTrackPublic(BaseModel):
    slot: int
    spotify_track_id: str
    title: str
    artist: str
    album_title: str | None = None
    cover_image_url: str | None = None
    open_url: str


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
    rating_stats: UserRatingStats = Field(default_factory=UserRatingStats)
    featured_tracks: list[FeaturedTrackPublic] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)


class FeaturedTracksUpdate(BaseModel):
    """Up to 5 slots; index is the slot number (0–4). Use null to leave a slot empty."""

    slots: list[str | None] = Field(default_factory=list)

    @field_validator("slots")
    @classmethod
    def max_five_slots(cls, v: list[str | None]) -> list[str | None]:
        if len(v) > 5:
            raise ValueError("At most 5 featured song slots")
        return v
