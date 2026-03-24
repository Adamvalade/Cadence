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
    def cross_scheme_localhost_dev(self) -> bool:
        """Next on http://localhost while API is https://localhost — different schemes = cross-site; Lax cookies skip fetch()."""
        if self.is_production:
            return False
        u = self.FRONTEND_URL.lower().strip()
        return u.startswith("http://localhost") or u.startswith("http://127.0.0.1")

    @property
    def access_token_cookie_samesite(self) -> str:
        return "none" if self.cross_scheme_localhost_dev else "lax"

    @property
    def access_token_cookie_secure(self) -> bool:
        if self.cross_scheme_localhost_dev:
            return True
        return self.cookie_secure

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
