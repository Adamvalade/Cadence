# Cadence

Cadence is a small full-stack app for logging albums you’ve listened to, writing short reviews, and seeing what people you follow are into. There’s search (with Spotify as a catalog source), a home feed from followed users, and pages for profiles, albums, and lists.

**Try demo** on the login page (when enabled) opens a pre-seeded account. Main code: `web/src/app`, `api/app/routers`.

---

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy + Alembic, Postgres, Redis  
- **Frontend:** Next.js (App Router), TypeScript  
- **Deploy:** Docker Compose; optional Caddy + Let’s Encrypt under `deploy/`

Rough layout:

```
api/app/     routers, models, services (feed, Spotify client, etc.)
web/src/     app routes, components, API client
```

---

## Run it locally

1. `./bin/setup.sh` — Python venv, migrations, `web/.env.local`, `npm install`  
2. Copy `api/.env.example` → `api/.env` and fix `DATABASE_URL` / `SECRET_KEY` / `FRONTEND_URL` (Postgres from `docker-compose.yml` is on port **5433** by default).  
3. `./bin/dev.sh` — Postgres + Redis in Docker, API at **http://localhost:8000**, Next at **http://localhost:3000**

---

## Production (Compose)

From the **repo root** (where `docker-compose.prod.yml` lives):

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml up --build -d
```

Compose reads **`.env` in that root folder**—not `api/.env`. (`api/.env` is for local `uvicorn` only.)

You need things like `POSTGRES_PASSWORD`, `SECRET_KEY`, `FRONTEND_URL`, and `NEXT_PUBLIC_API_URL` (public URLs your browser actually uses). More detail: [deploy/README.md](deploy/README.md).

**API 404s from the browser:** `NEXT_PUBLIC_API_URL` must match how traffic reaches the API (path vs subdomain). Same-origin setups use Next’s `/internal-api/*` BFF so `/api/*` nginx rules don’t hit FastAPI by mistake. **404 on `/api/auth/...` with healthy `/health`:** often full path still has `/api` at the app; the API infers a `/api` mount from `NEXT_PUBLIC_API_URL` when it ends with `/api`, or set `API_FORCE_NO_PREFIX=true` if the proxy strips `/api`.

### Demo mode (optional)

Add to your **root** `.env`:

```env
DEMO_LOGIN_ENABLED=true
DEMO_USER_PASSWORD=some-password-at-least-8-characters
```

`DEMO_USER_PASSWORD` is the shared demo account password (server-side only; **Try demo** logs in without visitors typing it). Use a dedicated value, not a personal password.

---

## Ops notes

- API runs `alembic upgrade head` on container start.  
- Prod turns off OpenAPI docs; `/health` checks DB + Redis.  
- Dependabot: [.github/dependabot.yml](.github/dependabot.yml)

### Alembic “already exists”

DB exists but Alembic version is wrong: align version with `./bin/setup.sh` / stamp + `alembic upgrade head` per the error output.
