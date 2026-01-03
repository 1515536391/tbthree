#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PIDS_DIR="$ROOT_DIR/.pids"
FRONTEND_DIR="${FRONTEND_DIR:-$ROOT_DIR/frontend}"
FRONTEND_LOG="$PIDS_DIR/frontend.log"
FRONTEND_PID_FILE="$PIDS_DIR/frontend.pid"

mkdir -p "$PIDS_DIR"

if [ -f "$FRONTEND_PID_FILE" ] && ps -p "$(cat "$FRONTEND_PID_FILE")" >/dev/null 2>&1; then
  echo "✅ Frontend already running (pid=$(cat "$FRONTEND_PID_FILE"))"
  exit 0
fi

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ Frontend directory not found: $FRONTEND_DIR" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "❌ npm not found. Please install Node.js first." >&2
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "📦 Installing frontend deps (npm install) (may require internet)"
  npm install
fi

echo "🚀 Starting frontend (Vue dev server) in background..."
nohup npm run serve >"$FRONTEND_LOG" 2>&1 &
echo $! >"$FRONTEND_PID_FILE"

echo "✅ Frontend started: http://127.0.0.1:8080"
