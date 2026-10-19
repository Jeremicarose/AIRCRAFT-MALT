# Follow-up: the three release blockers

This follow-up starts from the completed [19 October audit](audit.md). The earlier
evidence package is immutable. Results for this follow-up are stored separately
under `artifacts/blockers-2026-10-19/` and will be linked to a committed candidate.

## Scope and authorization

The user requested completion of the three blockers. Work therefore includes an
isolated release-candidate commit, clean source verification, local container
execution where possible, and concrete review/wallet/field-trial preparation.
The original prohibition on spending funds and deploying real infrastructure
still requires clarification for those specific operations. No reviewer or feed
operator is contacted automatically. No private keys or seed phrases are needed.

## Release and container evidence

Candidate branch: `readiness/external-testing-2026-10-19`, initially based on
`df82f6c`. Its worktree is `artifacts/blockers-2026-10-19/candidate`. Existing
working changes are preserved on the user's `main` worktree.

Two release-path failures were identified before the candidate was committed:

- The current benchmark runner and repository CI reference bundle v4, but only
  v2/v3 were present. The default verification command failed. A new v4 bundle
  was generated and verified; historical bundles were not rewritten.
- The release workflow installed the frontend before its local SDK and packaged
  the old v2 benchmark. It now installs the SDK first and packages v4.

The container check is being extended from a manually inserted persistence row
to an actual synthetic processor → SQLite → API → frontend run. It also performs
online backup, restore into a new file, restored API startup and graceful shutdown.
The report identifies same-image restore separately from application-version rollback.

Local virtualization support is present. Any temporary VM uses task-specific
storage and must not mount the user's home directory or wallet material.
The intended staging host is still required to establish target-host deployment,
TLS, incident ownership and rollback evidence.

## Independent review and wallet lifecycle

An independent review cannot be issued by the implementation author. The repository
currently names one maintainer and contains no independent attestation. See the
[review brief](independent-review-brief.md) for the exact deliverables and gate.
A local source review or additional scanner result will not be relabelled independent.

The operator-managed wallet rehearsal is described in
[the acceptance runbook](operator-acceptance-runbook.md). It uses the supported
CCC signer/browser path. The older CLI lifecycle runner accepts raw-key files and
is not selected for this task. Signing/funding remain pending operator direction.

## Physical receiver campaign and operations

No `receiver-clocks.local.json`, authorized multi-receiver source, or independent
reference window was supplied. These facts cannot be synthesized. The acceptance
runbook specifies the inputs, measured clock evidence, capture commands and failure
scenarios that will be executed once authorized inputs are available.

The live preflight had a verified environment-isolation defect: it read root `.env`
even when `MLAT_ENV_FILE=/dev/null` was selected. A failing regression reproduced
this; the preflight now respects the explicitly selected environment file, and the
targeted suite passes. This prevents a dry validation run from accidentally using
private live-feed configuration.

Statuses will be updated from executed evidence. Preparing a runbook or a request
for review does not satisfy the corresponding external gate.
