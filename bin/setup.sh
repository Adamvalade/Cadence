#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Cadence backend..."

# Resolve repo root no matter where script is run from
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/api"
VENV_DIR="$API_DIR/.venv"

cd "$API_DIR"

# 1) Create virtual environment if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
else
  echo "Virtual environment already exists."
fi

# 2) Activate virtual environment (for THIS script only)
echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 3) Upgrade pip inside venv
python -m pip install --upgrade pip

# 4) Install dependencies inside venv
if [ -f "requirements.txt" ]; then
  echo "Installing dependencies..."
  python -m pip install -r requirements.txt
else
  echo "ERROR: requirements.txt not found in api/"
  exit 1
fi

echo ""
echo "Using Python:"
python -c "import sys; print(sys.executable)"

echo ""
echo "Verifying FastAPI..."
python - <<'EOF'
import fastapi
print("FastAPI version:", fastapi.__version__)
EOF

# 5) Optionally start server
if [[ "${1:-}" == "--run" ]]; then
  echo ""
  echo "Starting FastAPI server..."
  exec python -m uvicorn main:app --reload
else
  echo ""
  echo "Setup complete."
  echo "To run the server:"
  echo "  cd api"
  echo "  source .venv/bin/activate"
  echo "  uvicorn main:app --reload"
  echo ""
  echo "Or simply:"
  echo "  ./bin/setup.sh --run"
fi
