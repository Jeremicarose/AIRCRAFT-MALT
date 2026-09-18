# Registry V2 Review Evidence

This bundle is bound to source commit `e99ea8d55403254e2b31bcc128baaf45cf26b325` and Git tree `e50bd667852a4e9a30e6638840fa3867cd421199`. All recorded checks passed.

The included contract binary matches the immutable `data1` Pudge deployment and its signed CKB CLI lifecycle evidence. The July mutable deployment is retained separately for historical comparison. No private key is included. The browser QA report is bound to the same clean source tree. A browser/TypeScript-SDK signed lifecycle and independent security review remain external steps.

Verify this bundle from the repository with:

```bash
python tools/registry/verify_registry_v2_review_evidence.py --bundle /Users/jeremicarose/Downloads/mlat-system 2/evidence/registry-v2-review-2026-09-18-final
```
