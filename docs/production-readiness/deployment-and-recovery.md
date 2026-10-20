# Deployment and recovery

This is a procedure for local validation and later operator review, not evidence
that production infrastructure has been deployed. Local container builds, synthetic processing, restart and backup/restore have
now passed; target-host deployment and restore remain unverified. See the
[20 October evidence](../../evidence/console-experience-2026-10-20/README.md). See the independent [release gates](release-checklist.md).

## Supported setup

The reproducible baseline is Python **3.12.11**, Node **22.23.1**, Rust **1.95.0**,
CKB target `riscv64imac-unknown-none-elf`, and Ubuntu 24.04 CI. The current local
validation ran on macOS. Install Git and a C compiler; the contract also needs
the RISC-V compiler/toolchain described in `contracts/registry-v2/README.md`.
Docker Engine/Compose is optional for local source execution and required to
verify container deployment. Physical receivers and a wallet are not prerequisites
for synthetic/historical tests.

From a new checkout, install the locked dependencies and package:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --require-hashes -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation .
python -m pip check
node --version
npm --prefix sdk/typescript ci
npm --prefix reference/mlat/frontend ci
npm --prefix reference/mlat/frontend run build
```

Verify the displayed patch versions against `.python-version` and `.nvmrc`.
Use `nvm use` if nvm manages Node. The fresh Python environment, wheel installation
and production frontend build were executed locally; clean committed source and local container execution now also pass.
Public CI and target-host acceptance are separate requirements.

The API initializes/migrates SQLite schema version 2 on connection; there is no
separate migration service. Before upgrading any existing database, make an online
backup and validate restoration into a new destination. Do not point test commands
at a live database. UNKNOWN legacy provenance is intentionally not inferred.

## Safe local modes

Use the supplied [testing environment example](testing.env.example). It has no
credentials, registered feed destination or production-network default. Export it
in each terminal before starting the demo:

```bash
set -a
source docs/production-readiness/testing.env.example
set +a
./run-demo.sh
```

This binds the backend to loopback, uses `data/controlled-synthetic.db`, disables
administrative writes and the optional broadcaster, and explicitly generates
synthetic observations. In another terminal with the same environment and Node
version, start the frontend:

```bash
npm --prefix reference/mlat/frontend start
```

Open `http://localhost:3000/app/overview`. To use historical data instead, stop
the synthetic services, then use a distinct database and backend origin:

```bash
MLAT_ENV_FILE=/dev/null DATABASE_PATH=data/controlled-historical.db API_HOST=127.0.0.1 API_PORT=5058 ./run-replay.sh
```

In the frontend terminal:

```bash
MLAT_API_INTERNAL_URL=http://127.0.0.1:5058 npm --prefix reference/mlat/frontend start
```

Open `/app/replay`. Replaying the same fixture is idempotent; it must not create
duplicate events or relabel data as live. The frontend registry directory can
independently use public testnet discovery. Offline availability of replay does
not imply public RPC availability.

## Health, shutdown and troubleshooting

```bash
curl --fail http://127.0.0.1:5057/healthz
curl --fail http://127.0.0.1:5057/api/health
curl --fail http://127.0.0.1:5057/api/readiness
curl --fail http://localhost:3000/healthz
```

Use port 5058 for historical mode. `/healthz` proves process responsiveness;
component health and readiness must be inspected separately. A historical replay
can have a healthy API and completed replay while live clocks/discovery remain
unconfigured. That is expected. Runtime health is based on stored snapshots; it
is not an independent frontend rendering or continuous chain probe.

Stop foreground services with Ctrl-C and wait for the API/processor children to
exit. Command feed transports terminate then kill a child after a bounded grace
period. The process supervisor shuts down the other service if one exits. A
two-minute restart observation passed locally; abrupt power-loss durability and
target-host service-manager behavior remain unverified. SQLite uses WAL with
`synchronous=NORMAL`, which does not promise preservation of every recent commit
through power loss.

If startup fails, check the stated missing variable/version, database directory
permissions, port conflicts and mode binding. Never resolve a mode mismatch by
editing stored provenance. For blocked feeds, review the exact allowlist and
timing source. For registry failure, inspect trusted RPC/indexer reachability,
TLS, immutable code hash and scan latency; old registry receivers are excluded
until discovery succeeds. Do not turn off TLS verification to obtain a pass.

## Backup and restore

These commands copy SQLite through its online backup API, including committed WAL
data, check integrity, use a private temporary file, and refuse an existing target:

```bash
python tools/mlat/database_snapshot.py backup --source data/controlled-synthetic.db --destination backups/controlled-before-upgrade.db
python tools/mlat/database_snapshot.py restore --source backups/controlled-before-upgrade.db --destination data/controlled-restored.db
```

Choose a new destination for every run. Start a separate API against the restored
file and compare event counts, IDs, nanoseconds, provenance and representative
positions before switching services. Regression tests verify committed WAL rows,
restored IDs/provenance, continued writes and rollback on migration failure.
Never copy only the main `.db` file while writers are active, and never overwrite
the active database during restore.

