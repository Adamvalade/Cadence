#!/usr/bin/env bash
# Trusted TLS for the API on :8000 (e.g. when the web app uses NEXT_PUBLIC_API_URL=https://…).
# Requires mkcert: https://github.com/FiloSottile/mkcert
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="$ROOT_DIR/api/certs"
CERT_FILE="$CERT_DIR/localhost.pem"
KEY_FILE="$CERT_DIR/localhost-key.pem"

mkdir -p "$CERT_DIR"

if ! command -v mkcert >/dev/null 2>&1; then
  echo "mkcert is not installed."
  echo ""
  echo "  macOS:  brew install mkcert && mkcert -install"
  echo "  Other:  https://github.com/FiloSottile/mkcert#installation"
  exit 1
fi

mkcert -install >/dev/null 2>&1 || true
mkcert -cert-file "$CERT_FILE" -key-file "$KEY_FILE" localhost 127.0.0.1 ::1

echo "Wrote:"
echo "  $CERT_FILE"
echo "  $KEY_FILE"
echo ""
echo "Set in web/.env.local:"
echo "  NEXT_PUBLIC_API_URL=https://127.0.0.1:8000"
echo "Then restart ./bin/dev.sh — TLS is used when these cert files exist."
