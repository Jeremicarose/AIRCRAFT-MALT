# Environment Variables

This is the authoritative environment-variable reference. Copy `.env.example`
for local use. Never commit `.env`, wallet keys, API keys, or feed credentials.

Boolean values accept `1`, `true`, `yes`, or `on` as true. Other values are
false. Relative paths are resolved from the process working directory unless a
specific command says otherwise.

## Registry And CKB

| Variable | Default | Meaning |
|---|---|---|
| `CKB_NETWORK` | `testnet` | Network label exposed to clients. |
| `CKB_RPC_URL` | Pudge public RPC | CKB JSON-RPC endpoint. |
| `CKB_INDEXER_URL` | Pudge public indexer | Cell discovery endpoint. |
| `CKB_API_TIMEOUT` | `15` | Timeout in seconds for the live-ingest readiness RPC/indexer probe. |
| `CKB_TESTNET_EXPLORER_TX_URL` | Pudge transaction explorer | Base URL used for evidence links. |
| `RECEIVER_REGISTRY_TYPE_HASH` | empty | Registry contract code hash used for discovery. |
| `RECEIVER_REGISTRY_HASH_TYPE` | `type` in code | Historical compatibility uses `type`; reviewed writable deployments must use immutable `data1`. The example fails closed with `data1`. |
| `ALLOW_MUTABLE_REGISTRY_CODE` | `false` | Allows historical reads from a mutable code binding. Strict production still rejects it. |
| `CKB_SSL_VERIFY` | `true` | Verifies RPC and indexer TLS certificates. Strict production rejects `false`. |
| `CKB_MAX_RECORD_AGE_SECONDS` | `86400` | Maximum age accepted for an active Registry record. |
| `CKB_REGISTRY_REFRESH_SECONDS` | `30` | Registry refresh interval, clamped to at least five seconds. |
| `CKB_HYBRID_SIMULATION_MIN_RECEIVERS` | `4` | Minimum real receivers before hybrid simulation is unnecessary. |
| `NEXT_PUBLIC_REGISTRY_CODE_HASH` | empty | Browser-visible immutable Registry code hash. |
| `NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH` | empty | Browser-visible deployment transaction hash. |
| `NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX` | empty | Browser-visible deployment output index. |

The three browser deployment variables must come from the same verified
immutable deployment. Never use the historical mutable hash for writes.

## Receiver Ingest

| Variable | Default | Meaning |
|---|---|---|
| `FOURDSKY_API_KEY` | empty | Canonical feed credential. `FOURDSKYAPIKEY` is a deprecated compatibility alias. |
| `FOURDSKY_ENDPOINT` | empty | Canonical feed endpoint. `FOURDSKYENDPOINT` is a deprecated compatibility alias. |
| `FOURDSKY_TRANSPORT` | `auto` | `command-jsonl`, `websocket-json`, or demo-only `simulation`. Strict mode rejects `auto` and `simulation`. |
| `FOURDSKY_AUTH_HEADER` | `X-API-Key` | Feed authentication header name. |
| `FOURDSKY_AUTH_SCHEME` | empty | Optional authorization scheme such as `Bearer`. |
| `FOURDSKY_AUTH_TOKEN` | empty | Optional explicit feed token. Secret. |
| `FOURDSKY_SUBSCRIBE_MESSAGE` | empty | Optional WebSocket subscription message. |
| `FOURDSKY_BRIDGE_COMMAND` | empty | Direct command and arguments for JSONL ingest. It is parsed without a shell. |
| `FOURDSKY_EXTERNAL_SOURCE_ATTESTED` | `false` | Operator assertion that a remote source exists when a local port cannot be probed. It is not independent proof. |
| `FOURDSKY_SYNCHRONIZED_CLOCKS_ATTESTED` | `false` | Operator assertion supplementing per-receiver timing evidence. |
| `MLAT_RECEIVER_CONFIG` | empty | Path to the local receiver and clock qualification file. |
| `MLAT_RAW_OBSERVATION_LOG` | empty | New or empty per-run JSONL capture path. |
| `MAX_RECEIVERS` | `10` | Maximum active receivers selected by the runtime. |
| `MAX_CLOCK_UNCERTAINTY_NS` | `100` | Maximum accepted one-way receiver clock uncertainty. |

## Runtime And Evidence

| Variable | Default | Meaning |
|---|---|---|
| `MLAT_ENV_FILE` | `.env` | Dotenv file loaded at process import. Export this before startup; setting it inside `.env` is too late. |
| `DATABASE_PATH` | `data/mlat_data.db` | SQLite database path shared by the processor and API. |
| `LOG_LEVEL` | `INFO` | Python logging level. |
| `STRICT_PRODUCTION_MODE` | `false` | Enables fail-closed live configuration checks. |
| `SIMULATE_IF_UNAVAILABLE` | `true` | Allows demo fallback. Strict mode rejects true. |
| `SIMULATION_RETENTION_HOURS` | `24` | Replay observation retention. |
| `STATISTICS_RETENTION_DAYS` | `7` | Stored statistics retention. |
| `HEALTH_STALE_SIGNAL_SECONDS` | `120` | Health threshold for stale input. |
| `STATS_INTERVAL_SECONDS` | `60` | Runtime statistics publication interval. |
| `REQUIRE_LIVE_BENCHMARKABLE_OUTPUT` | `false` | Fails evidence publication unless live readiness gates pass. |
| `REGISTRY_EVIDENCE_BUNDLE` | historical bundle | Saved lifecycle evidence exposed by the API. |
| `BENCHMARK_REPORT_PATH` | live evidence path | Accuracy/evidence report consumed by the API. |
| `BENCHMARK_MAX_REPORT_BYTES` | `5242880` | Maximum report or evidence payload read by the API. |
| `PERFORMANCE_REPORT_PATH` | experimental path | Local performance report consumed by the API. |
| `RELIABILITY_REPORT_PATH` | experimental path | Local reliability report consumed by the API. |
| `BENCHMARK_MARKDOWN_PATH` | live README path | Markdown output used by evidence capture tools. |
| `LIVE_PREFLIGHT_REPORT` | `logs/live-preflight.json` | Saved strict-live preflight report used by `run-live.sh`. |

