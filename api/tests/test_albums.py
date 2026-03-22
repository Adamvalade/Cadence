import pytest


@pytest.mark.asyncio
async def test_create_album(auth_client):
    r = await auth_client.post("/albums", json={
        "title": "Kid A",
        "artist": "Radiohead",
        "release_year": 2000,
        "genre": "Electronic",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Kid A"
    assert data["artist"] == "Radiohead"
    assert data["release_year"] == 2000
    assert data["id"]


@pytest.mark.asyncio
async def test_create_album_unauthenticated(client):
    r = await client.post("/albums", json={
        "title": "Test Album",
        "artist": "Test Artist",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_album(auth_client, client):
    create = await auth_client.post("/albums", json={
        "title": "Amnesiac",
        "artist": "Radiohead",
        "release_year": 2001,
    })
    album_id = create.json()["id"]

    r = await client.get(f"/albums/{album_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Amnesiac"


@pytest.mark.asyncio
async def test_get_album_not_found(client):
    r = await client.get("/albums/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_album_rating_aggregation(auth_client, client):
    create = await auth_client.post("/albums", json={
        "title": "Hail to the Thief",
        "artist": "Radiohead",
        "release_year": 2003,
    })
    album_id = create.json()["id"]

    await auth_client.post("/reviews", json={
        "album_id": album_id,
        "rating": 8,
    })

    r = await client.get(f"/albums/{album_id}")
    data = r.json()
    assert data["avg_rating"] == 8.0
    assert data["review_count"] == 1
