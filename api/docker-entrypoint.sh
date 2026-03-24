#!/bin/sh
set -e

# Docker / Swarm secrets mounted as files (see deploy/docker-compose.secrets.yml).
if [ -n "${SECRET_KEY_FILE:-}" ] && [ -r "$SECRET_KEY_FILE" ]; then
  export SECRET_KEY="$(tr -d '\n\r' < "$SECRET_KEY_FILE")"
fi

if [ -n "${DATABASE_URL_FILE:-}" ] && [ -r "$DATABASE_URL_FILE" ]; then
  export DATABASE_URL="$(tr -d '\n\r' < "$DATABASE_URL_FILE")"
elif [ -n "${POSTGRES_PASSWORD_FILE:-}" ] && [ -r "$POSTGRES_PASSWORD_FILE" ]; then
  export DATABASE_URL="$(
    python -c 'import os, urllib.parse; p = os.environ["POSTGRES_PASSWORD_FILE"]; pw = open(p).read().strip(); u = urllib.parse.quote("cadence", safe=""); q = urllib.parse.quote(pw, safe=""); print(f"postgresql+asyncpg://{u}:{q}@db:5432/cadence")'
  )"
fi

alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000
