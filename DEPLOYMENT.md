# Deployment

## Scope

Registry V2 is a CKB contract plus off-chain discovery modules; it is not a
long-running server. The MLAT reference is a single-node processor/API/frontend
deployment used to consume and validate registry records.

No production SLO, mainnet release, or horizontally scaled topology has been
validated.

Every supported configuration value is documented in the
[environment-variable reference](docs/ENVIRONMENT.md).

## Contract Build

```bash
cd contracts/registry-v2
make test
make check
```

The deployable binary is:

```text
contracts/registry-v2/target/riscv64imac-unknown-none-elf/release/receiver-registry
```

Generate a `ckb-cli` deployment configuration:

```bash
python3 tools/registry/generate_receiver_registry_deploy_config.py
```

Deployment, capacity balancing, signing, and broadcast depend on a separately
installed `ckb-cli`. Never place private keys in this repository. Follow the
[Registry Integration Guide](docs/registry/INTEGRATION.md).

Any contract source change creates a new binary and requires a new deployment.
Do not reuse the published V2 code hash for modified source.

## MLAT Reference: Local Processes

```bash
cp .env.example .env
python3 -m pip install --require-hashes -r requirements-dev.lock
```

Synthetic demonstration (explicitly labelled, with generated aircraft):

```bash
./run-demo.sh
```

Historical replay (separate database and API on port 5058):

```bash
./run-replay.sh
```

Open `/app/replay` with the frontend's `MLAT_API_INTERNAL_URL` set to
`http://127.0.0.1:5058`. See [historical replay](docs/mlat/HISTORICAL_REPLAY.md).

Strict live mode validates prerequisites before starting:

```bash
./run-live.sh
```

The installed `mlat-api` command uses one Gunicorn worker with four threads.
The launcher supervises one API process and one processor process. It uses one
SQLite database path and stops both when either exits.

Frontend:

```bash
cd reference/mlat/frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:3000/app/overview`.

Install/build `sdk/typescript` with `npm ci` before installing the frontend.
Use Node 22.23.1 and Python 3.12.11 to match the tested dependency locks.

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | Port | Responsibility |
|---|---:|---|
| `mlat-processor` | none | registry/ingest/correlation/solve/write |
| `mlat-api` | 5000 | REST, health, evidence, optional Socket.IO |
| `mlat-frontend` | 3000 | Next.js operator reference |

The processor and API share local `data/` and `logs/` bind mounts. This is a
single-host topology. Do not place them on different hosts with SQLite.
The Python image runs as UID/GID 10001. Prepare writable host directories for
that identity, or use locally managed volumes. The follow-up local Linux VM run verified both images, non-root startup, the
synthetic pipeline, restart, backup/restore and shutdown. See the
[container evidence](evidence/console-experience-2026-10-20/README.md).
Target-host operations remain a separate acceptance requirement.

## Strict Live Configuration

At minimum:

```dotenv
STRICT_PRODUCTION_MODE=true
DEMO_MODE=false
SIMULATE_IF_UNAVAILABLE=false
CKB_SSL_VERIFY=true
RECEIVER_REGISTRY_TYPE_HASH=0x...
RECEIVER_REGISTRY_HASH_TYPE=data1
ALLOW_MUTABLE_REGISTRY_CODE=false
RATE_LIMIT_ENABLED=true
FOURDSKY_TRANSPORT=command-jsonl
FOURDSKY_BRIDGE_COMMAND=python3 tools/mlat/multi_receiver_beast_bridge.py --config receiver-clocks.local.json --audit-log logs/field-trial-raw.jsonl
MLAT_RECEIVER_CONFIG=receiver-clocks.local.json
MLAT_RAW_OBSERVATION_LOG=logs/field-trial-raw.jsonl
FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED=true
MAX_CLOCK_UNCERTAINTY_NS=100
REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true
```

Run:

```bash
python3 tools/mlat/check_live_ingest_readiness.py --require-ready
```

The preflight opens and validates `MLAT_RECEIVER_CONFIG`, requires four unique
Registry V2 identities, checks current clock-validity windows, and probes every
configured Beast endpoint. It also requires a new or empty run-scoped raw
observation log whose path matches the bridge command. Startup checks are still
guardrails, not physical proof: every observation needs integer nanosecond
timing and clock provenance accepted by the runtime.

## Render Blueprint

`render.yaml` defines two ephemeral Render web services: a Python service for
the replay processor/API and a Docker service for the Next.js frontend. The
Python service uses `/tmp` SQLite. Set the frontend's server-only
`MLAT_API_INTERNAL_URL` to that API service's actual public HTTPS origin.
Render free web services cannot receive private-network requests, so a
`fromService: hostport` binding will not work for this free blueprint.
See [Render private networking](https://render.com/docs/private-network).
The blueprint prompts for this value instead of inventing a service URL.

This blueprint is a hosted walkthrough, not a production deployment template
and not evidence of live field operation. A public deployment URL and
production SLO have not been verified in this repository.

## Operational Requirements

Before any production claim:

- independently audit the contract
- use a reviewed owner-lock policy
- pin and verify deployment artifacts
- terminate TLS and restrict CORS
- keep admin routes off unless required
- keep rate limiting enabled; use a shared edge limiter before adding API workers
- move from SQLite if multi-node operation is required
- define backups, restore tests, metrics, alerts, SLOs, and rollback
- capture a live field evidence window

## Rollback

CKB contract cells cannot be upgraded in place. Rollback means stopping use of a
new code hash and returning consumers to a prior deployment where compatible.
Records under different code hashes are separate registries and must never be
merged without an explicit migration policy.

Schema version 2 migrates position identity and adds provenance in one SQLite
transaction. Existing rows keep their IDs and become UNKNOWN, because their
original data source cannot be recovered safely. Each runtime database is bound
to LIVE, SYNTHETIC, or HISTORICAL_REPLAY; switching modes requires a separate file.
There is no automated schema rollback. Back up SQLite before upgrades, including
its WAL contents through SQLite's backup API, and restore the backup if rolling
back application code. See [operations](docs/mlat/OPERATIONS.md).
