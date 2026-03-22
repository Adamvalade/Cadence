import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import settings
from app.schemas.album import AlbumSearchResult


class SpotifyService:
    def __init__(self):
        if settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
            auth_manager = SpotifyClientCredentials(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager)
        else:
            self._sp = None

    def search_albums(self, query: str, limit: int = 20) -> list[AlbumSearchResult]:
        if not self._sp:
            return []

        results = self._sp.search(q=query, type="album", limit=limit)
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

        try:
            album = self._sp.album(spotify_id)
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
        # prefer ~300px wide image, fall back to first
        for img in images:
            if img.get("width") and 200 <= img["width"] <= 400:
                return img["url"]
        return images[0].get("url")
