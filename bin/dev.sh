#!/usr/bin/env bash
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

SSL_CERT="$API_DIR/certs/localhost.pem"
SSL_KEY="$API_DIR/certs/localhost-key.pem"
UVICORN_SSL=()
if [[ -f "$SSL_CERT" && -f "$SSL_KEY" ]]; then
  UVICORN_SSL=(--ssl-keyfile "$SSL_KEY" --ssl-certfile "$SSL_CERT")
  API_URL_MSG="https://127.0.0.1:8000  (TLS: api/certs/)"
else
  API_URL_MSG="http://localhost:8000"
fi

if [[ -f "$WEB_DIR/.env.local" ]] && grep -qE '^[[:space:]]*NEXT_PUBLIC_API_URL=https://' "$WEB_DIR/.env.local" 2>/dev/null; then
  if [[ ! -f "$SSL_CERT" || ! -f "$SSL_KEY" ]]; then
    echo ""
    echo "ERROR: web/.env.local sets NEXT_PUBLIC_API_URL=https://… but api/certs/localhost.pem is missing."
    echo "Run once:  ./bin/ssl-localhost.sh   (needs: brew install mkcert)"
    echo "Or switch web/.env.local to:  NEXT_PUBLIC_API_URL=http://localhost:8000"
    exit 1
  fi
fi
echo ""
echo "API  → $API_URL_MSG  (docs: /docs)"
echo "App  → http://localhost:3000"
echo "Press Ctrl+C to stop API + web."
echo ""

(
  cd "$API_DIR"
  # shellcheck source=/dev/null
  source .venv/bin/activate
  exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 "${UVICORN_SSL[@]}"
) &
API_PID=$!

if [[ ${#UVICORN_SSL[@]} -gt 0 ]]; then
  _https_ok=false
  for _ in $(seq 1 40); do
    if curl -skf "https://127.0.0.1:8000/health" >/dev/null 2>&1; then
      _https_ok=true
      break
    fi
    sleep 0.25
  done
  if [[ "$_https_ok" != true ]]; then
    echo ""
    echo "ERROR: https://127.0.0.1:8000 did not respond (TLS). The app is configured for HTTPS but the API is not up with TLS."
    if curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
      echo ""
      echo "Port 8000 is answering with plain HTTP only — usually an old uvicorn started without certificates."
      echo "Fix: stop it, then run this script again:"
      echo "  lsof -nP -iTCP:8000 -sTCP:LISTEN"
      echo "  kill <PID>     # then:  ./bin/dev.sh"
    fi
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
    exit 1
  fi
fi

cd "$WEB_DIR"
npm run dev
