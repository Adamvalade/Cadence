from pydantic import BaseModel

from app.schemas.review import ReviewResponse


class FeedResponse(BaseModel):
    items: list[ReviewResponse]
    has_more: bool
    next_cursor: str | None = None
