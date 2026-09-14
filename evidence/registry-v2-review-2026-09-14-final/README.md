# Registry V2 Review Evidence

This bundle is bound to source commit `4fc8fce48a86cd0dbfab70c4910580eac2c61730` and Git tree `3facd3f14a2d1224432c5b99c0fce5abeabd082f`. All recorded checks passed.

The included contract binary matches the immutable `data1` Pudge deployment and its signed CKB CLI lifecycle evidence. The July mutable deployment is retained separately for historical comparison. No private key is included. The browser QA report is bound to the same clean source tree. A browser/TypeScript-SDK signed lifecycle and independent security review remain external steps.

Verify this bundle from the repository with:

```bash
python tools/registry/verify_registry_v2_review_evidence.py --bundle artifacts/registry-v2-review-final-4fc8fce
```
