# Release blocker follow-up evidence

Candidate: `57a0c7f17fd0a1cac8681ed860c5cfb1aafcecfa` on local branch
`readiness/external-testing-2026-10-19`. This package supplements, and does not
replace, the original readiness evidence. See
[the resolution report](../../docs/production-readiness/blocker-resolution-2026-10-19.md).

Confirmed results:

- Clean committed source, verified source archive and complete Git bundle.
- 294 Python, 78 SDK, 60 frontend unit and 16 contract tests passed; 57 shared
  conformance cases / 171 assertions agree. Exact deployed contract bytes reproduced.
- Final clean browser reports: 31 synthetic and 3 historical tests, zero failed,
  `worktree_clean=true`, `pass=true`, both naming the final candidate commit.
- Both final Docker images built. The actual synthetic pipeline, non-root API,
  restart persistence, private control socket, backup/restore, restored API,
  frontend proxy and graceful shutdown passed in the local Linux VM.
- RustSec scan completed; zero vulnerability-category entries but seven warnings
  remain, scoped outside the deployed contract target's normal/build dependency
  graph. This is not an independent review or unconditional security approval.

`commands.json` records exact arguments, directories, start times, exit codes and
active elapsed time. Host suspension caused large UTC gaps in one browser run;
its failed report is retained, and the unchanged retry inhibited idle sleep.
Do not infer a production latency claim from command duration on this host.

`container-runtime-failure-report.json` preserves the first runtime failure.
It led to a Dockerfile home-directory fix and ephemeral-port rediscovery in the
test harness. `container-runtime-final-report.json` records the actual passing
checks and image IDs. This is same-image restore in a local VM, not a production
version rollback or recovery on an unspecified target host.

The initial backend dependency download and Rust advisory clone timed out.
Their failed attempts are retained. The initial isolated Cargo cache could not
check withdrawn crates; `rust-advisories-complete.json` is the completed scan
using a populated index. No advisories were ignored and no contract dependencies
were changed to obtain the result.

`manifest.json` binds the local archive and Git bundle. The larger files remain
at the listed `artifacts/blockers-2026-10-19/` paths. The candidate worktree stays
clean; these follow-up evidence files are outside that source snapshot.

Still pending: explicit public branch-export approval and public CI; the intended
staging host/operational owner and previous compatible deployment; an independent
reviewer; authorized wallet signing/spending; real receiver/clock/location evidence
and an independent reference window. No public push, deployment, wallet transaction,
reviewer contact or physical receiver campaign was performed.

The temporary VM was stopped after validation. Disposable test resources were
removed; images and VM disk remain locally for reproduction. The user's concurrent
main-worktree documentation deletions were recorded without being overwritten.

Verify this package with `shasum -a 256 -c checksums.sha256` from this directory.
Checksum integrity does not imply production readiness. Gates B and C remain unpassed.
