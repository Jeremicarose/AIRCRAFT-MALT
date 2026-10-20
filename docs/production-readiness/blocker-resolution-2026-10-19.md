# Follow-up: the three release blockers

Final local candidate: **`57a0c7f17fd0a1cac8681ed860c5cfb1aafcecfa`**.
Local source, browser, container and restore validation is complete. The three
broader blockers are **not all complete**: public CI needs explicit publication
approval; target-host operations, independent review, wallet signing and physical
receiver evidence still need operator inputs. No evidence is fabricated to close them.

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

## Verified candidate results

The first candidate was committed as `ad3051abb3f95c18bfcd158f513474c3400128e5` on
`readiness/external-testing-2026-10-19`. The user's main working tree is separate.
The archive SHA-256 is
`8dd8a8c5d4700cd9dbb447ec8782ff80fd83558c4db7657119a155d447ec216c`;
the copy inside the local VM matches that hash.

- Locked SDK/frontend installs, frontend production build and unit suites pass.
- Python: 294 tests; SDK: 78; frontend unit: 60; contract: 16, all passed.
- Both browser reports now have `worktree_clean=true` and `pass=true`: 31
  synthetic checks and 3 historical checks, bound to the exact candidate commit.
- The clean contract rebuild exactly matches deployed SHA-256
  `087a8b19ca99170d8d1e8c018b749259ce067ad3cb1cc8cef3b4a490ccae0465`.
- All 57 shared protocol cases / 171 assertions agree. The new v4 deterministic
  bundle regenerates identically, with prior bundles preserved.
- A common-pattern candidate secret scan found no matches in 819 text files;
  repository hygiene checks also pass. This is not an independent security audit.

Public CI is still blocked: automatic approval review rejected exporting the
candidate and evidence to the public GitHub branch without explicit permission.
The approval question identifies the commit and public destination. No push was
performed, and no alternate publication route was attempted.

Six documentation deletions appeared in the main worktree during validation,
outside this task's changes. They are recorded in `concurrent-main-deletions.json`.
The committed candidate retains its earlier reviewed snapshot; these concurrent
edits have not been restored, overwritten or silently incorporated.

## Final packaging and container results

Actual container execution exposed two issues missed by source-only checks:

- Gunicorn 26 attempted to create its control socket under `/home/mlat`, but the
  non-root image user had no writable home. The image now creates a private home
  with mode 0700. A new container check rejects the former control-server error.
- Docker reassigned an ephemeral host port on restart (32770 → 32771 in a
  controlled reproduction). The restarted API was healthy; the test still polled
  its old port. The harness now rediscovers that port before asserting recovery.

The fixes are committed in `57a0c7f`. Application, solver, contract, SDK and frontend
sources are unchanged from `ad3051a`. Because the Dockerfile is part of the
deterministic source bundle, a new **v5** benchmark package was created and verified;
v4 and earlier packages remain unchanged. CI/release packaging points to v5.

Both final images built from the checksum-verified archive in an isolated Linux VM:

| Image | Docker image ID |
| --- | --- |
| Backend | `sha256:4a1341f6adc67278ed11b100633860cd234a46ee776077cc9bb96e6cd349925d` |
| Frontend | `sha256:98025c0fdc1708a69c5cc376bae825a4f055b642f0b51d3b391678830471c537` |

The final container report is **PASS** for non-root UID 10001, bundled solver
evidence, actual synthetic processor → solver → SQLite → API, persisted IDs after
restart, clean control-socket startup, backup/restore into a new database and its
API, frontend proxy, and graceful API shutdown. Test containers/networks/volumes
were removed by the harness. This is local same-image recovery, not recovery on
an unspecified production host or rollback to an approved earlier production image.
The isolated VM was stopped after the passing run; its images remain available
locally. The final historical browser report also passes all three checks on
`57a0c7f` with a clean worktree.

The initial backend build timed out downloading NumPy; retrying the same recipe
and hashes passed. The initial container runtime failure is retained. The final
synthetic browser retry passed all 31 tests, bound to `57a0c7f` with
`worktree_clean=true` and `pass=true`. The preceding run failed four tests while
logs contained 942-second and 7,267-second gaps. Host suspension is suspected;
idle sleep was inhibited for the passing retry. No assertions were weakened.

## Rust dependency scan

The missing Rust scan was completed using checksum-verified cargo-audit 0.22.2
and RustSec snapshot `999ec89d5d3f10f20be14750ec8c2d8b44e0ac9b`
(17 October 2026). The full-history network fetch first failed; a fresh anonymous
shallow checkout succeeded. The initial isolated-cache scan could not check withdrawn
crates; the scan was repeated with the populated local crate index.

The scanner exited 0 with **zero vulnerability-category entries**, but reported:

| Category | Package | Finding |
| --- | --- | --- |
| Unmaintained | atomic-polyfill 1.0.3 | RUSTSEC-2023-0089 |
| Unmaintained | paste 1.0.15 | RUSTSEC-2024-0436 |
| Unsoundness | faster-hex 0.6.1 | RUSTSEC-2026-0306 |
| Unsoundness | lru 0.7.8 | RUSTSEC-2026-0253 |
| Unsoundness | memmap2 0.5.10 | RUSTSEC-2026-0186 |
| Unsoundness | rand 0.7.3 | RUSTSEC-2026-0097 |
| Withdrawn release | spin 0.9.8 | Crates.io yanked-package warning |

All seven are absent from the contract target's normal/build dependency graph
(`cargo tree --locked --target riscv64imac-unknown-none-elf --edges normal,build`).
They remain test-tooling/dependency-maintenance review items. No advisory was
suppressed, no contract dependency changed, and no independent approval is inferred.

## Handoff artifacts and remaining decisions

Local source archive: `artifacts/blockers-2026-10-19/candidate-57a0c7f.tar.gz`.
SHA-256: `8bede2f7dc5e2c4ba0b5a44d8c6470081a9d3fa27fc672ec826cb6b933e6df70`.
The Git bundle `candidate-57a0c7f.bundle` contains the branch and complete history
and passed `git bundle verify`. Neither artifact has been published.

1. Approve the public candidate branch export if GitHub CI is desired. Automatic
   approval review blocked publication of the source/documentation/evidence payload;
   no alternate route was used. The final candidate adds only the documented
   packaging/harness/v5-evidence changes beyond the earlier approval question.
2. Identify the staging host/operational owner and prior compatible image/database
   for target-host restore/rollback, TLS, alert and retention verification.
3. Appoint the independent reviewer and provide their actual signed/account-bound
   report; confirm the operator-managed wallet rehearsal and spending authorization.
4. Supply local paths to authorized receiver/clock configuration, calibration
   evidence and independent reference data. Never send private keys or private feed URLs.

Until these inputs arrive, external/production gates remain unpassed. The
review brief and operator runbook are executable preparation, not substitute results.

The final [evidence package](../../evidence/production-readiness-blockers-2026-10-19/README.md)
contains exact command records, both failed and passing reports, scanner findings,
source bindings and image identifiers. Earlier evidence remains untouched.
