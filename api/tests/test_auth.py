import pytest


@pytest.mark.asyncio
async def test_register(client):
    r = await client.post("/auth/register", json={
        "email": "reg@cadence.app",
        "username": "reguser",
        "password": "password123",
        "display_name": "Reg User",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["message"] == "Registration successful"
    assert data["user"]["username"] == "reguser"
    assert "access_token" in r.cookies


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/auth/register", json={
        "email": "dup@cadence.app",
        "username": "dupuser",
        "password": "password123",
    })
    r = await client.post("/auth/register", json={
        "email": "dup@cadence.app",
        "username": "dupuser2",
        "password": "password123",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_validation(client):
    r = await client.post("/auth/register", json={
        "email": "bad",
        "username": "ab",
        "password": "short",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/register", json={
        "email": "login@cadence.app",
        "username": "loginuser",
        "password": "password123",
    })
    r = await client.post("/auth/login", json={
        "email": "login@cadence.app",
        "password": "password123",
    })
    assert r.status_code == 200
    assert r.json()["user"]["username"] == "loginuser"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrongpw@cadence.app",
        "username": "wrongpwuser",
        "password": "password123",
    })
    r = await client.post("/auth/login", json={
        "email": "wrongpw@cadence.app",
        "password": "wrongpassword",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me(auth_client):
    r = await auth_client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == auth_client.user["username"]


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    r = await client.get("/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(client):
    r = await client.post("/auth/forgot-password", json={"email": "nobody@cadence.app"})
    assert r.status_code == 200
    assert "message" in r.json()


@pytest.mark.asyncio
async def test_forgot_and_reset_password(client, monkeypatch):
    from app.routers import auth as auth_mod

    monkeypatch.setattr(auth_mod.secrets, "token_urlsafe", lambda _n: "fixed-test-reset-token-abcdef")

    await client.post(
        "/auth/register",
        json={
            "email": "resetme@cadence.app",
            "username": "resetmeuser",
            "password": "oldpassword123",
        },
    )
    r = await client.post("/auth/forgot-password", json={"email": "resetme@cadence.app"})
    assert r.status_code == 200

    r2 = await client.post(
        "/auth/reset-password",
        json={"token": "fixed-test-reset-token-abcdef", "new_password": "newpassword999"},
    )
    assert r2.status_code == 200

    bad = await client.post("/auth/login", json={"email": "resetme@cadence.app", "password": "oldpassword123"})
    assert bad.status_code == 401

    ok = await client.post("/auth/login", json={"email": "resetme@cadence.app", "password": "newpassword999"})
    assert ok.status_code == 200


@pytest.mark.asyncio
async def test_logout(client):
    reg = await client.post("/auth/register", json={
        "email": "logout@cadence.app",
        "username": "logoutuser",
        "password": "password123",
    })
    cookies = dict(reg.cookies)

    r = await client.post("/auth/logout", cookies=cookies)
    assert r.status_code == 200
    assert r.json()["message"] == "Logged out"
