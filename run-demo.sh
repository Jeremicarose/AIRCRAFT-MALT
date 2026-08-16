#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-5057}"
export DATABASE_PATH="${DATABASE_PATH:-$ROOT_DIR/data/mlat_demo.db}"
export STRICT_PRODUCTION_MODE=false
export FOURDSKY_TRANSPORT=simulation
export SIMULATE_IF_UNAVAILABLE=true
export RECEIVER_REGISTRY_TYPE_HASH=""
export REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=false
export ENABLE_ADMIN_API=false
export ENABLE_BACKGROUND_BROADCASTER=false
export DEMO_MODE=true
export DEMO_SCENARIO="${DEMO_SCENARIO:-northeast-corridor}"
export DEMO_READ_ONLY=true
export DEMO_LABEL="${DEMO_LABEL:-Hosted demo - Northeast replay}"
export DEMO_AUTO_CONNECT=true
export STATS_INTERVAL_SECONDS="${STATS_INTERVAL_SECONDS:-15}"

echo "Starting the MLAT reference API at http://localhost:${API_PORT}/api"
exec "$ROOT_DIR/render-entrypoint.sh"
