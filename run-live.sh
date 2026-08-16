#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-5057}"
export DATABASE_PATH="${DATABASE_PATH:-$ROOT_DIR/data/mlat_live.db}"
export STRICT_PRODUCTION_MODE=true
export SIMULATE_IF_UNAVAILABLE=false
export REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
export DEMO_MODE=false
export ENABLE_ADMIN_API=false
export BENCHMARK_REPORT_PATH="${BENCHMARK_REPORT_PATH:-$ROOT_DIR/evidence/mlat-reference/live/latest.json}"
export PERFORMANCE_REPORT_PATH="${PERFORMANCE_REPORT_PATH:-$ROOT_DIR/evidence/mlat-reference/experimental/performance-local-simulation.json}"
export RELIABILITY_REPORT_PATH="${RELIABILITY_REPORT_PATH:-$ROOT_DIR/evidence/mlat-reference/experimental/reliability-local-simulation.json}"
export LIVE_PREFLIGHT_REPORT="${LIVE_PREFLIGHT_REPORT:-$ROOT_DIR/logs/live-preflight.json}"

echo "Checking strict live-evidence launch gates..."
python3 "$ROOT_DIR/tools/mlat/check_live_ingest_readiness.py" \
  --require-ready \
  --output "$LIVE_PREFLIGHT_REPORT"

echo "Starting the strict MLAT reference API at http://localhost:${API_PORT}/api"
exec "$ROOT_DIR/render-entrypoint.sh"
