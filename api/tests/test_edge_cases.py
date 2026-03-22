import uuid

import pytest


@pytest.mark.asyncio
async def test_malformed_uuid_album(client):
    r = await client.get("/albums/not-a-uuid")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_malformed_uuid_review(client):
    r = await client.get("/reviews/not-a-uuid")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_user_profile(client):
    r = await client.get("/users/absolutely_nobody_12345")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_user_reviews(client):
    r = await client.get("/reviews", params={"username": "ghost_user_99999"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reviews_require_filter(client):
    r = await client.get("/reviews")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_expired_token(client):
    r = await client.get("/auth/me", cookies={"access_token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalid"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_follow_nonexistent_user(client):
    suffix = uuid.uuid4().hex[:6]
    reg = await client.post("/auth/register", json={
        "email": f"edge_{suffix}@cadence.app",
        "username": f"edge_{suffix}",
        "password": "password123",
    })
    cookies = dict(reg.cookies)

    fake_id = str(uuid.uuid4())
    r = await client.post(f"/users/{fake_id}/follow", cookies=cookies)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_follow_status_unauthenticated(client):
    r = await client.get(f"/users/{uuid.uuid4()}/follow/status")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_review_nonexistent_album(auth_client):
    fake_id = str(uuid.uuid4())
    r = await auth_client.post("/reviews", json={"album_id": fake_id, "rating": 5})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_others_review(client):
    suffix_a = uuid.uuid4().hex[:6]
    suffix_b = uuid.uuid4().hex[:6]

    reg_a = await client.post("/auth/register", json={
        "email": f"own_a_{suffix_a}@cadence.app",
        "username": f"own_a_{suffix_a}",
        "password": "password123",
    })
    cookies_a = dict(reg_a.cookies)

    reg_b = await client.post("/auth/register", json={
        "email": f"own_b_{suffix_b}@cadence.app",
        "username": f"own_b_{suffix_b}",
        "password": "password123",
    })
    cookies_b = dict(reg_b.cookies)

    album_r = await client.post("/albums", json={
        "title": f"Edge Album {suffix_a}",
        "artist": "Edge Artist",
    }, cookies=cookies_a)
    album_id = album_r.json()["id"]

    review_r = await client.post("/reviews", json={
        "album_id": album_id,
        "rating": 7,
    }, cookies=cookies_a)
    review_id = review_r.json()["id"]

    r = await client.delete(f"/reviews/{review_id}", cookies=cookies_b)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
