# Deployment Guide

This guide covers local and hosted deployment patterns for MLAT Airspace Console.

The repository is currently best suited for:

- local operation
- hosted replay/demo deployments
- single-node operational deployments
- integration environments for live external feeds and receiver registries

It should not be described as a fully validated horizontally scaled production service.

## Deployment goals

A deployment should let operators and evaluators inspect:

- recent aircraft outputs
- quality and uncertainty signals
- freshness and runtime status
- receiver context
- API access-tier behavior

## Basic local deployment

### 1. Clone and configure

```bash
git clone <your-repo>
cd mlat-system
cp .env.example .env
```

Edit `.env` with the environment values relevant to your setup.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the stack

API:

```bash
mlat-api
```

Processor:

```bash
mlat-processor
```

### 4. Verify

```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/receivers
curl http://localhost:5000/api
```

Open:

- `http://localhost:5000/`
- `http://localhost:5000/dashboard.html`

## Docker deployment

```bash
cp .env.example .env
docker-compose build
docker-compose up -d
docker-compose logs -f
```

## Environment guidance

Typical variables include:

```bash
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_TYPE_HASH
SIMULATE_IF_UNAVAILABLE=false

FOURDSKYAPIKEY=your_api_key_here
FOURDSKYENDPOINT=wss://your-feed-endpoint

DATABASE_PATH=/app/data/mlat_data.db
API_HOST=0.0.0.0
API_PORT=5000
LOG_LEVEL=INFO
```

Additional runtime controls may include health/stats and demo-mode settings depending on deployment goals.

## What to verify after deploy

### Health and freshness

```bash
curl http://localhost:5000/api/health
```

Check for:

- database status
- runtime freshness fields
- broadcaster status
- stale-signal indicators

### Product outputs

Verify:

- `/api/positions/recent`
- `/api/aircraft/<id>/track`
- `/api/receivers`
- `/dashboard.html`

Check that payloads and UI expose quality-oriented context where expected.

### Commercial behavior

If you are using API keys and plans, verify:

- public/demo limits are enforced
- premium-only routes behave correctly
- statistics access matches plan expectations
- stream entitlements are required where expected

## Hosted replay/demo deployment

Use this mode when you want a stable, read-only product walkthrough.

Recommended environment values:

```bash
FOURDSKY_TRANSPORT=simulation
SIMULATE_IF_UNAVAILABLE=true
ENABLE_ADMIN_API=false
ENABLE_BACKGROUND_BROADCASTER=true
DEMO_MODE=true
DEMO_SCENARIO=default
DEMO_READ_ONLY=true
DEMO_LABEL=Hosted demo · Northeast replay
DEMO_AUTO_CONNECT=true
DATABASE_PATH=/var/data/mlat_data.db
API_HOST=0.0.0.0
API_PORT=5000
```

Expected characteristics:

- homepage and dashboard indicate replay/demo mode
- the deployment is safe for read-only exploration
- the API remains available for inspection
- admin cleanup routes remain unavailable if disabled

## Render hosted deployment

This repository includes `render-entrypoint.sh` for a single-service Render topology.

Recommended start command:

```bash
./render-entrypoint.sh
```

The script:

- creates the parent directory for `DATABASE_PATH`
- starts `src/production_main.py` in the background
- starts `src/api/rest_api.py` in the foreground
- stops the background processor when the web process exits

## Security guidance

- do not commit secrets
- keep feed credentials and registry credentials separate
- restrict admin functionality where not needed
- use TLS and a reverse proxy for public deployments
- treat hosted demo and premium environments as different operational surfaces

## Backup and maintenance

For single-node SQLite deployments:

- keep the DB on persistent storage
- snapshot or back up the database regularly
- monitor disk growth and cleanup behavior
- validate restore procedures before relying on backups

## Scaling note

The current repository is strongest in single-node operation. If you need multi-node or high-scale production behavior, treat that as further engineering work rather than an already-proven property of this codebase.

## Troubleshooting

### Inspect service state

```bash
docker-compose ps
docker-compose logs mlat-processor
docker-compose logs mlat-api
```

### Common issues

**Database locked**

```bash
docker-compose down
rm data/mlat_data.db-shm data/mlat_data.db-wal
docker-compose up -d
```

**API not responding**

```bash
docker-compose logs mlat-api
docker-compose restart mlat-api
```

**No useful positions**

Check:

- receiver geometry
- timestamp quality
- receiver count
- feed health
- runtime freshness and health output

## Related docs

- [README.md](../README.md)
- [GETTING_STARTED.md](GETTING_STARTED.md)
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- [CKB_INTEGRATION_GUIDE.md](CKB_INTEGRATION_GUIDE.md)
