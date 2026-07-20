#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATABASE_PATH="${DATABASE_PATH:-$ROOT_DIR/data/mlat_data.db}"
PROCESSOR_PID=""
API_PID=""

mkdir -p "$(dirname "$DATABASE_PATH")"

export DATABASE_PATH
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-5000}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"

cleanup() {
    trap - EXIT INT TERM
    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        echo "Stopping MLAT API ($API_PID)..."
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true
    fi
    if [ -n "$PROCESSOR_PID" ] && kill -0 "$PROCESSOR_PID" 2>/dev/null; then
        echo "Stopping MLAT processor ($PROCESSOR_PID)..."
        kill "$PROCESSOR_PID" 2>/dev/null || true
        wait "$PROCESSOR_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo "Starting MLAT processor with DATABASE_PATH=$DATABASE_PATH"
python3 "$ROOT_DIR/src/production_main.py" &
PROCESSOR_PID=$!

echo "Starting MLAT API on ${API_HOST}:${API_PORT}"
python3 "$ROOT_DIR/src/api/rest_api.py" &
API_PID=$!

# Keep the service healthy as a unit. If either half exits, the trap stops the
# other half and the supervisor returns the failed process status.
while kill -0 "$PROCESSOR_PID" 2>/dev/null && kill -0 "$API_PID" 2>/dev/null; do
    sleep 1
done

if ! kill -0 "$PROCESSOR_PID" 2>/dev/null; then
    echo "MLAT processor exited; stopping the API."
    wait "$PROCESSOR_PID"
    exit $?
fi

echo "MLAT API exited; stopping the processor."
wait "$API_PID"
