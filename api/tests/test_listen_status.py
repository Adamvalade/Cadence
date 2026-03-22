import uuid

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    r = await client.post("/auth/register", json={
        "email": f"ls_{suffix}@cadence.app",
        "username": f"ls_{suffix}",
        "password": "password123",
    })
    cookies = dict(r.cookies)

    album_r = await client.post("/albums", json={
        "title": f"LS Album {suffix}",
        "artist": "LS Artist",
    }, cookies=cookies)
    album_id = album_r.json()["id"]

    return cookies, album_id


@pytest.mark.asyncio
async def test_set_listen_status(client):
    cookies, album_id = await _setup(client)

    r = await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "want_to_listen",
    }, cookies=cookies)
    assert r.status_code == 200
    assert r.json()["status"] == "want_to_listen"
    assert r.json()["album_id"] == album_id


@pytest.mark.asyncio
async def test_update_listen_status(client):
    cookies, album_id = await _setup(client)

    await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "want_to_listen",
    }, cookies=cookies)

    r = await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "listened",
    }, cookies=cookies)
    assert r.status_code == 200
    assert r.json()["status"] == "listened"


@pytest.mark.asyncio
async def test_invalid_status(client):
    cookies, album_id = await _setup(client)

    r = await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "invalid_status",
    }, cookies=cookies)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_album_listen_status(client):
    cookies, album_id = await _setup(client)

    r = await client.get(f"/listen-status/{album_id}", cookies=cookies)
    assert r.status_code == 200
    assert r.json()["status"] is None

    await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "listening",
    }, cookies=cookies)

    r = await client.get(f"/listen-status/{album_id}", cookies=cookies)
    assert r.status_code == 200
    assert r.json()["status"] == "listening"


@pytest.mark.asyncio
async def test_get_all_listen_statuses(client):
    cookies, album_id = await _setup(client)

    await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "want_to_listen",
    }, cookies=cookies)

    r = await client.get("/listen-status", cookies=cookies)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert any(s["album_id"] == album_id for s in r.json())


@pytest.mark.asyncio
async def test_filter_listen_statuses(client):
    cookies, album_id = await _setup(client)

    await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "want_to_listen",
    }, cookies=cookies)

    r = await client.get("/listen-status", params={"status": "want_to_listen"}, cookies=cookies)
    assert r.status_code == 200
    assert all(s["status"] == "want_to_listen" for s in r.json())

    r = await client.get("/listen-status", params={"status": "listened"}, cookies=cookies)
    assert r.status_code == 200
    assert not any(s["album_id"] == album_id for s in r.json())


@pytest.mark.asyncio
async def test_delete_listen_status(client):
    cookies, album_id = await _setup(client)

    await client.put("/listen-status", json={
        "album_id": album_id,
        "status": "listening",
    }, cookies=cookies)

    r = await client.delete(f"/listen-status/{album_id}", cookies=cookies)
    assert r.status_code == 204

    r = await client.get(f"/listen-status/{album_id}", cookies=cookies)
    assert r.json()["status"] is None


@pytest.mark.asyncio
async def test_delete_nonexistent_status(client):
    cookies, album_id = await _setup(client)

    r = await client.delete(f"/listen-status/{album_id}", cookies=cookies)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_listen_status_unauthenticated(client):
    r = await client.put("/listen-status", json={
        "album_id": "00000000-0000-0000-0000-000000000000",
        "status": "listening",
    })
    assert r.status_code == 401
