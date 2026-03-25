import secrets
from urllib.parse import quote, urlparse

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.rate_limit import auth_limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserBrief

router = APIRouter()

oauth = OAuth()


def _client_facing_base_url(request: Request) -> str:
    """Public URL of the API as the browser sees it (TLS termination / reverse proxy safe)."""
    proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    if proto not in ("http", "https"):
        proto = request.url.scheme
    host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()
    if not host:
        host = request.headers.get("host", "").split(",")[0].strip()
    if host:
        return f"{proto}://{host}".rstrip("/")
    return str(request.base_url).rstrip("/")


def _spotify_redirect_uri(request: Request) -> str:
    """Must exactly match a URI registered on the Spotify app."""
    explicit = (settings.SPOTIFY_REDIRECT_URI or "").strip()
    if explicit:
        return explicit
    base = _client_facing_base_url(request)
    return f"{base}/auth/spotify/callback"


def _spotify_oauth_origin(redirect_uri: str) -> str:
    p = urlparse(redirect_uri)
    return f"{p.scheme}://{p.netloc}"

if settings.SPOTIFY_CLIENT_ID:
    oauth.register(
        name="spotify",
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        authorize_url="https://accounts.spotify.com/authorize",
        access_token_url="https://accounts.spotify.com/api/token",
        api_base_url="https://api.spotify.com/v1/",
        client_kwargs={"scope": "user-read-email user-read-private"},
    )

if settings.GOOGLE_CLIENT_ID:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def _attach_access_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite=settings.access_token_cookie_samesite,  # type: ignore[arg-type]
        secure=settings.access_token_cookie_secure,
        max_age=60 * 60 * 24 * 7,
    )


def _issue_session(response: Response, user_id: str) -> str:
    token = create_access_token(user_id)
    _attach_access_token_cookie(response, token)
    return token


def _user_brief(user: User) -> UserBrief:
    return UserBrief(
        id=str(user.id),
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


# ── Email/Password ──────────────────────────────────────────────────


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    auth_limiter.check(request)
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already taken")

    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
        display_name=body.display_name or body.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = _issue_session(response, str(user.id))
    return AuthResponse(message="Registration successful", user=_user_brief(user), access_token=token)


@router.post("/login", response_model=AuthResponse)
async def login(request: Request, body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    auth_limiter.check(request)
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = _issue_session(response, str(user.id))
    return AuthResponse(message="Login successful", user=_user_brief(user), access_token=token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        "access_token",
        path="/",
        httponly=True,
        samesite=settings.access_token_cookie_samesite,  # type: ignore[arg-type]
        secure=settings.access_token_cookie_secure,
    )
    return {"message": "Logged out"}


@router.get("/me", response_model=UserBrief)
async def me(current_user: User = Depends(get_current_user)):
    return _user_brief(current_user)


# ── Spotify OAuth ────────────────────────────────────────────────────


@router.get("/spotify")
async def spotify_login(request: Request):
    if not settings.SPOTIFY_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Spotify OAuth not configured")
    redirect_uri = _spotify_redirect_uri(request)
    explicit = (settings.SPOTIFY_REDIRECT_URI or "").strip()
    if explicit:
        want_origin = _spotify_oauth_origin(redirect_uri).rstrip("/")
        got_origin = _client_facing_base_url(request)
        if want_origin != got_origin:
            return RedirectResponse(url=f"{want_origin}/auth/spotify", status_code=307)
    return await oauth.spotify.authorize_redirect(request, redirect_uri)


@router.get("/spotify/callback")
async def spotify_callback(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.SPOTIFY_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Spotify OAuth not configured")

    token_data = await oauth.spotify.authorize_access_token(request)
    resp = await oauth.spotify.get("me", token=token_data)
    profile = resp.json()

    spotify_id = profile["id"]
    email = profile.get("email")
    display_name = profile.get("display_name", "")
    avatar_url = None
    images = profile.get("images", [])
    if images:
        avatar_url = images[0].get("url")

    result = await db.execute(select(User).where(User.spotify_id == spotify_id))
    user = result.scalar_one_or_none()

    if not user and email:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.spotify_id = spotify_id

    if not user:
        username = _generate_username(display_name or spotify_id)
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            username = f"{username}_{secrets.token_hex(3)}"

        user = User(
            email=email or f"{spotify_id}@spotify.oauth",
            username=username,
            display_name=display_name or username,
            spotify_id=spotify_id,
            avatar_url=avatar_url,
        )
        db.add(user)

    if avatar_url and not user.avatar_url:
        user.avatar_url = avatar_url

    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id))
    url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback#access_token={quote(token, safe='')}"
    redirect = RedirectResponse(url=url, status_code=307)
    _attach_access_token_cookie(redirect, token)
    return redirect


# ── Google OAuth ─────────────────────────────────────────────────────


@router.get("/google")
async def google_login(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    base = _client_facing_base_url(request)
    redirect_uri = f"{base}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    token_data = await oauth.google.authorize_access_token(request)
    id_info = token_data.get("userinfo", {})

    email = id_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    name = id_info.get("name", "")
    avatar_url = id_info.get("picture")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        username = _generate_username(name or email.split("@")[0])
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            username = f"{username}_{secrets.token_hex(3)}"

        user = User(
            email=email,
            username=username,
            display_name=name or username,
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(str(user.id))
    url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback#access_token={quote(token, safe='')}"
    redirect = RedirectResponse(url=url, status_code=307)
    _attach_access_token_cookie(redirect, token)
    return redirect


def _generate_username(source: str) -> str:
    clean = "".join(c if c.isalnum() or c == "_" else "" for c in source.lower().replace(" ", "_"))
    return (clean or "user")[:25]
