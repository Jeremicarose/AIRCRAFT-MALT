# MLAT Reference Evidence

`reproducible-benchmark-v2` is the authoritative deterministic regression
package. `reproducible-benchmark-v1` is retained unchanged as historical
evidence. `experimental` contains historical local simulation measurements.
`ui-review-2026-08-05` is validation-only presentation evidence from a dirty
worktree; it does not support solver, live-operation, or accessibility claims.

No synchronized physical receiver benchmark is currently published.

When a physical run is available, capture it with
`tools/mlat/capture_grant_evidence.py` and verify it with
`tools/mlat/verify_live_evidence.py`. A valid V2 bundle contains raw timed
observations and supports offline re-solving; screenshots alone are not MLAT
evidence.
