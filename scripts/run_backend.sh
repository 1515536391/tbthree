#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PIDS_DIR="$ROOT_DIR/.pids"
BACKEND_DIR="${BACKEND_DIR:-$ROOT_DIR/backend}"
BACKEND_LOG="$PIDS_DIR/backend.log"
BACKEND_PID_FILE="$PIDS_DIR/backend.pid"

mkdir -p "$PIDS_DIR"

if [ -f "$BACKEND_PID_FILE" ] && ps -p "$(cat "$BACKEND_PID_FILE")" >/dev/null 2>&1; then
  echo "✅ Backend already running (pid=$(cat "$BACKEND_PID_FILE"))"
  exit 0
fi

if [ ! -d "$BACKEND_DIR" ]; then
  echo "❌ Backend directory not found: $BACKEND_DIR" >&2
  exit 1
fi

cd "$BACKEND_DIR"

# venv bootstrap
if [ ! -d ".venv" ]; then
  echo "📦 Creating python venv (.venv)"
  python3 -m venv .venv
fi

source .venv/bin/activate

if [ -f "requirements.txt" ]; then
  echo "📦 Installing backend deps (may require internet)"
  pip install -U pip >/dev/null
  pip install -r requirements.txt
fi

echo "🚀 Starting backend (uvicorn) in background..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$BACKEND_LOG" 2>&1 &
echo $! >"$BACKEND_PID_FILE"

echo "✅ Backend started: http://127.0.0.1:8000/docs"
