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
export BENCHMARK_REPORT_PATH="${BENCHMARK_REPORT_PATH:-$ROOT_DIR/benchmark/latest.json}"
export PERFORMANCE_REPORT_PATH="${PERFORMANCE_REPORT_PATH:-$ROOT_DIR/benchmark/performance-latest.json}"
export RELIABILITY_REPORT_PATH="${RELIABILITY_REPORT_PATH:-$ROOT_DIR/benchmark/reliability-latest.json}"

echo "Checking strict live-evidence launch gates..."
python3 "$ROOT_DIR/scripts/check_live_ingest_readiness.py" --require-ready

echo "Starting strict live runtime at http://localhost:${API_PORT}/app/pipeline.html"
exec "$ROOT_DIR/render-entrypoint.sh"
