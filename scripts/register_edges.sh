#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/backend/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ backend/.env not found. Run: make init" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [ ! -x "$TB3D" ]; then
  echo "❌ TB3D binary not found: $TB3D" >&2
  exit 1
fi

echo "🧩 Registering edges on chain (admin: $ADMIN_NAME)"

register_edge() {
  local edge_addr="$1"
  local region="$2"
  echo "- register-edge $edge_addr region=$region"
  "$TB3D" tx tbthree register-edge "$edge_addr" "$region" \
    --from "$ADMIN_NAME" --keyring-backend "$KEYRING_BACKEND" --home "$CHAIN_HOME" \
    --chain-id "$CHAIN_ID" --node "$CHAIN_RPC" -y --broadcast-mode block >/dev/null
}

register_edge "$EDGE1_ADDR" "A" || true
register_edge "$EDGE2_ADDR" "A" || true
register_edge "$EDGE3_ADDR" "B" || true

echo "✅ Edge registration tx sent. (If already registered, it's ok.)"
