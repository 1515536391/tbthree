#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PIDS_DIR="$ROOT_DIR/.pids"

stop_pid_file() {
  local name="$1"
  local file="$PIDS_DIR/$name.pid"
  if [ -f "$file" ]; then
    local pid
    pid="$(cat "$file")"
    if ps -p "$pid" >/dev/null 2>&1; then
      echo "🛑 Stopping $name (pid=$pid)"
      kill "$pid" || true
    fi
    rm -f "$file"
  fi
}

stop_pid_file frontend
stop_pid_file backend
stop_pid_file chain

echo "✅ All stopped."
