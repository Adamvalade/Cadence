import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.deps import get_db
from app.db.base import Base
from app.main import create_app
import app.models  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def _reset_db():
    import asyncio

    async def _setup():
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_setup())
    yield
    asyncio.run(_setup())


@pytest_asyncio.fixture
async def client():
    test_engine = create_async_engine(settings.DATABASE_URL, pool_size=5, max_overflow=10)
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _override_get_db():
        async with test_session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    await test_engine.dispose()


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    unique = uuid.uuid4().hex[:8]
    r = await client.post("/auth/register", json={
        "email": f"test_{unique}@cadence.app",
        "username": f"user_{unique}",
        "password": "testpass123",
        "display_name": f"Test {unique}",
    })
    assert r.status_code == 201
    cookies = dict(r.cookies)
    user_data = r.json()["user"]

    class AuthenticatedClient:
        def __init__(self, inner: AsyncClient, cookies: dict, user: dict):
            self._inner = inner
            self.cookies = cookies
            self.user = user

        async def get(self, url, **kw):
            return await self._inner.get(url, cookies=self.cookies, **kw)

        async def post(self, url, **kw):
            return await self._inner.post(url, cookies=self.cookies, **kw)

        async def patch(self, url, **kw):
            return await self._inner.patch(url, cookies=self.cookies, **kw)

        async def delete(self, url, **kw):
            return await self._inner.delete(url, cookies=self.cookies, **kw)

    return AuthenticatedClient(client, cookies, user_data)
