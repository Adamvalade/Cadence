import pytest


async def _create_album(auth_client, title="Test Album"):
    r = await auth_client.post("/albums", json={
        "title": title,
        "artist": "Test Artist",
        "release_year": 2024,
    })
    return r.json()["id"]


@pytest.mark.asyncio
async def test_create_review(auth_client):
    album_id = await _create_album(auth_client, "Review Album 1")

    r = await auth_client.post("/reviews", json={
        "album_id": album_id,
        "rating": 7,
        "body": "Solid album.",
        "is_relisten": False,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["rating"] == 7
    assert data["body"] == "Solid album."
    assert data["username"] == auth_client.user["username"]
    assert data["album_id"] == album_id


@pytest.mark.asyncio
async def test_create_review_duplicate(auth_client):
    album_id = await _create_album(auth_client, "Review Album Dup")

    await auth_client.post("/reviews", json={"album_id": album_id, "rating": 5})
    r = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 8})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_review_invalid_rating(auth_client):
    album_id = await _create_album(auth_client, "Review Album Invalid")

    r = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 11})
    assert r.status_code == 422

    r = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 0})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_review(auth_client):
    album_id = await _create_album(auth_client, "Review Album Get")
    create = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 6})
    review_id = create.json()["id"]

    r = await auth_client.get(f"/reviews/{review_id}")
    assert r.status_code == 200
    assert r.json()["rating"] == 6


@pytest.mark.asyncio
async def test_update_review(auth_client):
    album_id = await _create_album(auth_client, "Review Album Update")
    create = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 5})
    review_id = create.json()["id"]

    r = await auth_client.patch(f"/reviews/{review_id}", json={"rating": 8, "body": "Updated."})
    assert r.status_code == 200
    assert r.json()["rating"] == 8
    assert r.json()["body"] == "Updated."


@pytest.mark.asyncio
async def test_delete_review(auth_client):
    album_id = await _create_album(auth_client, "Review Album Delete")
    create = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 4})
    review_id = create.json()["id"]

    r = await auth_client.delete(f"/reviews/{review_id}")
    assert r.status_code == 204

    r = await auth_client.get(f"/reviews/{review_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_like_unlike_review(auth_client):
    album_id = await _create_album(auth_client, "Review Album Like")
    create = await auth_client.post("/reviews", json={"album_id": album_id, "rating": 9})
    review_id = create.json()["id"]

    r = await auth_client.post(f"/reviews/{review_id}/like")
    assert r.status_code == 201

    r = await auth_client.get(f"/reviews/{review_id}")
    assert r.json()["like_count"] == 1
    assert r.json()["liked_by_me"] is True

    # duplicate like
    r = await auth_client.post(f"/reviews/{review_id}/like")
    assert r.status_code == 409

    # unlike
    r = await auth_client.delete(f"/reviews/{review_id}/like")
    assert r.status_code == 204

    r = await auth_client.get(f"/reviews/{review_id}")
    assert r.json()["like_count"] == 0
