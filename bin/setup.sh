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
alembic upgrade head

# ── Frontend setup ───────────────────────────────────────────────────
echo ""
echo "Setting up frontend..."
cd "$WEB_DIR"

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
echo "  cd api && source .venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "To start the frontend:"
echo "  cd web && npm run dev"
echo ""

if [[ "${1:-}" == "--run" ]]; then
  echo "Starting backend server..."
  cd "$API_DIR"
  source "$VENV_DIR/bin/activate"
  exec python -m uvicorn main:app --reload
fi
