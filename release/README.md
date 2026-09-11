# Stable Release Gate

`release.example.json` documents the stable-release evidence contract. Copy it
to `release/release.json`, replace every placeholder with committed evidence,
and commit that manifest with the release candidate.

Repository checks run during normal CI:

```bash
python tools/check_release_readiness.py --profile repository
```

Stable tags run the fail-closed gate and re-query the public deployment and CKB
evidence:

```bash
python tools/check_release_readiness.py \
  --profile stable \
  --manifest release/release.json \
  --release-ref vX.Y.Z \
  --live
```

The security-review attestation must be JSON with these fields:

```json
{
  "schema_version": 1,
  "independent": true,
  "reviewer": "Named reviewer or organization",
  "source_commit": "40 lowercase hexadecimal characters",
  "contract_binary_sha256": "64 lowercase hexadecimal characters",
  "contract_binary_ckb_data_hash": "0x followed by 64 lowercase hexadecimal characters",
  "conclusion": "pass_with_findings",
  "unresolved_critical_findings": 0,
  "unresolved_high_findings": 0,
  "report_path": "evidence/registry-v2-security-review/report.pdf",
  "report_sha256": "64 lowercase hexadecimal characters",
  "report_url": "https://public-review.example/report",
  "signature_or_account_url": "https://public-review.example/reviewer"
}
```

The checker also confirms that contract, protocol-client, and conformance paths
have not changed since `source_commit`. An audit declaration without the report,
matching hash, public reviewer identity, and unchanged reviewed code does not
open the gate. The attested contract binary hashes must also match the exact
`data1` binary recorded by the signed lifecycle bundle.

Generate the browser report from a clean committed tree after building the
frontend. The Playwright reporter writes `tmp/browser-qa-report.json` by
default, or the path supplied through `BROWSER_QA_REPORT`. The stable gate
requires schema version 1, the primary Registry route, a clean source revision, no
fewer than nine completed and passing browser tests, no failed browser tests,
and no serious or critical WCAG A/AA axe findings. A run that fails before test
execution cannot produce passing release evidence.
