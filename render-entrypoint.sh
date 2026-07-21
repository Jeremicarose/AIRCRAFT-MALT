#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATABASE_PATH="${DATABASE_PATH:-$ROOT_DIR/data/mlat_data.db}"
PROCESSOR_PID=""
API_PID=""

mkdir -p "$(dirname "$DATABASE_PATH")"

export DATABASE_PATH
export API_HOST="${API_HOST:-0.0.0.0}"
# Render injects PORT for the public listener. API_PORT remains available for
# local and non-Render deployments.
export API_PORT="${PORT:-${API_PORT:-5000}}"
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

echo "Starting MLAT API on ${API_HOST}:${API_PORT}"
if command -v gunicorn >/dev/null 2>&1; then
    gunicorn \
        --bind "${API_HOST}:${API_PORT}" \
        --workers 1 \
        --worker-class gthread \
        --threads 4 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --capture-output \
        api.rest_api:app &
else
    python3 "$ROOT_DIR/src/api/rest_api.py" &
fi
API_PID=$!

echo "Waiting for the MLAT API liveness endpoint..."
API_READY=false
for _ in $(seq 1 "${API_STARTUP_TIMEOUT_SECONDS:-45}"); do
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "MLAT API exited before becoming ready."
        wait "$API_PID"
        exit $?
    fi
    if python3 -c \
        'import sys, urllib.request; urllib.request.urlopen(sys.argv[1], timeout=1).read()' \
        "http://127.0.0.1:${API_PORT}/healthz" >/dev/null 2>&1; then
        API_READY=true
        break
    fi
    sleep 1
done

if [ "$API_READY" != "true" ]; then
    echo "MLAT API did not become ready within the startup timeout."
    exit 1
fi

echo "MLAT API is ready; starting processor with DATABASE_PATH=$DATABASE_PATH"
python3 "$ROOT_DIR/src/production_main.py" &
PROCESSOR_PID=$!

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
