#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PIDS_DIR="$ROOT_DIR/.pids"
CHAIN_DIR="${CHAIN_DIR:-$ROOT_DIR/chain/tbthree}"
CHAIN_LOG="$PIDS_DIR/chain.log"
CHAIN_PID_FILE="$PIDS_DIR/chain.pid"

mkdir -p "$PIDS_DIR"

if [ -f "$CHAIN_PID_FILE" ] && ps -p "$(cat "$CHAIN_PID_FILE")" >/dev/null 2>&1; then
  echo "✅ Chain already running (pid=$(cat "$CHAIN_PID_FILE"))"
  exit 0
fi

if ! command -v ignite >/dev/null 2>&1; then
  echo "❌ ignite not found. Please install Ignite CLI first." >&2
  exit 1
fi

if [ ! -d "$CHAIN_DIR" ]; then
  echo "❌ Chain directory not found: $CHAIN_DIR" >&2
  echo "Run: make bootstrap" >&2
  exit 1
fi

echo "🚀 Starting chain (ignite chain serve) in background..."
(
  cd "$CHAIN_DIR"
  nohup ignite chain serve >"$CHAIN_LOG" 2>&1 &
  echo $! >"$CHAIN_PID_FILE"
)

# wait for RPC
RPC_URL="http://127.0.0.1:26657/status"
for i in {1..60}; do
  if curl -s "$RPC_URL" | grep -q '"node_info"'; then
    echo "✅ Chain RPC is up: $RPC_URL"
    exit 0
  fi
  sleep 1
done

echo "⚠️ Chain started but RPC not ready yet. Check logs: $CHAIN_LOG"
