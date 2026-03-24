import threading

import spotipy
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import settings
from app.schemas.album import AlbumSearchResult

# Spotify GET /search: limit max 10 per item type (Web API reference, not Spotipy default).
_SPOTIFY_SEARCH_LIMIT_MAX = 10


def _resolve_spotify_track_id(item: dict) -> str | None:
    """Album track items often omit `id` or put the real id under `linked_from` (market / linking)."""
    tid = item.get("id")
    if isinstance(tid, str) and tid.strip():
        return tid.strip()
    linked = item.get("linked_from") or {}
    if isinstance(linked, dict):
        lid = linked.get("id")
        if isinstance(lid, str) and lid.strip():
            return lid.strip()
    uri = item.get("uri") or ""
    if isinstance(uri, str) and uri.startswith("spotify:track:"):
        parts = uri.split(":")
        if len(parts) >= 3 and parts[2]:
            return parts[2]
    return None

# One client + in-memory token cache: avoids concurrent .cache file corruption when
# many requests each did SpotifyService() + default CacheFileHandler (same .cache path).
_init_lock = threading.Lock()
_spotify: spotipy.Spotify | None = None


def _get_spotify() -> spotipy.Spotify | None:
    global _spotify
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        return None
    if _spotify is None:
        with _init_lock:
            if _spotify is None:
                auth = SpotifyClientCredentials(
                    client_id=settings.SPOTIFY_CLIENT_ID,
                    client_secret=settings.SPOTIFY_CLIENT_SECRET,
                    cache_handler=MemoryCacheHandler(),
                )
                _spotify = spotipy.Spotify(
                    auth_manager=auth,
                    requests_session=True,
                    retries=2,
                    status_retries=2,
                    requests_timeout=15,
                )
    return _spotify


class SpotifyService:
    def __init__(self):
        self._sp = _get_spotify()

    def search_albums(self, query: str, limit: int = _SPOTIFY_SEARCH_LIMIT_MAX) -> list[AlbumSearchResult]:
        if not self._sp:
            return []

        lim = max(1, min(int(limit), _SPOTIFY_SEARCH_LIMIT_MAX))
        market = settings.SPOTIFY_MARKET.strip() or "US"

        results = self._sp.search(
            q=query,
            type="album",
            limit=lim,
            offset=0,
            market=market,
        )
        albums = results.get("albums", {}).get("items", [])

        return [
            AlbumSearchResult(
                spotify_id=album["id"],
                title=album["name"],
                artist=", ".join(a["name"] for a in album.get("artists", [])),
                release_year=self._parse_year(album.get("release_date", "")),
                cover_image_url=self._best_image(album.get("images", [])),
            )
            for album in albums
        ]

    def get_album(self, spotify_id: str) -> dict | None:
        if not self._sp:
            return None

        market = settings.SPOTIFY_MARKET.strip() or "US"
        try:
            album = self._sp.album(spotify_id, market=market)
        except Exception:
            return None

        return {
            "spotify_id": album["id"],
            "title": album["name"],
            "artist": ", ".join(a["name"] for a in album.get("artists", [])),
            "release_year": self._parse_year(album.get("release_date", "")),
            "cover_image_url": self._best_image(album.get("images", [])),
            "genre": ", ".join(album.get("genres", [])[:3]) or None,
        }

    def get_album_tracks(self, spotify_album_id: str) -> list[dict]:
        """Paginate Spotify album tracks (50 per page)."""
        if not self._sp:
            return []

        market = settings.SPOTIFY_MARKET.strip() or "US"
        out: list[dict] = []
        offset = 0
        page_limit = 50
        while True:
            page = self._sp.album_tracks(
                spotify_album_id,
                limit=page_limit,
                offset=offset,
                market=market,
            )
            items = page.get("items") or []
            for t in items:
                tid = _resolve_spotify_track_id(t)
                if not tid:
                    continue
                out.append(
                    {
                        "spotify_track_id": tid,
                        "title": t.get("name") or "Unknown",
                        "disc_number": int(t.get("disc_number") or 1),
                        "track_number": int(t.get("track_number") or 0),
                    }
                )
            if not page.get("next"):
                break
            offset += len(items)
            if not items:
                break
        return out

    def search_tracks(self, query: str, limit: int = _SPOTIFY_SEARCH_LIMIT_MAX) -> list[dict]:
        if not self._sp:
            return []
        lim = max(1, min(int(limit), _SPOTIFY_SEARCH_LIMIT_MAX))
        market = settings.SPOTIFY_MARKET.strip() or "US"
        results = self._sp.search(q=query, type="track", limit=lim, offset=0, market=market)
        items = (results.get("tracks") or {}).get("items") or []
        out: list[dict] = []
        for t in items:
            tid = _resolve_spotify_track_id(t)
            if not tid:
                continue
            alb = t.get("album") or {}
            out.append(
                {
                    "spotify_track_id": tid,
                    "title": t.get("name") or "Unknown",
                    "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                    "album_title": alb.get("name"),
                    "cover_image_url": self._best_image(alb.get("images") or []),
                }
            )
        return out

    def get_track_public_meta(self, spotify_track_id: str) -> dict | None:
        if not self._sp:
            return None
        market = settings.SPOTIFY_MARKET.strip() or "US"
        try:
            t = self._sp.track(spotify_track_id, market=market)
        except Exception:
            return None
        alb = t.get("album") or {}
        return {
            "spotify_track_id": t.get("id") or spotify_track_id,
            "title": t.get("name") or "Unknown",
            "artist": ", ".join(a["name"] for a in t.get("artists", [])),
            "album_title": alb.get("name"),
            "cover_image_url": self._best_image(alb.get("images") or []),
        }

    @staticmethod
    def _parse_year(date_str: str) -> int | None:
        if not date_str:
            return None
        try:
            return int(date_str[:4])
        except ValueError:
            return None

    @staticmethod
    def _best_image(images: list[dict]) -> str | None:
        if not images:
            return None
        for img in images:
            if img.get("width") and 200 <= img["width"] <= 400:
                return img["url"]
        return images[0].get("url")
