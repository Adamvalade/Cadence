from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cadence:cadence@localhost:5432/cadence"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/auth/spotify/callback"
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

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