## Demo

| Variable | Default | Meaning |
|---|---|---|
| `DEMO_MODE` | `false` | Enables deterministic replay. Strict mode rejects true. |
| `DEMO_SCENARIO` | `default` | Replay scenario identifier. |
| `DEMO_READ_ONLY` | follows demo mode | Disables state-changing demo operations. |
| `DEMO_LABEL` | scenario label | Visible replay label. It must not imply live data. |
| `DEMO_AUTO_CONNECT` | follows demo mode | Starts replay processing automatically. |

## API And Frontend

| Variable | Default | Meaning |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Flask or Gunicorn bind host. |
| `API_PORT` | `5000` | API port outside Render. Local scripts use `5057`. |
| `PORT` | unset | Render-provided public port; overrides `API_PORT` in `render-entrypoint.sh`. |
| `API_DEBUG` | `false` | Flask debug mode. Never enable on a public deployment. |
| `CORS_ALLOWED_ORIGINS` | local origins | Comma-separated exact frontend origins. Do not use `*` with credentials. |
| `ENABLE_ADMIN_API` | `false` | Enables destructive maintenance endpoints. |
| `ENABLE_BACKGROUND_BROADCASTER` | `true` | Enables the API-side Socket.IO polling loop. |
| `API_KEY` | empty | Legacy fallback for `ADMIN_API_KEY`. Secret. |
| `ADMIN_API_KEY` | empty | Admin-route credential. Secret. |
| `API_KEY_HEADER` | `X-API-Key` | Header used for admin and account API keys. |
| `PUBLIC_PLAN_CODE` | `public_demo` | Database plan applied to anonymous requests. |
| `PREMIUM_PLAN_CODE` | `premium` | Database plan required for premium endpoints. |
| `RATE_LIMIT_ENABLED` | `false` | Enables the process-local sliding-window limiter. Strict API startup requires true. |
| `RATE_LIMIT_REQUESTS` | `120` | Requests allowed per client and window. |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Sliding rate-limit window. |
| `RATE_LIMIT_MAX_CLIENTS` | `10000` | Memory bound for tracked client buckets. |
| `API_STARTUP_TIMEOUT_SECONDS` | `45` | Seconds the process supervisor waits for `/healthz`. |
| `MLAT_API_INTERNAL_URL` | `http://127.0.0.1:5057` | Server-only API origin used by Next.js. |
| `NEXT_PUBLIC_API_BASE_URL` | same origin | Optional browser-visible API origin. Never put a credential here. |
| `NEXT_DIST_DIR` | unset | Optional Next.js build-directory override. Development defaults to `.next`; production defaults to `.next-production`. |
| `NODE_ENV` | framework-managed | Selects development or production behavior and the default Next build directory. |
| `GITHUB_REF_NAME` | GitHub-managed | Supplies the pushed tag to the stable-release checker in GitHub Actions. |
| `PLAYWRIGHT_EXECUTABLE_PATH` | Playwright-managed | Optional local path to an installed Chromium browser. CI installs Playwright's pinned Chromium instead. |
| `PLAYWRIGHT_API_PORT` | `4312` | Dedicated local demo API port used by browser QA. |
| `PLAYWRIGHT_FRONTEND_PORT` | `4311` | Dedicated local production frontend port used by browser QA. |
| `PLAYWRIGHT_DIST_DIR` | `.next-production` | Existing production build directory staged into an isolated runtime for browser QA. |
| `PATH` | inherited | System executable search path. Browser QA prepends the repository `.venv/bin` directory when it starts the local API. |
| `GITHUB_SHA` | GitHub-managed | Binds browser QA evidence to the checked-out source commit. Local runs derive the commit from Git. |
| `CI` | CI-managed | Enables Playwright retries. Browser checks always start fresh repository servers. |
| `BROWSER_QA_REPORT` | `tmp/browser-qa-report.json` | Optional output path for the Playwright Live Map and Registry accessibility evidence report. |
| `RUN_EXTERNAL_MAP_TEST` | unset | Set to `true` only for the opt-in Playwright check that reaches the public OpenStreetMap tile service; it is not required for the offline/browser release suite. |

The built-in rate limiter is correct only for the documented single-worker API.
A multi-worker or multi-node deployment needs a shared limiter at the ingress or
in a shared store.

## Optional Reference Acquisition

| Variable | Default | Meaning |
|---|---|---|
| `OPENSKY_CLIENT_ID` | empty | OpenSky OAuth client identifier used only by the reference-data fetch tool. |
| `OPENSKY_CLIENT_SECRET` | empty | OpenSky OAuth client secret. Never commit it. |

## Stable Release Values

`GITHUB_REF_NAME` and `GITHUB_SHA` are supplied automatically by GitHub Actions
when release readiness runs. They only bind CI evidence to a tag and commit;
local operators should leave them unset.

A stable release must record deployment values in immutable evidence rather
than relying on a maintainer's `.env`. At minimum it must use:

```dotenv
STRICT_PRODUCTION_MODE=true
DEMO_MODE=false
SIMULATE_IF_UNAVAILABLE=false
CKB_SSL_VERIFY=true
RECEIVER_REGISTRY_HASH_TYPE=data1
ALLOW_MUTABLE_REGISTRY_CODE=false
RATE_LIMIT_ENABLED=true
ENABLE_ADMIN_API=false
```
