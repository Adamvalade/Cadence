from pydantic import BaseModel, Field


class TrackRatingUpsert(BaseModel):
    rating: int = Field(ge=1, le=10)


class AlbumTrackResponse(BaseModel):
    id: str
    spotify_track_id: str
    title: str
    disc_number: int
    track_number: int
    my_rating: int | None = None

    model_config = {"from_attributes": True}


class AlbumTracksPayload(BaseModel):
    tracks: list[AlbumTrackResponse]
    track_count: int
    my_rated_count: int
    my_track_average: float | None = None
