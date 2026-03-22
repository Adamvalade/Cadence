from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Cadence API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import auth, users, albums, reviews, follows, feed, lists

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(albums.router, prefix="/albums", tags=["albums"])
    app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
    app.include_router(follows.router, tags=["follows"])
    app.include_router(feed.router, prefix="/feed", tags=["feed"])
    app.include_router(lists.router, prefix="/lists", tags=["lists"])

    @app.get("/health")
    def health():
        return {"ok": True, "service": "cadence-api"}

    return app
