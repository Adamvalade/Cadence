from pydantic import BaseModel


class TrackSearchResult(BaseModel):
    spotify_track_id: str
    title: str
    artist: str
    album_title: str | None = None
    cover_image_url: str | None = None
