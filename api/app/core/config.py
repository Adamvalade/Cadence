from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Reject these in production (see validate_production_settings).
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
    # Loaded for env/Compose parity with Spotify dashboard; album search uses client credentials only.
    SPOTIFY_REDIRECT_URI: str = ""
    # ISO 3166-1 alpha-2; client-credentials search/catalog calls need a market
    SPOTIFY_MARKET: str = "US"

    # Password reset emails via https://resend.com (optional; without these, link is only logged in dev)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    ENVIRONMENT: str = "development"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Comma-separated hostnames for TrustedHostMiddleware in production (e.g. "api.example.com").
    # Empty = middleware disabled (e.g. Docker internal hostname varies).
    TRUSTED_HOSTS: str = ""

    # Optional override for the URL prefix of all routers (e.g. "/api"). Usually leave unset: if
    # NEXT_PUBLIC_API_URL ends with .../api, we mount at /api automatically (see api_router_mount_prefix).
    API_ROOT_PATH: str = ""

    # Browser-visible API base (same value as web’s NEXT_PUBLIC_API_URL). Used in Docker to infer /api mount.
    NEXT_PUBLIC_API_URL: str = ""

    # If true, never infer /api from NEXT_PUBLIC_API_URL (use when the edge strips /api before the container).
    API_FORCE_NO_PREFIX: bool = False

    # Optional error reporting (initialized in api/main.py before create_app).
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    # Demo account: POST /auth/demo-login (404 when disabled). Use a dedicated email; min 8-char password.
    DEMO_LOGIN_ENABLED: bool = False
    DEMO_USER_EMAIL: str = "demo@cadence.local"
    DEMO_USER_PASSWORD: str = ""
    DEMO_LOGIN_AUTO_CREATE: bool = True
    # When demo login is configured, seed fake friends + reviews at API startup (idempotent).
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
        """Path prefix for all app routers (e.g. /api). /health and / stay at the app root."""
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

    @property
    def trusted_hosts_list(self) -> list[str]:
        raw = self.TRUSTED_HOSTS.strip()
        if not raw:
            return []
        return [h.strip() for h in raw.split(",") if h.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def assert_safe_for_production(*, environment: str, secret_key: str, frontend_url: str) -> None:
    """Fail fast on unsafe defaults when environment is production (testable without env reload)."""
    if environment != "production":
        return
    sk = secret_key.strip()
    if sk in WEAK_SECRET_KEYS or len(sk) < MIN_PRODUCTION_SECRET_KEY_LEN:
        raise RuntimeError(
            "Production requires SECRET_KEY: at least 32 characters and not a known placeholder. "
            'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    front = frontend_url.lower().strip().rstrip("/")
    if front.startswith("http://") and not (
        front.startswith("http://localhost") or front.startswith("http://127.0.0.1")
    ):
        raise RuntimeError(
            "Production FRONTEND_URL must use https:// except for http://localhost or http://127.0.0.1 "
            "(local smoke tests)."
        )


def validate_production_settings() -> None:
    assert_safe_for_production(
        environment=settings.ENVIRONMENT,
        secret_key=settings.SECRET_KEY,
        frontend_url=settings.FRONTEND_URL,
    )
