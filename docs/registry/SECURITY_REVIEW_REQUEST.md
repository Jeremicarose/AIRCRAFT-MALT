# Registry V2 External Security Review Request

## Review status

Independent review is requested and has not yet been completed. Do not describe
Registry V2 as audited until a named reviewer publishes a report or signs the
attestation at the end of this document.

The external review target is one exact, clean Git commit containing every path
listed under Review targets. Record that full commit SHA in the reviewer
attestation; do not infer the review target from the deployed contract alone.

The historical testnet deployment has separate, immutable provenance. Its
contract source is commit `61ab011de58397cb8d6ca3cecb5c659c69e2fc8c` and its
lifecycle tooling is commit `adbdbd1a5a2afebad4067649dc3af57a682e545a`, as
recorded in `evidence/registry-v2-testnet-2026-07-30-final/manifest.json`. The
current review tree may contain off-chain fixes that postdate that deployment;
those fixes do not change the deployed binary.

## Security objective

Registry V2 maintains one immutable Receiver Identity across authorized
metadata updates, ownership transfers, and permanent revocation. The identity
is the 32-byte type-script argument, not the human Receiver Label.

The contract must prevent:

- identity creation with forged Type ID arguments
- multiple live outputs in one identity group
- deletion of an identity without a revocation tombstone
- sequence rollback, reuse, or jumps
- mutation of the human Receiver Label
- resurrection or deletion after revocation
- state transitions without authorization by the current cell lock

## Intended transaction rules

| Group inputs | Group outputs | Required behavior |
|---:|---:|---|
| 0 | 1 | Type ID creation, sequence 0, non-revoked record |
| 1 | 1 | Immutable label, sequence +1, nondecreasing timestamp |
| 1 | 1 | Output lock may change to transfer ownership |
| 1 | 1 | Revocation creates a permanent tombstone |
| Any other cardinality | Any | Reject |

The previous input lock authorizes update, transfer, and revocation. The type
script validates lifecycle continuity; it does not replace CKB lock-script
verification.

## Review targets

- `contracts/registry-v2/src/entry.rs`
- `contracts/registry-v2/src/record.rs`
- `contracts/registry-v2/src/error.rs`
- `contracts/registry-v2/tests/lifecycle.rs`
- `src/ckb_registry/record.py`
- `src/ckb_registry/discovery.py`
- `tools/registry/registry_v2_testnet_lifecycle.py`
- `tools/registry/verify_registry_v2_evidence.py`
- `docs/adr/0001-receiver-identity-and-lifecycle.md`

## Questions for the reviewer

1. Can Type ID creation be bypassed through group layout, output ordering, or
   dependency manipulation?
2. Can an identity be duplicated, burned, or resurrected through a transaction
   shape not covered by the test suite?
3. Are JSON decoding, numeric handling, length limits, or unknown-field rules
   consensus-safe and denial-of-service resistant?
4. Does changing the output lock correctly model ownership transfer under CKB's
   transaction and script-group semantics?
5. Can sequence or label continuity be bypassed through malformed data or
   multiple script groups?
6. Is the permanent tombstone model worth its occupied-capacity cost, or should
   the lifecycle use a different terminal-state design?
7. Does off-chain discovery correctly distinguish the contract binary data hash,
   the deployed contract Type ID script hash, and each receiver identity arg?
8. Are there missing adversarial CKB-VM or public-testnet cases?

## Known limitations

- CKB proves transaction authorization and state transitions, not physical
  receiver existence, coordinates, clock synchronization, or stream honesty.
- Receiver Labels are immutable but not globally unique.
- Revocation leaves a live tombstone cell and therefore retains occupied CKB
  capacity.
- The first evidence deployment uses standard secp256k1 locks, not multisig or
  OmniLock.
- Testnet rejection evidence is node validation evidence, not a substitute for
  source review, formal verification, or a professional audit.

## Suggested review method

1. Build with the pinned toolchain and compare both published hashes.
2. Run the Rust invariant and signed secp256k1 CKB-VM tests.
3. Run `tools/registry/verify_registry_v2_evidence.py` locally and with `--live`.
4. Add at least one attack transaction or fuzz/property test not written by the
   project author.
5. Publish findings with severity, affected invariant, reproduction steps, and
   a proposed fix.

Before review begins, verify the supplied source tree is clean with
`git status --short` and confirm that the full `HEAD` SHA is the SHA recorded in
the attestation. The historical evidence directory must not be rewritten to
make it appear to have been produced from the newer review target.

## Reviewer attestation

```text
Reviewer name / organization:
Review date:
Source commit:
Evidence manifest SHA-256:
Review scope:
Tools and tests used:
Critical findings:
High findings:
Medium findings:
Low findings:
Residual risks:
Conclusion: pass / pass with findings / fail
Report URL:
Signature or verifiable account URL:
```
