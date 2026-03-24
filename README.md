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

### Alembic: `relation "albums" already exists`

That means the database **already has tables** (e.g. from tests or manual `create_all`) but **`alembic_version` is empty**, so `upgrade` tries to run the initial migration again.

- If the schema already matches the latest migration (you have `listen_statuses`, etc.):  
  `cd api && source .venv/bin/activate && alembic stamp head`
- If you only have the older tables and are missing a later migration:  
  `alembic stamp 225104d8ff02` then `alembic upgrade head`

After stamping, `alembic current` should show `ab35e8d933c3 (head)` (or whatever `head` is in your repo).