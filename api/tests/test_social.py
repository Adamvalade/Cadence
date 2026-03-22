import uuid

import pytest
from httpx import AsyncClient


async def _register_user(client: AsyncClient, suffix: str):
    r = await client.post("/auth/register", json={
        "email": f"social_{suffix}@cadence.app",
        "username": f"social_{suffix}",
        "password": "password123",
    })
    return dict(r.cookies), r.json()["user"]


@pytest.mark.asyncio
async def test_follow_unfollow(client):
    cookies_a, user_a = await _register_user(client, uuid.uuid4().hex[:6])
    cookies_b, user_b = await _register_user(client, uuid.uuid4().hex[:6])

    # A follows B
    r = await client.post(f"/users/{user_b['id']}/follow", cookies=cookies_a)
    assert r.status_code == 201

    # check followers of B
    r = await client.get(f"/users/{user_b['username']}/followers")
    assert len(r.json()) == 1
    assert r.json()[0]["username"] == user_a["username"]

    # check following of A
    r = await client.get(f"/users/{user_a['username']}/following")
    assert len(r.json()) == 1
    assert r.json()[0]["username"] == user_b["username"]

    # duplicate follow
    r = await client.post(f"/users/{user_b['id']}/follow", cookies=cookies_a)
    assert r.status_code == 409

    # unfollow
    r = await client.delete(f"/users/{user_b['id']}/follow", cookies=cookies_a)
    assert r.status_code == 204

    r = await client.get(f"/users/{user_b['username']}/followers")
    assert len(r.json()) == 0


@pytest.mark.asyncio
async def test_cannot_follow_self(client):
    cookies, user = await _register_user(client, uuid.uuid4().hex[:6])
    r = await client.post(f"/users/{user['id']}/follow", cookies=cookies)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed(client):
    cookies_a, user_a = await _register_user(client, f"feed_a_{uuid.uuid4().hex[:4]}")
    cookies_b, user_b = await _register_user(client, f"feed_b_{uuid.uuid4().hex[:4]}")

    # A follows B
    await client.post(f"/users/{user_b['id']}/follow", cookies=cookies_a)

    # B creates an album and review
    album_r = await client.post("/albums", json={
        "title": "Feed Test Album",
        "artist": "Feed Artist",
    }, cookies=cookies_b)
    album_id = album_r.json()["id"]

    await client.post("/reviews", json={
        "album_id": album_id,
        "rating": 7,
    }, cookies=cookies_b)

    # A checks feed
    r = await client.get("/feed", cookies=cookies_a)
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == user_b["username"]
    assert data["items"][0]["album_title"] == "Feed Test Album"


@pytest.mark.asyncio
async def test_user_profile(client):
    cookies, user = await _register_user(client, uuid.uuid4().hex[:6])

    r = await client.get(f"/users/{user['username']}")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == user["username"]
    assert data["review_count"] == 0
    assert data["follower_count"] == 0


@pytest.mark.asyncio
async def test_update_profile(client):
    cookies, user = await _register_user(client, uuid.uuid4().hex[:6])

    r = await client.patch("/users/me", json={
        "display_name": "New Name",
        "bio": "Hello world",
    }, cookies=cookies)
    assert r.status_code == 200
    assert r.json()["display_name"] == "New Name"
    assert r.json()["bio"] == "Hello world"
