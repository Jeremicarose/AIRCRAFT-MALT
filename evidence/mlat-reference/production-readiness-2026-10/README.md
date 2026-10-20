# Local production-readiness validation evidence

Audit work began 8 October 2026; the session resumed 13 October.
This package records local checks, read-only public CKB probes, and explicitly
synthetic performance measurements. It is not physical field evidence, a signed
release, an independent security audit or a successful remote deployment.

- `validation.json`: final executed checks and their limits.
- `pipeline-envelope.json`: nine synthetic in-process load scenarios, including
  actual achieved rates, failures, CPU, peak process memory and stage latency.
- `correlation-before.json` / `correlation-after.json`: the same 2,000-observation
  buffer experiment before and after batched cleanup.
- `ckb-rpc.json`: immutable code-cell existence and hash check, with TLS verified.
- `ckb-indexer.json`: public paginated Registry results. Live cells do not prove
  physical receiver existence or participation.
- `python-dependencies.json` / `frontend-dependencies.json`: vulnerability scan
  results at their recorded check time; they are not a future security guarantee.
- `api-startup.json`: installed API startup, health and graceful shutdown.
- `registry-conformance.json`: 57 cases shared across Rust, Python and TypeScript.
- `solver-typing-equivalence.json`: executable AST comparison for the typing-only solver edits.
- `browser-qa-*.json`: local test outcomes; release pass remains false while the worktree is uncommitted.
- `manual-review.md` and `screenshots/`: browser review of the actual application.
- `checksums.sha256`: checksums of the evidence files.

The older signed Registry bundles and numerical benchmark packages were retained.
The workspace contained pre-existing uncommitted work; this package must not be
represented as CI evidence bound to a newly committed release.
