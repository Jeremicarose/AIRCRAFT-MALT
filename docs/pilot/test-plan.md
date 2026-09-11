# Pilot Acceptance Test Plan

Run this plan against the exact commit and deployment that participants will
use. Preserve logs and public testnet transaction identifiers. Never preserve
wallet secrets or private feed credentials.

## Entry gates

- Rust, Python, TypeScript SDK, frontend type, and frontend production builds pass.
- Registry deployment uses CKB testnet and immutable `hash_type=data1` code.
- Deployment binary hash, outpoint, source commit, and evidence manifest agree.
- A maintainer completes the browser create, update, transfer, history, and
  revoke flow with disposable test identities.
- MLAT replay data is visibly labeled replay. Live data is labeled live only
  when strict live readiness passes.
- Recovery instructions work in a clean checkout.

## Receiver lifecycle

| Test | Expected result |
|---|---|
| Connect wallet | Wallet and application both show CKB testnet |
| Register | One live Registry cell is created with a canonical 32-byte identity |
| Discover | Indexer discovery finds the record without its outpoint |
| Inspect | Owner lock, label, sequence, status, outpoint, and transaction are visible |
| Update | Allowed metadata changes; identity and label stay fixed; sequence adds one |
| Transfer | New owner lock is visible; identity and label stay fixed |
| Revoke | Terminal tombstone is committed; stream fields are removed |
| History | Create, update, transfer, and revoke form one verified spend chain |

## Registry to MLAT

| Stage | Expected result |
|---|---|
| Registry | Current receiver record is available |
| Discovery | Complete indexer pagination returns it once |
| Eligibility | Only active receivers with MLAT capability enter the pool |
| Ingest | Observation identity is bound to its connection or trusted local adapter |
| Correlation | Same transmission is grouped across at least four qualified receivers |
| Solve | MLAT position includes contributing receiver identities |
| Aircraft investigation | User can open every contributing receiver |
| Reverse lookup | Receiver inspector shows Registry identity, owner, status, and history |
| Return path | User returns to the selected aircraft with context preserved |

## Failure propagation

| Failure | Required behavior |
|---|---|
| Receiver revoked | Remove it from active discovery and the MLAT pool on refresh |
| Receiver transferred | Show the new owner without changing canonical identity |
| Receiver missing | Mark unavailable and remove it from the active pool |
| Payload claims another receiver | Reject the payload |
| Two identities share one WebSocket | Reject configuration because the connection is ambiguous |
| Duplicate live identity | Quarantine the identity and fail closed |
| Malformed or stalled pagination | Reject the entire incomplete discovery result |
| Indexer or Registry refresh fails | Remove Registry receivers until a complete refresh succeeds |
| Heartbeat from revoked identity | Reject it; heartbeat cannot change lifecycle state |
| Feed becomes stale | Keep Registry lifecycle state separate; mark operational state stale |
| Contract uses mutable type hash in strict mode | Refuse startup |

## Clean external-user test

In a new checkout with no project caches or databases:

1. Follow only the public quick start.
2. Install locked Python and Node dependencies.
3. Run the test suite.
4. Start processor, API, and frontend.
5. Open the Live Map from the root URL.
6. Inspect the Receiver directory lifecycle workflow, then complete the MLAT reference workflow.
7. Stop the indexer path and verify fail-closed behavior.
8. Restore it and verify recovery.
9. Restart all services and verify persisted non-secret evidence.

The test fails if a maintainer must edit source, manually repair a database, or
explain an unlabeled simulated value.

## Product measurements

Record registration, discovery, lifecycle, and MLAT completion rates; critical
errors; time to first successful task; and user-blocking issues. Measure each
task from the participant's first action to completion or abandonment.
