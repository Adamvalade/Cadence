import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.spotify_catalog import TrackSearchResult
from app.services.spotify import SpotifyService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tracks/search", response_model=list[TrackSearchResult])
async def search_tracks(q: str = Query(min_length=1)):
    try:
        spotify = SpotifyService()
        rows = spotify.search_tracks(q)
    except Exception:
        logger.exception("Spotify track search failed for query=%r", q)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spotify search is temporarily unavailable.",
        ) from None
    return [TrackSearchResult(**r) for r in rows]
