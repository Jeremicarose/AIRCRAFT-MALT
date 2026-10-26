# Independent review brief

Status: **AWAITING INDEPENDENT REVIEWER**. This is a request/brief, not an audit
attestation. The maintainer must appoint the reviewer; no request has been sent.

## Review subject

Use the committed candidate on `readiness/external-testing-2026-10-19` and its
source archive/hash manifest. Review the full accumulated working-tree change,
not only the last security patches. Record the exact commit and contract hashes.
The deployed immutable testnet code hash is
`0x40ebcd7df892234592a97c987faadce70df6bcfb5f7fa24fa78431cc24f3d6fa`.
Its saved binary SHA-256 is
`087a8b19ca99170d8d1e8c018b749259ce067ad3cb1cc8cef3b4a490ccae0465`.
Verify both independently from the saved deployment and a fresh build using the
documented deployment toolchain. No new contract deployment is proposed.

## Scope and testable questions

1. Contract: Type-ID creation, exact cell-group cardinality, input-lock ownership,
   sequence/label continuity, strict JSON, integer/record bounds, irreversible
   revocation and prohibition of burn/resurrection. Verify actual CKB-VM behavior.
2. SDK/Python: schema agreement, fresh node verification rather than indexer-only
   authority, duplicate quarantine, complete pagination, deadlines, error handling,
   owner transfer and spent-cell rejection before wallet preparation.
3. Feed/runtime: connection-bound identities, endpoint/credential separation,
   untrusted clock/geometry claims, malformed data and resource bounds, current
   receiver eligibility, pending observation removal after revocation, replay isolation.
4. API/storage: administrative authorization, public disclosure policy, continued
   streaming access after revocation, limiter/connection scope, secret handling,
   provenance migrations, duplicate writes and recovery.
5. Deployment/evidence: container permissions, copied assets, package reproducibility,
   actual source bindings, uncalibrated solver quality, missing physical evidence
   and operational gaps. Do not infer correctness from a passing test count alone.

Use the [threat model](security-threat-model.md), [test plan](test-plan.md), ADRs,
contract README, current source and actual results. The old audit is evidence to
inspect, not an independent conclusion to endorse without checking.

## Reviewer deliverables

Provide a report with finding IDs, severity, affected source, reproduction, impact,
fix/mitigation verification and remaining limitations. Sign or publish its hash
through an independently verifiable reviewer account. The existing release gate
expects an attestation with these fields; populate them with real reviewed facts:

```json
{
  "schema_version": 1,
  "independent": false,
  "conclusion": "pending",
  "reviewer": "",
  "source_commit": "",
  "contract_binary_sha256": "",
  "contract_binary_ckb_data_hash": "",
  "report_path": "",
  "report_sha256": "",
  "report_url": "",
  "signature_or_account_url": "",
  "unresolved_critical_findings": null,
  "unresolved_high_findings": null
}
```

This intentionally cannot pass the release gate. Only the independent reviewer
may supply their identity, conclusion and reviewed counts. Save their actual
report/attestation under a new evidence directory and verify the hash and review
scope using `tools/check_release_readiness.py`. Do not create a release tag merely
to test that gate. Findings requiring a contract change need a new version and
separately approved deployment, not replacement of historical evidence.
