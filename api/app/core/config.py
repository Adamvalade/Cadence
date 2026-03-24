from urllib.parse import urlparse

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cadence:cadence@localhost:5432/cadence"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    # Must match Spotify app Redirect URIs exactly. Spotify treats https://localhost as "insecure" in
    # Safari and newer rules — use https://127.0.0.1:8000/... (see bin/ssl-localhost.sh).
    SPOTIFY_REDIRECT_URI: str = "https://127.0.0.1:8000/auth/spotify/callback"
    # ISO 3166-1 alpha-2; client-credentials search/catalog calls need a market
    SPOTIFY_MARKET: str = "US"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    ENVIRONMENT: str = "development"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    @property
    def access_token_cookie_samesite(self) -> str:
        # SameSite=None requires Secure; only use in production over HTTPS.
        return "lax"

    @property
    def access_token_cookie_secure(self) -> bool:
        # Browsers ignore Secure cookies set over plain HTTP — dev APIs are usually http://,
        # so forcing Secure=True breaks session cookies entirely while JSON login still "works".
        return self.is_production

    @property
    def cors_allow_origins(self) -> list[str]:
        """Origins allowed for credentialed CORS (must list exact browser origins)."""
        primary = self.FRONTEND_URL.rstrip("/")
        if self.is_production:
            return [primary]
        origins = {primary}
        parsed = urlparse(self.FRONTEND_URL)
        host, port = parsed.hostname, parsed.port
        scheme = parsed.scheme or "http"
        if host == "localhost" and port:
            origins.add(f"{scheme}://127.0.0.1:{port}")
        elif host == "127.0.0.1" and port:
            origins.add(f"{scheme}://localhost:{port}")
        return sorted(origins)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
