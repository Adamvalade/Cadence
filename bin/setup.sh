#!/usr/bin/env bash
# One-time install: Docker deps, Python venv, migrations, npm install.
# Does NOT start servers by default — use ./bin/dev.sh or ./bin/setup.sh --dev
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DEV=false
for _arg in "$@"; do
  case "$_arg" in
    --dev|--run)
      RUN_DEV=true
      ;;
  esac
done
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
_migrate_status=1
_max_attempts=8
for _attempt in $(seq 1 "$_max_attempts"); do
  set +e
  _migrate_out="$(alembic upgrade head 2>&1)"
  _migrate_status=$?
  set -e
  if [ "$_migrate_status" -eq 0 ]; then
    printf '%s\n' "$_migrate_out"
    break
  fi
  printf '%s\n' "$_migrate_out"
  if echo "$_migrate_out" | grep -qiE 'already exists|DuplicateTable'; then
    _target="$(printf '%s\n' "$_migrate_out" | grep 'Running upgrade' | tail -1 | sed -n 's/.*Running upgrade[[:space:]]*->[[:space:]]*\([a-f0-9]*\).*/\1/p')"
    if [ -z "$_target" ]; then
      echo "  Duplicate tables but could not parse Alembic target revision. See README (Alembic)."
      exit 1
    fi
    echo "  Schema already includes revision $_target; stamping it and retrying upgrade..."
    alembic stamp "$_target"
  else
    exit "$_migrate_status"
  fi
done
if [ "$_migrate_status" -ne 0 ]; then
  echo "  Migrations failed after $_max_attempts attempts."
  exit 1
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

if [[ "$RUN_DEV" == true ]]; then
  echo "Starting app on localhost (API + web)..."
  exec "$ROOT_DIR/bin/dev.sh"
fi

echo "Nothing is listening yet. To open the app locally, run:"
echo ""
echo "  ./bin/dev.sh"
echo ""
echo "That starts Postgres/Redis (Docker), the API on :8000, and Next.js on :3000."
echo "Or use two terminals:"
echo "  cd api && source .venv/bin/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "  cd web && npm run dev"
echo ""
