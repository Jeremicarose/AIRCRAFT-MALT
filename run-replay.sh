#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
export DATABASE_PATH="${DATABASE_PATH:-$ROOT_DIR/data/mlat_historical.db}"
export API_HOST="${API_HOST:-127.0.0.1}"
export API_PORT="${API_PORT:-5058}"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
export MLAT_ENV_FILE=/dev/null
export FOURDSKY_TRANSPORT=historical-replay
export DEMO_MODE=false
export STRICT_PRODUCTION_MODE=false
export SIMULATE_IF_UNAVAILABLE=false
export RECEIVER_REGISTRY_TYPE_HASH=""
export ENABLE_ADMIN_API=false
export ENABLE_BACKGROUND_BROADCASTER=false
export RATE_LIMIT_ENABLED=true
python3 "$ROOT_DIR/tools/mlat/replay_compact_dataset.py" --database "$DATABASE_PATH"
echo "HISTORICAL REPLAY API: http://${API_HOST}:${API_PORT}; source times remain dataset-relative."
exec gunicorn --bind "${API_HOST}:${API_PORT}" --workers 1 --worker-class gthread --threads 4 mlat_reference.api.rest_api:app
