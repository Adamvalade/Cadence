import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings, validate_production_settings
from app.core.http_middleware import RequestIdMiddleware
from app.db.session import async_session

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.demo_seed_at_startup_enabled:
        try:
            from app.services.demo_seed import seed_demo_public_dataset

            async with async_session() as session:
                await seed_demo_public_dataset(session)
                await session.commit()
        except Exception:
            logger.exception("Demo dataset seed at startup failed")
    yield


async def _redis_reachable() -> bool:
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            return bool(await client.ping())
        finally:
            await client.aclose()
    except Exception:
        return False


def create_app() -> FastAPI:
    validate_production_settings()

    doc_kwargs = {}
    if settings.is_production:
        doc_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    app = FastAPI(title="Cadence API", lifespan=lifespan, **doc_kwargs)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        if isinstance(exc, StarletteHTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        if isinstance(exc, RequestValidationError):
            from fastapi.exception_handlers import request_validation_exception_handler

            return await request_validation_exception_handler(request, exc)
        if isinstance(exc, ResponseValidationError):
            from fastapi.exception_handlers import response_validation_exception_handler

            return await response_validation_exception_handler(request, exc)

        rid = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception", extra={"request_id": rid})
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)
    if settings.is_production and settings.trusted_hosts_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)

    from app.routers import auth, users, albums, reviews, follows, feed, lists, listen_status, discover, spotify_catalog

    api_routes = APIRouter()
    api_routes.include_router(auth.router, prefix="/auth", tags=["auth"])
    api_routes.include_router(spotify_catalog.router, prefix="/spotify", tags=["spotify"])
    api_routes.include_router(users.router, prefix="/users", tags=["users"])
    api_routes.include_router(albums.router, prefix="/albums", tags=["albums"])
    api_routes.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
    api_routes.include_router(follows.router, tags=["follows"])
    api_routes.include_router(feed.router, tags=["feed"])
    api_routes.include_router(lists.router, prefix="/lists", tags=["lists"])
    api_routes.include_router(listen_status.router, prefix="/listen-status", tags=["listen-status"])
    api_routes.include_router(discover.router, prefix="/discover", tags=["discover"])

    mount = settings.api_router_mount_prefix
    app.include_router(api_routes, prefix=mount)
    logger.info("Mounted API routers under prefix %r", mount if mount else "")

    @app.get("/")
    async def root():
        payload = {
            "service": "cadence-api",
            "health": "/health",
            "hint": "The web app runs separately (e.g. http://localhost:3000).",
        }
        if not settings.is_production:
            payload["docs"] = "/docs"
        return payload

    @app.get("/health")
    async def health():
        from sqlalchemy import text

        from app.db.session import async_session

        db_ok = False
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
                db_ok = True
        except Exception:
            pass

        redis_ok = await _redis_reachable()

        body = {
            "ok": db_ok,
            "service": "cadence-api",
            "database": "connected" if db_ok else "unavailable",
            "redis": "connected" if redis_ok else "unavailable",
        }
        return JSONResponse(
            status_code=200 if db_ok else 503,
            content=body,
        )

    return app
