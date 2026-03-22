import uuid

import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    r = await client.post("/auth/register", json={
        "email": f"list_{suffix}@cadence.app",
        "username": f"list_{suffix}",
        "password": "password123",
    })
    cookies = dict(r.cookies)
    user = r.json()["user"]

    album_r = await client.post("/albums", json={
        "title": f"List Album {suffix}",
        "artist": "List Artist",
    }, cookies=cookies)
    album_id = album_r.json()["id"]

    return cookies, user, album_id


@pytest.mark.asyncio
async def test_create_list(client):
    cookies, user, _ = await _setup(client)

    r = await client.post("/lists", json={
        "title": "My List",
        "description": "A test list",
        "is_public": True,
    }, cookies=cookies)
    assert r.status_code == 201
    assert r.json()["title"] == "My List"


@pytest.mark.asyncio
async def test_add_item_to_list(client):
    cookies, user, album_id = await _setup(client)

    create = await client.post("/lists", json={"title": "Item List"}, cookies=cookies)
    list_id = create.json()["id"]

    r = await client.post(f"/lists/{list_id}/items", json={
        "album_id": album_id,
        "position": 0,
    }, cookies=cookies)
    assert r.status_code == 201

    r = await client.get(f"/lists/{list_id}")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1
    assert r.json()["items"][0]["album_id"] == album_id


@pytest.mark.asyncio
async def test_delete_list(client):
    cookies, user, _ = await _setup(client)

    create = await client.post("/lists", json={"title": "Delete Me"}, cookies=cookies)
    list_id = create.json()["id"]

    r = await client.delete(f"/lists/{list_id}", cookies=cookies)
    assert r.status_code == 204

    r = await client.get(f"/lists/{list_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_user_lists(client):
    cookies, user, _ = await _setup(client)

    await client.post("/lists", json={"title": "Public List", "is_public": True}, cookies=cookies)
    await client.post("/lists", json={"title": "Private List", "is_public": False}, cookies=cookies)

    r = await client.get("/lists", params={"username": user["username"]})
    assert r.status_code == 200
    titles = [l["title"] for l in r.json()]
    assert "Public List" in titles
    assert "Private List" not in titles
