# Deployment

## Scope

Registry V2 is a CKB contract plus off-chain discovery modules; it is not a
long-running server. The MLAT reference is a single-node processor/API/frontend
deployment used to consume and validate registry records.

No production SLO, mainnet release, or horizontally scaled topology has been
validated.

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

Replay mode:

```bash
./run-demo.sh
```

Strict live mode validates prerequisites before starting:

```bash
./run-live.sh
```

The launcher supervises one API process and one processor process. It uses one
SQLite database path and stops both when either exits.

Frontend:

```bash
cd reference/mlat/frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:3000/app/overview`.

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

## Strict Live Configuration

At minimum:

```dotenv
STRICT_PRODUCTION_MODE=true
DEMO_MODE=false
SIMULATE_IF_UNAVAILABLE=false
CKB_SSL_VERIFY=true
RECEIVER_REGISTRY_TYPE_HASH=0x...
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

`render.yaml` deploys the replay processor and API as one Python service. It is
ephemeral and uses `/tmp` SQLite. It does not build or host the Next frontend.

This blueprint is a backend walkthrough, not a production deployment template
and not evidence of live field operation.

## Operational Requirements

Before any production claim:

- independently audit the contract
- use a reviewed owner-lock policy
- pin and verify deployment artifacts
- terminate TLS and restrict CORS
- keep admin routes off unless required
- add rate limiting and dependency scanning
- move from SQLite if multi-node operation is required
- define backups, restore tests, metrics, alerts, SLOs, and rollback
- capture a live field evidence window

## Rollback

CKB contract cells cannot be upgraded in place. Rollback means stopping use of a
new code hash and returning consumers to a prior deployment where compatible.
Records under different code hashes are separate registries and must never be
merged without an explicit migration policy.

The MLAT reference has no automated schema rollback. Back up SQLite before
upgrades and validate restore behavior in the target environment.
