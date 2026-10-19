# MLAT reference operations

This is a single-node validation console, not an aviation safety service.
Registry authorization is verified separately from receiver location, clock
quality and the truth of observations.

## Health and recovery

`/healthz` checks API process liveness. `/api/health` checks storage access and
reports HEALTHY, DEGRADED, FAILED or NOT CONFIGURED for components with a reason
and operator action. Frontend rendering cannot be established by the API; check
the frontend's own `/healthz` and open it in a browser. RPC/indexer health reflects
the last completed registry discovery, not an independent continuous probe.

| Symptom | Meaning | Action |
|---|---|---|
| Clock unqualified | Missing synchronization, missing integer timing, unknown source, or excessive uncertainty | Verify hardware timing and documented uncertainty; never assert qualification just to pass the gate |
| Feed endpoint blocked | Registry metadata selected a destination the operator has not approved | Review and add the exact URL to `FOURDSKY_ALLOWED_ENDPOINTS`; credentials only go to `FOURDSKY_ENDPOINT` |
| Registry unavailable | Current identities cannot be verified | Check TLS trust, RPC/indexer reachability and code hash. Receivers are excluded until discovery recovers; the API remains useful |
| Timestamp rejected | Time is malformed, outside the live window, duplicated or out of order | Check the receiver's common timebase and bridge ordering; use isolated replay for historical records |
| Position not stored | SQLite write failed | Check volume permissions, disk space and competing writers. Health exposes storage failures rather than silently claiming success |
| Provenance mismatch | A different runtime mode owns this database | Select a new `DATABASE_PATH`; do not relabel old rows |
| Map unavailable | External tiles or WebGL failed | Use the tables and inspector; retry the map. Attribution and browser referrer policy remain enabled |

## Storage and restart

SQLite uses WAL and a 30-second busy timeout. Schema version 2 migrates position
identity and adds source metadata atomically. Old rows become UNKNOWN. Precise
nanosecond values are stored and returned as decimal strings, preserving them
in JavaScript clients. Every solution records its receiver geometry and event ID.

Back up a running database using SQLite's online backup interface rather than
copying just the main file while WAL writes continue. Test restoration into a
separate path before relying on backups. Preserve the original file for rollback.
Synthetic retention deletes only SYNTHETIC positions and synthetic statistics.
Live retention remains explicit operator maintenance; it is not automatically
enabled by the demo retention setting. Schedule VACUUM outside ingestion.

An API process reads bounded runtime snapshots from the shared database. A stopped
processor writes its stopped state; stale snapshots are not treated as fresh
clock qualification. Receiver updates/ownership changes discard pending old
observations and reset clock qualification.

## Observation and solution contracts

See [input contract](data-source-contract.md). Positions include `data_provenance`,
`source_id`, `timestamp_ns`, `source_timestamp_ns`, `correlation_id`, captured
receiver geometry, solver method/residual/iterations and observation limitations.
`quality.confidence_calibrated` is false. The retained solver quality/spread
fields are heuristics, not a probability or a validated error bound.

Recent positions are bounded to 1,000 records, public access to 100. Track history
has explicit limits and access policy. Replay is paginated separately. JSON writes
are size-limited and reject duplicate keys. The API's rate limiter is process-local;
deploy one API worker or supply an edge limiter before increasing workers.

## Diagnostics and secrets

Pipeline transitions emit JSON events including observation rejection, correlation,
clock qualification, solve start/completion/failure and position creation. IDs link
stages without embedding credentials. The bridge's command line and arbitrary
stderr are not logged. Process termination has a bounded grace period.

The Diagnostics page exports `/api/diagnostics/bundle`. This uses an explicit field
allowlist: source context, component state, counters, bounded rejection records and
receiver qualification. It excludes environment dumps, feed URLs, API keys,
subprocess arguments and raw stderr. Receiver identities and registered positions
are public metadata; review the bundle before sharing it outside your project.

## Tested operating envelope

`python tools/mlat/measure_pipeline_envelope.py --output /tmp/envelope.json`
measures 4, 5 and 10 synthetic receiver callbacks, three aircraft, 100 events per
scenario, at target rates of 100, 1,000 and 10,000 observations/second. It measures
the actual parser, runtime validation, correlator, solver and SQLite writes.
It is an in-process test, not a physical network or long-duration soak test.
It excludes the production loop's 100 ms batching wait. See the production
readiness report for measured rates, CPU, memory and limitations.
