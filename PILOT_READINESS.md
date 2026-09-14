# Pilot Readiness

Status date: 2026-09-14
Overall status: `NOT READY`

## What happened

The repository now passes its contract, Python, TypeScript SDK, schema
conformance, and frontend compilation checks. Security tests also confirm that
MLAT refreshes Registry state while running, rejects identity mismatch, rejects
ambiguous shared WebSocket identities, and fails closed when discovery becomes
incomplete.

The older `hash_type=type` deployment remains historical and read-only. A fresh
Pudge testnet bundle now records an immutable `data1` deployment and signed
create-update-transfer-revoke lifecycle for the current contract binary.
Its saved chain data passes the offline verifier, and saved live RPC and indexer
reports pass. Local CI now rebuilds the exact deployed binary and passes. GitHub
CI provenance and an independent security
review are still missing; the stable release gate must repeat the live check.

## Readiness by area

| Area | Status | Evidence | Required next action |
|---|---|---|---|
| Registry source | Prepared | 5 Rust host and 11 CKB-VM tests pass | Independent review |
| Registry deployment | Partial | Fresh evidence binds the deployed binary with `data1`, records the signed lifecycle, and includes passing live RPC/indexer and local CI reports | Add GitHub CI provenance, repeat the live check at release, and obtain independent review of the exact binary hashes |
| Python discovery | Prepared | Pagination, duplicate, schema, and binding tests pass; the fresh revoked identity is excluded by live verification | Keep monitoring the public indexer during pilot runs |
| TypeScript SDK | Prepared | 72 SDK tests pass, discovery and history pagination fail closed, and the current testnet factory uses the immutable deployment | Run a funded CCC wallet lifecycle through the browser |
| MLAT replay | Prepared | Python integration suite passes | Keep replay labels visible |
| MLAT live field use | Blocked | Harness exists; no synchronized physical run | Obtain four qualified receiver feeds |
| UI | Partial | 22 current unit/contract tests and the 17-route Node 22 production build pass; malformed Registry rows without explicit canonical identity are excluded; the older source-bound bundle records nine browser checks for commit `4fc8fce` | Run the current 12-test browser suite from a clean final commit in public CI and complete a funded wallet-signed lifecycle |
| Public deployment | Blocked | No verified complete hosted URL | Deploy frontend, API, and processor |
| Recruitment | Prepared, not executed | 13 public leads; messages and tracker exist | Send authorized permission requests and invitations |
| Pilot | Not started | 0 contacted, 0 confirmed, 0 completed | Clear P0 gates before inviting |

## Security status

| Finding | Status | Meaning |
|---|---|---|
| H-01 mutable contract implementation | Fixed on the fresh testnet deployment | The new lifecycle uses `data1`, which binds the script to the deployed bytes; strict mode still rejects the historical `type` deployment, and independent review remains required |
| H-02 runtime Registry changes | Fixed and verified | A real testnet revocation was removed without restarting the process; a focused regression test proves owner transfer updates the running inventory |
| H-03 feed impersonation | Fixed for supported paths | Bound identity mismatch is rejected; shared WebSocket identity is rejected; local Beast bridge uses endpoint configuration |
| M-01 self-declared `updated_at` authority | Fixed | Capacity selection uses canonical identity ordering, not record time |
| M-02 pagination completeness | Fixed | Empty terminal page is required; missing, repeated, or excessive cursors fail closed |
| M-03 independent evidence derivation | Fixed for saved evidence | Verifier recalculates transaction hashes, Type ID, spend chain, locks, records, and binary hashes |
| M-04 V2 schema mismatch | Fixed in current source | Rust, Python, and TypeScript share corpus version 2 and pass 171 assertions |
| `u64` precision | Fixed | Python bounds and TypeScript `bigint` preserve exact values |
| Testnet evidence generation | Executed, provenance incomplete | A funded immutable lifecycle, seven rejected attacks, checksums, live RPC/indexer reports, and a passing local CI record are saved; GitHub CI is missing |
| Ownership provenance | Fixed in current data path | Owner lock and change history are preserved and verified |
| Audited-revision reproducibility | Partial | The deployment manifest links the binary to a source-bound review candidate, and local CI rebuilt the exact deployed hashes | Add GitHub CI evidence and an independent review attesting the same binary SHA-256 and CKB data hash |

No security finding is hidden. The contract remains unaudited. The Flask API's
rate limiter is process-local and therefore only suitable for the documented
single-worker deployment. The supported CKB JavaScript dependency chain has a
documented low-severity upstream advisory.

## Verification results

- Python: 199 passed with `python -m pytest`.
- Registry contract: 16 tests passed.
- TypeScript SDK: 72 tests passed.
- Cross-language conformance: 57 cases, 171 assertions, zero failures.
- Historical offline evidence verifier: passed all checks.
- Frontend type check: passed.
- Frontend: 22 unit/contract tests, type check, and a Node 22 production build
  passed and generated all 17 routes.
- Browser: the current Playwright suite defines 12 checks covering the Registry
  landing route, MLAT investigation and recovery paths, map degradation,
  accessibility, mobile layout, assets, and security headers. A clean run of
  this expanded suite is still required. The older nine-check suite covered the
  secondary MLAT reference navigation, the aircraft-receiver return path,
  production assets, mobile width, security headers, and WCAG scans. The
  source-bound review bundle at commit `4fc8fce` records all 9 as passing with
  0 serious or critical accessibility findings. That report does not certify
  later frontend commits.
- Fresh immutable lifecycle: 50 bundled files, local CI, and 100 live-chain
  checks passed. The lifecycle-bundle verifier now fails closed only because
  its GitHub CI record is missing. The stable release gate separately requires
  a final manifest and tag, independent review, and a healthy public deployment.

## Recruitment status

- Leads: 13
- Contacted: 0
- Permission requested: 0
- Invited: 0
- Interested: 0
- Confirmed: 0
- Scheduled: 0
- Pilot run: 0
- Interviewed: 0
- Follow-up: 0
- Potential clients or partners: 0

## Known limitations

- CKB proves authorized lifecycle state, not hardware, coordinates, custody,
  timing, stream honesty, or participant truthfulness.
- MLAT replay proves software integration, not live localization accuracy.
- A real MLAT solve needs at least four physically synchronized receivers.
- The current deployment topology is single-node and uses SQLite.
- A wallet-signed browser lifecycle has not been rehearsed on the hardened code.

## Next actions

1. Freeze and commit the remaining frontend source, then run the expanded
   browser suite from that clean commit.
2. Obtain independent review attesting the deployed binary SHA-256 and CKB data hash.
3. Repeat live verification at release time using normal TLS verification.
4. Generate a new source-bound review bundle for the final canonical commit and
   preserve its browser report in CI.
5. Complete the funded CCC wallet acceptance lifecycle in the browser.
6. Deploy a complete pilot environment.
7. Send permission requests and direct invitations from the maintainer's named
   public account, then update the tracker with actual responses.
