"""Batch-load track-level rating stats for review authors on each album."""

import uuid
from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.models.track import Track
from app.models.track_rating import TrackRating


async def batch_album_track_rating_summaries(
    db: AsyncSession,
    reviews: Sequence[Review],
) -> dict[tuple[uuid.UUID, uuid.UUID], tuple[int, float | None]]:
    """Map (user_id, album_id) -> (count of track ratings on that album, average or None)."""
    if not reviews:
        return {}
    album_ids = {r.album_id for r in reviews}
    user_ids = {r.user_id for r in reviews}
    stmt = (
        select(TrackRating.user_id, Track.album_id, TrackRating.rating)
        .join(Track, Track.id == TrackRating.track_id)
        .where(Track.album_id.in_(album_ids), TrackRating.user_id.in_(user_ids))
    )
    result = await db.execute(stmt)
    bucket: dict[tuple[uuid.UUID, uuid.UUID], list[int]] = defaultdict(list)
    for user_id, album_id, rating in result.all():
        bucket[(user_id, album_id)].append(rating)
    out: dict[tuple[uuid.UUID, uuid.UUID], tuple[int, float | None]] = {}
    for key, vals in bucket.items():
        out[key] = (len(vals), round(sum(vals) / len(vals), 1))
    return out
