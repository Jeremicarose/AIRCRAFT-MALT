# Pilot Readiness

Status date: 2026-09-09
Overall status: `NOT READY`

## What happened

The repository now passes its contract, Python, TypeScript SDK, schema
conformance, and frontend compilation checks. Security tests also confirm that
MLAT refreshes Registry state while running, rejects identity mismatch, rejects
ambiguous shared WebSocket identities, and fails closed when discovery becomes
incomplete.

The only deployed Registry V2 evidence is tied to an older contract whose
`hash_type=type` binding permits the implementation cell to change under the
same script hash. It is preserved as historical evidence and marked read-only.
The current hardened contract source has not been independently reviewed or
deployed with an immutable `data1` code hash.

## Readiness by area

| Area | Status | Evidence | Required next action |
|---|---|---|---|
| Registry source | Prepared | 5 Rust host and 11 CKB-VM tests pass | Independent review |
| Registry deployment | Blocked | Historical evidence verifies but is mutable and read-only | Deploy reviewed binary with `data1` |
| Python discovery | Prepared | Pagination, duplicate, schema, and binding tests pass | Exercise new testnet deployment |
| TypeScript SDK | Prepared | 69 SDK tests pass | Configure immutable deployment and run funded browser lifecycle |
| MLAT replay | Prepared | Python integration suite passes | Keep replay labels visible |
| MLAT live field use | Blocked | Harness exists; no synchronized physical run | Obtain four qualified receiver feeds |
| UI | Prepared locally | Type check and production build pass | Complete updated browser and wallet checks |
| Public deployment | Blocked | No verified complete hosted URL | Deploy frontend, API, and processor |
| Recruitment | Prepared, not executed | 13 public leads; messages and tracker exist | Send authorized permission requests and invitations |
| Pilot | Not started | 0 contacted, 0 confirmed, 0 completed | Clear P0 gates before inviting |

## Security status

| Finding | Status | Meaning |
|---|---|---|
| H-01 mutable contract implementation | Blocked safely | Strict live mode rejects `type`; a new `data1` deployment is still required |
| H-02 runtime Registry changes | Fixed in code | Successful refresh applies removal and owner changes; failed refresh removes Registry receivers |
| H-03 feed impersonation | Fixed for supported paths | Bound identity mismatch is rejected; shared WebSocket identity is rejected; local Beast bridge uses endpoint configuration |
| M-01 self-declared `updated_at` authority | Fixed | Capacity selection uses canonical identity ordering, not record time |
| M-02 pagination completeness | Fixed | Empty terminal page is required; missing, repeated, or excessive cursors fail closed |
| M-03 independent evidence derivation | Fixed for saved evidence | Verifier recalculates transaction hashes, Type ID, spend chain, locks, records, and binary hashes |
| M-04 V2 schema mismatch | Fixed in current source | Rust, Python, and TypeScript share corpus version 2 and pass 171 assertions |
| `u64` precision | Fixed | Python bounds and TypeScript `bigint` preserve exact values |
| Testnet evidence generation | Tested locally | Tool tests pass; no new funded testnet execution occurred |
| Ownership provenance | Fixed in current data path | Owner lock and change history are preserved and verified |
| Audited-revision reproducibility | Partial | Source-bound generation and verification are implemented; the final bundle must be regenerated after the latest source fixes | A fresh deployment bundle still requires external signing |

No security finding is hidden. The contract remains unaudited, the Flask API has
no built-in rate limiter, and the supported CKB JavaScript dependency chain has
a documented low-severity upstream advisory.

## Verification results

- Python: 166 passed with `python -m pytest` and direct `pytest`.
- Registry contract: 16 tests passed.
- TypeScript SDK: 69 tests passed.
- Cross-language conformance: 57 cases, 171 assertions, zero failures.
- Historical offline evidence verifier: passed all checks.
- Frontend type check: passed.
- Frontend production build before final browser pass: passed.

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

1. Freeze the current contract candidate and obtain independent review.
2. Deploy the reviewed binary to CKB testnet with `hash_type=data1`.
3. Generate and verify a source-bound deployment and lifecycle evidence bundle.
4. Configure the SDK, backend, and UI to the immutable deployment.
5. Run the clean-checkout and funded browser acceptance test.
6. Deploy a complete pilot environment.
7. Send permission requests and direct invitations from the maintainer's named
   public account, then update the tracker with actual responses.
