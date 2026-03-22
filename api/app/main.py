from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Cadence API", lifespan=lifespan)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import auth, users, albums, reviews, follows, feed, lists, listen_status, discover

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(albums.router, prefix="/albums", tags=["albums"])
    app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
    app.include_router(follows.router, tags=["follows"])
    app.include_router(feed.router, prefix="/feed", tags=["feed"])
    app.include_router(lists.router, prefix="/lists", tags=["lists"])
    app.include_router(listen_status.router, prefix="/listen-status", tags=["listen-status"])
    app.include_router(discover.router, prefix="/discover", tags=["discover"])

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

        return {
            "ok": db_ok,
            "service": "cadence-api",
            "database": "connected" if db_ok else "unavailable",
        }

    return app
