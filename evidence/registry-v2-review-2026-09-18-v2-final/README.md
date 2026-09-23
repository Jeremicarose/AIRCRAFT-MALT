# Registry V2 Review Evidence

This bundle is bound to source commit `e92a341e01c2637bfaf8e218f748c33bab81e0cf` and Git tree `adf6401c3d16f86e19979550437ed474e14b90f4`. All recorded checks passed.

The included contract binary matches the immutable `data1` Pudge deployment and its signed CKB CLI lifecycle evidence. The July mutable deployment is retained separately for historical comparison. No private key is included. The browser QA report is bound to the same clean source tree. `github-ci-provenance.json` records the successful public Repository CI run, browser job, and source-named artifacts for this commit. A browser/TypeScript-SDK signed lifecycle and independent security review remain external steps.

Verify this bundle from the repository with:

```bash
python tools/registry/verify_registry_v2_review_evidence.py --bundle evidence/registry-v2-review-2026-09-18-v2-final
```
