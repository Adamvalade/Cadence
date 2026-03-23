#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/api"
WEB_DIR="$ROOT_DIR/web"
VENV_DIR="$API_DIR/.venv"

# ── Docker services ──────────────────────────────────────────────────
echo "Starting Docker services (Postgres + Redis)..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "Waiting for Postgres to be healthy..."
for i in $(seq 1 30); do
  if docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db pg_isready -U cadence >/dev/null 2>&1; then
    echo "  Postgres ready."
    break
  fi
  sleep 1
done

# ── Backend setup ────────────────────────────────────────────────────
echo ""
echo "Setting up backend..."
cd "$API_DIR"

if [ ! -d "$VENV_DIR" ]; then
  echo "  Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip -q
echo "  Installing Python dependencies..."
python -m pip install -r requirements.txt -q

if [ ! -f "$API_DIR/.env" ]; then
  echo "  Creating .env from .env.example..."
  cp "$API_DIR/.env.example" "$API_DIR/.env"
fi

echo "  Running database migrations..."
set +e
_migrate_out="$(alembic upgrade head 2>&1)"
_migrate_status=$?
set -e
if [ "$_migrate_status" -ne 0 ]; then
  # DB often already has tables (e.g. from tests) while alembic_version is empty
  if echo "$_migrate_out" | grep -q "already exists"; then
    echo "  Existing tables found without Alembic history; stamping head..."
    alembic stamp head
  else
    echo "$_migrate_out"
    exit "$_migrate_status"
  fi
fi

# ── Frontend setup ───────────────────────────────────────────────────
echo ""
echo "Setting up frontend..."
cd "$WEB_DIR"

if [ ! -f "$WEB_DIR/.env.local" ]; then
  if [ -f "$WEB_DIR/.env.example" ]; then
    echo "  Creating web/.env.local from .env.example..."
    cp "$WEB_DIR/.env.example" "$WEB_DIR/.env.local"
  else
    echo "  Creating web/.env.local with default API URL..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >"$WEB_DIR/.env.local"
  fi
fi

if [ ! -d "$WEB_DIR/node_modules" ]; then
  echo "  Installing npm dependencies..."
  npm install
else
  echo "  node_modules exists, skipping install."
fi

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo "Setup complete!"
echo ""
echo "To start the backend:"
echo "  cd api && source .venv/bin/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To start the frontend:"
echo "  cd web && npm run dev"
echo ""

if [[ "${1:-}" == "--run" ]]; then
  echo "Starting backend server..."
  cd "$API_DIR"
  source "$VENV_DIR/bin/activate"
  exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
fi
