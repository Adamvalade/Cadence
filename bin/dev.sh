#!/usr/bin/env bash
# Start Postgres/Redis + API + Next.js so the app is available on localhost.
# Run ./bin/setup.sh once first if you have no venv or node_modules.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/api"
WEB_DIR="$ROOT_DIR/web"
VENV_DIR="$API_DIR/.venv"
COMPOSE=(docker compose -f "$ROOT_DIR/docker-compose.yml")

if [ ! -d "$VENV_DIR" ]; then
  echo "No api/.venv found. Run:  ./bin/setup.sh"
  exit 1
fi
if [ ! -d "$WEB_DIR/node_modules" ]; then
  echo "No web/node_modules found. Run:  ./bin/setup.sh"
  exit 1
fi

echo "Docker: Postgres + Redis..."
"${COMPOSE[@]}" up -d

echo "Waiting for Postgres..."
for _ in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T db pg_isready -U cadence >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

cleanup() {
  if [ -n "${API_PID:-}" ]; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo ""
echo "API  → http://localhost:8000  (docs: /docs)"
echo "App  → http://localhost:3000"
echo "Press Ctrl+C to stop API + web."
echo ""

(
  cd "$API_DIR"
  # shellcheck source=/dev/null
  source .venv/bin/activate
  exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
) &
API_PID=$!

cd "$WEB_DIR"
npm run dev
