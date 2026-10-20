# Operator acceptance runbook

Status: **WAITING FOR WALLET / FEED / HOST INPUTS**. These are execution steps,
not results. Synthetic and historical runs cannot complete this acceptance.

## Inputs required, kept under operator control

- Staging host and public HTTPS origin, intended release revision/image digests,
  previous compatible image/database for rollback, and named operations owner.
- A separately authorized Pudge wallet and spending limit. Approve transactions
  in the wallet; never provide a raw private key or seed phrase. A second operator
  wallet is needed to demonstrate ownership transfer and wrong-owner rejection.
- At least four authorized independent receiver feeds with overlapping coverage,
  Registry identities and evidenced antenna coordinates. Prefer five or more
  suitably placed receivers for geometry and outlier assessment.
- Measured common-clock source, uncertainty, validity interval and calibration
  artifact for every receiver. Configure these locally; do not share feed URLs.
- A time-aligned independent reference track with known limitations and permission
  to retain/process it. Aircraft-reported ADS-B reference alone is not independent
  physical ground truth.
- Agreed observation/API rates, retention, recovery objectives, positional error
  limits, acceptable rejection rate and alert recipient. No values are invented here.

## Wallet lifecycle on the existing deployment

Start the exact candidate frontend and use its Receiver directory. Independently
verify the configured immutable code cell before opening the signer. Use a test
record whose label makes the controlled-test scope clear; do not claim synthetic
coordinates represent a physical receiver. Leave streams unadvertised for this
registry-only rehearsal.

1. Prepare create; inspect output Type ID, record, capacity, fee and owner lock.
   Stop at wallet approval until the operator accepts the spending limit.
2. After confirmation, verify the transaction and live cell through the node, then
   compare indexer/discovery. Indexer delay is pending, not permission to resubmit.
3. Update permitted metadata. Confirm exactly one sequence increment and the
   same immutable label/identity. Malformed input must be rejected before signing.
4. Transfer to the second operator wallet. Confirm the new output owner lock.
   Preparing an update with the previous wallet must fail ownership checks; do not
   spend funds broadcasting a deliberately invalid transaction.
5. Revoke using the current owner. Confirm the terminal tombstone, removal from
   eligible processing and inability to prepare resurrection.
6. Restart services and compare authoritative state again. Repeat read-only
   discovery during a controlled indexer/RPC interruption in staging; receivers
   must become ineligible, then recover only from fresh verified state.

Two registrations with the same human label may have different identities and
are permitted. A second independent creation using the same Type ID is invalid.
Contract VM tests exercise destructive/malformed signature/cardinality cases
without wasting testnet funds. Save only public transaction hashes, node/indexer
captures and signed-operation outcomes. Never include wallet material.

## Physical campaign

Follow [the field-trial procedure](../reference/mlat/FIELD_TRIAL.md) and the
receiver configuration template already in the repository. In a protected local
configuration, select explicit testnet URLs, immutable deployment, strict live
mode, real bridge command, receiver configuration and a new raw-observation log.
Use a new LIVE database, never a replay or synthetic database.

Run the actual preflight only after feed access is authorized:

```bash
python tools/mlat/check_live_ingest_readiness.py --receiver-config receiver-clocks.local.json --require-ready --output logs/field-preflight.json
./run-live.sh
```

Before starting the measured window, inspect provenance, all receiver identities,
clock validity/uncertainty, recent frames, geometry and component health. Do not
extend expired calibration windows or substitute arrival-at-server timestamps.
Use the existing `capture_reliability_window.py`, `capture_grant_evidence.py`,
`export_positions_for_benchmark.py` and `benchmark_mlat_against_reference.py`
commands documented in the field-trial guide, then verify the saved bundle with
`verify_live_evidence.py --require-publishable`. Record exact arguments locally;
share only the sanitized bundle and public identifiers.

Run the agreed load/observation window, then controlled cases: one feed disconnect,
delayed/duplicate/out-of-order input, insufficient receivers, authorized revocation
during processing, RPC/indexer interruption and recovery, process crash/restart,
and database backup/restore. Use staging fault injection; never damage a real feed
or production database to demonstrate recovery. Compare solved and rejected events,
horizontal/vertical/3D errors, p50/p95/p99 latency, CPU/RSS, queue depth/drops,
ingestion lag and failure rates against the pre-agreed criteria.

## Monitoring, restore and rollback acceptance

On the intended host, verify API liveness separately from processor readiness.
Exercise alerts for stale discovery, too few qualified receivers, clock expiry,
ingestion lag, queue drops, storage failure, solver rejections and disk pressure.
Capture the alarm and its recovery with UTC timestamps. Test the chosen notification
route only after its recipient and channel are explicitly authorized.

Back up the actual staging database, restore into a new file, and launch the API
against it. Compare IDs, source mode, nanoseconds, event counts and sample positions.
For version rollback, stop writers, select the approved previous image and its
compatible backup, switch to a new restored database path, then verify health and
fresh processing. Same-image restart/restore does not prove version rollback.

An operations owner must accept retention, backup schedule, restore timing, TLS,
authentication/edge limits, maintenance and incident response. Save results with
the actual source commit and image IDs. Leave every unexecuted step NOT RUN.
