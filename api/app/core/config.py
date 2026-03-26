from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings

WEAK_SECRET_KEYS = frozenset(
    {
        "change-me",
        "change-me-to-a-random-string",
        "dev-secret-change-in-production",
    }
)
MIN_PRODUCTION_SECRET_KEY_LEN = 32


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cadence:cadence@localhost:5432/cadence"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = ""
    SPOTIFY_MARKET: str = "US"

    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    ENVIRONMENT: str = "development"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    TRUSTED_HOSTS: str = ""

    API_ROOT_PATH: str = ""
    NEXT_PUBLIC_API_URL: str = ""
    API_FORCE_NO_PREFIX: bool = False

    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    DEMO_LOGIN_ENABLED: bool = False
    DEMO_USER_EMAIL: str = "demo@cadence.local"
    DEMO_USER_PASSWORD: str = ""
    DEMO_LOGIN_AUTO_CREATE: bool = True
    DEMO_SEED_AT_STARTUP: bool = True

    @field_validator("API_ROOT_PATH", mode="before")
    @classmethod
    def _normalize_api_root_path(cls, v: object) -> str:
        if v is None or v == "":
            return ""
        s = str(v).strip().rstrip("/")
        if not s:
            return ""
        return s if s.startswith("/") else f"/{s}"

    @field_validator("API_FORCE_NO_PREFIX", mode="before")
    @classmethod
    def _coerce_api_force_no_prefix(cls, v: object) -> bool:
        if isinstance(v, bool):
            return v
        if v is None or v == "":
            return False
        s = str(v).strip().lower()
        if s in ("0", "false", "no", "off", "n"):
            return False
        return s in ("1", "true", "yes", "on")

    @field_validator("DEMO_LOGIN_ENABLED", mode="before")
    @classmethod
    def _coerce_demo_login_enabled(cls, v: object) -> bool:
        if isinstance(v, bool):
            return v
        if v is None or v == "":
            return False
        s = str(v).strip().lower()
        if s in ("0", "false", "no", "off", "n"):
            return False
        return s in ("1", "true", "yes", "on")

    @property
    def api_router_mount_prefix(self) -> str:
        if self.API_FORCE_NO_PREFIX:
            return ""
        explicit = (self.API_ROOT_PATH or "").strip()
        if explicit:
            return self.API_ROOT_PATH
        pub = (self.NEXT_PUBLIC_API_URL or "").strip().rstrip("/")
        if pub.endswith("/api"):
            return "/api"
        return ""

    @property
    def demo_login_available(self) -> bool:
        return self.DEMO_LOGIN_ENABLED and len(self.DEMO_USER_PASSWORD.strip()) >= 8

    @property
    def demo_seed_at_startup_enabled(self) -> bool:
        return self.demo_login_available and self.DEMO_SEED_AT_STARTUP

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    @property
    def access_token_cookie_samesite(self) -> str:
        return "lax"

    @property
    def access_token_cookie_secure(self) -> bool:
        return self.is_production

    @property
    def cors_allow_origins(self) -> list[str]:
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

    @property
    def trusted_hosts_list(self) -> list[str]:
        raw = self.TRUSTED_HOSTS.strip()
        if not raw:
            return []
        return [h.strip() for h in raw.split(",") if h.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def assert_safe_for_production(*, environment: str, secret_key: str, frontend_url: str) -> None:
    if environment != "production":
        return
    sk = secret_key.strip()
    if sk in WEAK_SECRET_KEYS or len(sk) < MIN_PRODUCTION_SECRET_KEY_LEN:
        raise RuntimeError(
            "Production SECRET_KEY must be at least 32 characters and not a known placeholder."
        )
    front = frontend_url.lower().strip().rstrip("/")
    if front.startswith("http://") and not (
        front.startswith("http://localhost") or front.startswith("http://127.0.0.1")
    ):
        raise RuntimeError("Production FRONTEND_URL must use https:// (except localhost / 127.0.0.1).")


def validate_production_settings() -> None:
    assert_safe_for_production(
        environment=settings.ENVIRONMENT,
        secret_key=settings.SECRET_KEY,
        frontend_url=settings.FRONTEND_URL,
    )