For staging/production, an operator must assign backup ownership, encrypted
storage, access policy and an off-host schedule; choose recovery-point and
recovery-time objectives from business requirements. Run a timed restore on the
target host and record its results. Local tests do not verify that operational
backup schedule. Live positions, receiver metadata and usage records have no
automatic comprehensive retention policy. Synthetic position/statistics retention
is separate; historical replay persists until its dedicated database is retired.

## Controlled live/testnet setup

Use a separate protected environment file. Configure explicit `CKB_NETWORK=testnet`,
the verified public/operated node and indexer URLs, current immutable `data1` code
hash, an authorized feed/bridge, and an isolated LIVE database. Keep
`SIMULATE_IF_UNAVAILABLE=false`, `DEMO_MODE=false`, `CKB_SSL_VERIFY=true`,
`ALLOW_MUTABLE_REGISTRY_CODE=false`, `RATE_LIMIT_ENABLED=true` and
`STRICT_PRODUCTION_MODE=true`. Set `FOURDSKY_TRANSPORT` explicitly. A missing live
configuration must fail preflight, not silently become a synthetic source.

Document each receiver's identity, coordinates/provenance, clock source, measured
uncertainty and validity period. Only set synchronization attestations when true.
Review `docs/reference/mlat/LIVE_INGEST.md` and the receiver configuration template,
then run `python tools/mlat/check_live_ingest_readiness.py --require-ready` before
`./run-live.sh`. This preflight may contact configured receiver endpoints; run it
only for feeds the operator has authorized. No secret belongs in frontend build
arguments, public URLs, benchmark output or committed files.

Fresh wallet transactions and deployments need separate explicit approval. The
current testnet code hash and evidence are documented in the root `.env.example`
and saved deployment bundle; do not substitute placeholders into signed transactions.

## Staging deployment and rollback

The existing Dockerfiles use digest-pinned base images and non-root users. The
frontend build also needs `docs/pilot/assets/`, which is now explicitly copied
because the pilot route imports those public diagrams outside the frontend tree.
The isolated build reproduced the missing imports before this repair.
With those assets present and dependencies freshly installed, the isolated
production frontend build passed. This does not substitute for running the image.
The Python user is UID/GID 10001; frontend UID/GID is 1001. Host bind mounts need
appropriate access without making the database world-writable. Preserve separate
volumes for synthetic, historical and live modes. Compose currently publishes
ports directly; use loopback bindings or a reviewed TLS gateway before exposure.

On an approved local/staging Docker host, build and verify without publishing:

```bash
docker build --tag mlat-system:ci .
docker build --file reference/mlat/frontend/Dockerfile --tag mlat-frontend:ci .
python tools/check_container_runtime.py --output artifacts/container-smoke.json
```

The smoke tool creates uniquely named disposable resources and removes its own
resources afterward. It checks non-root startup, public assets, proxy, persistence
and shutdown. The original audit could not execute this command. The later local Linux VM run
passed processor → storage → API → frontend checks, restart, backup/restore and
shutdown; its actual image identifiers and reports are in the linked evidence.
Do not treat a local VM result as target-host recovery evidence.

Before external exposure, select an immutable application revision/image digest,
complete the independent gates, back up state, restrict CORS and secrets, configure
edge authentication/rate/connection limits, resource quotas, log rotation and
health alerts. Keep one processor and one API worker. Assign operational owners
and on-call contact routes through the organization's own process.

Rollback: stop ingestion and API, preserve the failing database/logs privately,
restore the pre-upgrade backup to a **new path**, select the previous compatible
application digest and database path, start API then processor, and verify counts,
source mode, health and fresh authorized observations. There is no automatic
schema downgrade. Never run old code against a newer schema without compatibility
evidence. Never reinterpret a different contract code hash as the same registry;
on-chain revocation is permanent and cannot be rolled back by restarting software.

For an incident, first contain exposure/stop suspect feeds, preserve a sanitized
diagnostic bundle and protected raw evidence, determine impact, rotate affected
deployment credentials if needed, restore/roll back from verified artifacts, and
record recovery tests and follow-up defects. Incident ownership and a rehearsal
on the target environment are still Gate C requirements.


## Hosted testing publication — 20 October 2026

The user authorized application publication and deployment after the local checks.
The prepared release branch includes the immutable local evidence packages. It is
an explicitly synthetic hosted walkthrough, not a new production-readiness claim.
Wallet signing, contract deployment and paid resources remain outside this action.

The Render free-plan blueprint now requires the API service's actual public HTTPS
origin in the frontend's server-only `MLAT_API_INTERNAL_URL`. Free web services
cannot receive private-network traffic; the earlier `hostport` binding was invalid
for this plan ([Render documentation](https://render.com/docs/private-network)).
Deploy the API first, set its real HTTPS origin, then deploy the console at the
same reviewed commit. Verify both health endpoints, proxied API provenance,
`/app/guide`, static assets and browser navigation before claiming deployment success.
A valid hosting login and service identities are required; no guessed hostname
or local container result substitutes for that verification.
