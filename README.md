# Cadence

Cadence is a small full-stack app for logging albums you’ve listened to, writing short reviews, and seeing what people you follow are into. There’s search (with Spotify as a catalog source), a home feed from followed users, and pages for profiles, albums, and lists.

If you’re reviewing this repo: clone it, skim `web/src/app` and `api/app/routers`, or hit a deployed instance and use **Try demo** on the login screen when that’s enabled—you’ll land in a pre-seeded account with fake friends and reviews so the UI isn’t empty.

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
cp .env.example .env   # if you don’t have one yet
docker compose -f docker-compose.prod.yml up --build -d
```

Compose reads **`.env` in that root folder**—not `api/.env`. (`api/.env` is for local `uvicorn` only.)

You need things like `POSTGRES_PASSWORD`, `SECRET_KEY`, `FRONTEND_URL`, and `NEXT_PUBLIC_API_URL` (public URLs your browser actually uses). More detail: [deploy/README.md](deploy/README.md).

**If the app suddenly 404s every API call:** check `NEXT_PUBLIC_API_URL`. If your reverse proxy serves the API under a path (e.g. `https://yoursite.com/api`), set that **full** value so the browser calls `https://yoursite.com/api/auth/...`. Same-origin fallback uses Next’s **`/internal-api/*`** proxy (not under `/api/*`, so naive `location /api/` rules don’t send those requests to FastAPI by mistake).

### Demo mode (optional)

Add to your **root** `.env`:

```env
DEMO_LOGIN_ENABLED=true
DEMO_USER_PASSWORD=some-password-at-least-8-characters
```

(You can keep `DEMO_USER_EMAIL`, `DEMO_LOGIN_AUTO_CREATE`, and `DEMO_SEED_AT_STARTUP` as in `.env.example`; defaults are fine.)

**What `DEMO_USER_PASSWORD` is:** It’s the password for the **single shared demo user** on your server. You choose it and put it only in `.env`. Recruiters **do not** type it—the **Try demo** button calls the API, which logs them into that account using the value from the server config. So it’s not “their” password; it’s the demo account’s password, and you should assume anyone with access to your env or repo secrets could see it. Don’t reuse a real personal password. After changing it, if the demo user already existed with an old hash, you’d need to fix or delete that user in the DB once—first-time deploys usually don’t hit that.

---

## Ops notes

- API runs `alembic upgrade head` on container start.  
- Prod turns off OpenAPI docs; `/health` checks DB + Redis.  
- Dependabot: [.github/dependabot.yml](.github/dependabot.yml)

### Alembic “already exists”

DB has tables but Alembic’s version is wrong. See `./bin/setup.sh` stamping logic, or stamp the revision named in the error then `alembic upgrade head` again—don’t `stamp head` unless you’re sure every migration already ran.
