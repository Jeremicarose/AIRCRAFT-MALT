# Controlled tester guide

Start with **local synthetic or historical replay**. You do not need a wallet,
real receiver or account secret. This guide supports controlled validation;
[Gate B is not yet fully satisfied](release-checklist.md). Do not use the output
for flight navigation, separation or safety decisions.

## Install and start

Use Python 3.12.11 and Node 22.23.1. In a fresh checkout, follow the exact locked
installation commands in [deployment and recovery](deployment-and-recovery.md).
Build the SDK before the frontend. Keep the repository's existing historical
fixtures; they include all data needed for offline replay.

For the simplest walkthrough, activate the Python environment and run:

```bash
source .venv/bin/activate
MLAT_ENV_FILE=/dev/null DATABASE_PATH=data/tester-historical.db API_HOST=127.0.0.1 API_PORT=5058 ./run-replay.sh
```

Leave that terminal running. In another terminal, using Node 22.23.1:

```bash
MLAT_API_INTERNAL_URL=http://127.0.0.1:5058 npm --prefix reference/mlat/frontend start
```

Open `http://localhost:3000/app/replay`. Expect **HISTORICAL REPLAY**, **362 events**,
**270 solved**, **92 rejected**. A rejected event is a retained result, not a hidden
error. Select an event and step through ingestion, validation, supplied grouping,
qualification, solve and storage. Receiver serials are dataset identifiers, not
CKB registrations. Original relative arrival times must not change to today's time.

For synthetic activity, stop both terminals with Ctrl-C. Export the safe example
and start the demo, then start the frontend in another terminal:

```bash
set -a
source docs/production-readiness/testing.env.example
set +a
./run-demo.sh
```

```bash
MLAT_API_INTERNAL_URL=http://127.0.0.1:5057 npm --prefix reference/mlat/frontend start
```

Open `/app/overview`, `/app/aircraft`, `/app/receivers` and `/app/pipeline`.
Expect SYNTHETIC labels and real solver successes/failures from synthetic input.
An unsuccessful solve must not appear as a newly stored position. Registered,
online, clock-qualified and contributing are different states.

## Scenarios to record

| Scenario | Expected result |
| --- | --- |
| Historical successful and rejected events | Both remain inspectable; no live claim; residual/iterations and original timing visible |
| Synthetic cold start | Loading/empty state first, then observations and stored solver output; no fake readiness while starting |
| Stop backend while frontend stays open | Visible service/disconnection error; last data is not silently presented as fresh |
| Restart backend with the same mode/database | Prior positions preserved, new activity resumes; no relabelling or duplicate historical events |
| Keyboard and narrow viewport | Navigation, event selection and inspectors remain usable without a mouse |
| Diagnostics | Shows component reasons, feed/clock/registry separation and export action; unconfigured components are not called healthy |
| Registry directory with internet available | Public testnet records and owner/lifecycle state; backend inventory may differ because it is mode-specific |
| Attempt mode change using the same database | Clear refusal; choose a new file instead |

Public registry discovery uses the configured testnet services and may fail during
an external outage. This does not invalidate offline replay. Registry lifecycle
failure/revocation cases can be exercised safely through automated tests:

```bash
MLAT_ENV_FILE=/dev/null python -m pytest -q tests/registry tests/mlat/test_runtime_guardrails.py tests/mlat/test_registry_pipeline_e2e.py
npm --prefix sdk/typescript test
```

Do not sign registry actions as part of the default walkthrough. Fresh create,
update, transfer and revoke require a separately approved operator-managed testnet
wallet and capacity. The owner keeps control of signing; the tester never supplies
private keys or seed phrases to the app or to a defect report. See the operator
campaign in [test plan](test-plan.md).

## Run and compare benchmarks

Use new output directories so earlier results remain available:

```bash
MLAT_ENV_FILE=/dev/null python tools/mlat/run_compact_solver_benchmark.py --output artifacts/tester-run-1/compact.json
MLAT_ENV_FILE=/dev/null python tools/mlat/run_reproducible_benchmark.py --output-dir artifacts/tester-run-1/synthetic
MLAT_ENV_FILE=/dev/null python -m pytest -q
```

Compare against [benchmark results](benchmark-results.md), including all 92
historical rejections and the large vertical error tail. Small cross-platform
floating-point differences do not establish a quality improvement. Never edit the
fixture or relax acceptance thresholds to make a run pass.

## Export diagnostics and report defects

Use Diagnostics → Export diagnostics, or save the allowlisted endpoint:

```bash
curl --fail --output artifacts/tester-diagnostics.json http://127.0.0.1:5058/api/diagnostics/bundle
```

Create `artifacts/` first if it does not exist. Use 5057 for synthetic mode.
Review the bundle before sharing: it includes receiver identifiers and timestamps,
but no environment dump, feed credentials, raw clock-source text, private feed URLs,
wallet secrets, command arguments or raw child-process logs. Do not attach `.env`,
receiver credentials, wallet exports, raw database files or unreviewed service logs.

Copy this template into the project's approved defect channel; this guide does not
send anything automatically:

```text
Title:
Application revision / working-tree changes:
OS, Python, Node, browser versions:
Mode: SYNTHETIC / HISTORICAL_REPLAY / separately authorized LIVE
Exact steps and commands (replace private paths/URLs with placeholders):
Expected behavior:
Observed behavior, UTC time, HTTP status or visible error:
Fixture event ID / synthetic scenario:
Reproducibility: always / intermittent, attempts and failures:
Sanitized diagnostic filename and screenshots:
Impact and any temporary workaround:
```

## Authorized live feeds, limitations and reset

Live testing needs explicit feed permission, enough independent receivers, verified
identity/location provenance, original frames and qualified common-clock timestamps.
Use a separate protected LIVE configuration/database and strict preflight. An ordinary
decoded aircraft-position feed is not a raw multi-receiver MLAT source. Ask the
operator to configure private URLs locally; never paste them into a public report.

Known limits: single-host SQLite, no independent security audit, no established
production accuracy/availability claim, no completed physical multi-receiver campaign,
and incomplete release-bound/container evidence. Live/usage data retention is not
automatically managed comprehensively. Historical data remains in its dedicated
database; demo cleanup applies only to synthetic data and configured statistics.

Reset safely by stopping both services and choosing a **new database path**. Keep
the old file as evidence. Restore only into a new destination using the documented
backup tool. Do not delete shared `data/`, clear a wallet, or attempt to reverse an
on-chain revocation. To leave testing, Ctrl-C both terminals and verify their local
ports are closed. No deployment or external communication is required.
