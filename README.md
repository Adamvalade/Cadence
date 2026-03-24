Cadence is a social app for logging albums, rating/reviewing music, and discovering new releases through people you follow.


Cadence/
  api/
    app/
      main.py
      core/        # settings, security, logging
      db/          # engine/session, base
      models/      # SQLAlchemy models
      schemas/     # Pydantic DTOs
      routers/     # FastAPI routers
      services/    # spotify client, feed builder, etc.
      tasks/       # background jobs (optional)
    tests/
    alembic/
    requirements.txt (or pyproject.toml)
  web/
    src/
      pages/ or app/   # if Next
      components/
      lib/             # api client, auth helpers
      styles/
  bin/
    setup.sh
  docker-compose.yml
  README.md
  SPEC.md

## Running locally

**First time:** `./bin/setup.sh` — installs Python deps, runs migrations, creates `web/.env.local`, `npm install`.

**Every time you want the site in the browser:** `./bin/dev.sh` — starts Docker (Postgres + Redis), API on **http://localhost:8000**, Next.js on **http://localhost:3000**.

Or one shot: `./bin/setup.sh --dev` (setup + then same as `dev.sh`).

Copy `api/.env.example` → `api/.env` and set `DATABASE_URL`, `SECRET_KEY`, optional Spotify keys, and `FRONTEND_URL=http://localhost:3000`. Postgres in Docker is on host port **5433** by default (`DATABASE_URL` in `.env.example` matches).

### Alembic: `relation "albums" already exists` (or other “already exists”)

The database **already has tables** but **`alembic_version` is empty or behind**, so `alembic upgrade head` tries to create objects that are already there. That also breaks the API if the code expects columns your DB does not have yet (e.g. search touching `albums`).

**Prefer:** run `./bin/setup.sh` again — it stamps the revision Alembic was trying to apply, then retries `upgrade head` in a loop.

**Manual recovery:** stamp the **target** revision from the error line `Running upgrade … -> REV`, then upgrade again. Example if the first failure is on the initial migration:

`cd api && source .venv/bin/activate && alembic stamp 225104d8ff02 && alembic upgrade head`

If the next error is `listen_statuses` already exists:

`alembic stamp ab35e8d933c3 && alembic upgrade head`

Repeat until `alembic upgrade head` succeeds. Avoid `alembic stamp head` unless you are sure every migration’s DDL is already applied — otherwise you can skip real migrations.

`alembic current` should end on the same revision as `alembic heads`.