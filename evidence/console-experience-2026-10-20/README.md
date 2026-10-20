# Console experience — final verification, 20 October 2026

The console now keeps its navigation frame mounted between pages and offers six
optional learning missions with 300 XP, badges, levels, pause and reset. Open
**Explorer missions** at `/app/guide` after starting the frontend. The existing
[tester guide](../../docs/production-readiness/external-tester-guide.md) describes
synthetic and historical startup. The replay mission requires historical mode;
the source lesson remains usable when runtime APIs are unavailable.

[The change report](../../docs/production-readiness/console-experience-2026-10-20.md)
explains the behavior and design limits. Progress is browser-local learning data.
It does not change registry state, receiver qualification, solver results or release
gates. Reset clears only mission progress; pause stops new awards. No wallet or
transaction is required for a mission.

## Source and reproducibility

The final local branch is `readiness/explorer-2026-10-20`, commit
`7aa4a178c589eff3d9829d127d27300c66def4bc`. The isolated candidate worktree is clean.
All 130 tracked frontend files match the user's working copy. Existing unrelated
changes were preserved, and no previously present source file was removed.

The source archive is
`artifacts/experience-2026-10-20/candidate-7aa4a17.tar.gz`.
Its SHA-256 is
`ed8a5033e67348a1a40faf921ad0e47577836af1475a5ee8a7ae81094260c5ea`.
The archive was verified inside the Linux VM before extraction/build.
[final-candidate.json](final-candidate.json) records source hashes and comparisons.

The 38-test synthetic browser run names commit `3b19c3f`; the four historical
checks name final commit `7aa4a17`. Their only difference is the historical test's
selectors being scoped to the main workspace. Application code and synthetic
tests are identical. The production application build and 63-unit suite used
`bd9ba58`; later commits change only browser-test selectors. The final Linux image
was built from `7aa4a17`, including its own successful TypeScript check. No result
is relabelled as having run against a different commit.

Backend, SDK, contracts and benchmark fixtures are unchanged from the earlier
[57a0c7f readiness candidate](../production-readiness-blockers-2026-10-19/README.md).
Its 294 Python, 78 SDK and 16 contract checks and v5 benchmark evidence remain
applicable to those unchanged components; they were not rerun in this UI phase.

## Executed checks

[commands.json](commands.json) contains all 56 recorded check invocations, exact
arguments, working directories, environment choices, exit codes and elapsed time,
including failed attempts. Node was 22.23.1; browser services used the pinned
Python 3.12 environment and `MLAT_ENV_FILE=/dev/null`.

| Command or check | Final result |
| --- | --- |
| `npm test` | 63 passed, 0 failed |
| `npm run typecheck` | Exit 0; this is also the configured `lint` script |
| `npm run build` | Candidate and working copy both exit 0 |
| `npm run test:e2e:prepared` | 38 passed, 0 failed |
| `npm run test:e2e:replay` | 4 passed, 0 failed |
| `python tools/check_release_readiness.py --profile repository` | Exit 0 |
| `python tools/check_documentation.py` | Exit 0 |
| `git diff --check` in the candidate | Exit 0 |
| `docker build --file reference/mlat/frontend/Dockerfile --tag mlat-frontend:explorer-7aa4a17 .` | Exit 0 |
| Container pipeline, restart, backup/restore, frontend proxy and shutdown | PASS |
| Container `/app/guide` server rendering and 26 static assets | PASS |

The synthetic browser suite uses synthetic MLAT data **and public CKB read-only
discovery**. It is not fully offline. One run encountered an indexer outage; the
application excluded unavailable receivers and showed the failure. The unchanged
targeted retry and complete subsequent run passed. This is not wallet lifecycle
or physical receiver evidence.

The browser checks cover stable frame identity during navigation/back/forward,
slow loading, API failure, keyboard use, mobile overflow, reduced motion, accessible
controls, correct/incorrect quiz answers, pause/reset, duplicate awards, blocked
storage, failed/successful diagnostic exports, and historical qualification.
Automated accessibility checks found no violations under their configured rules;
they do not replace human accessibility review.

[Failure notes](failure-notes.md) explain the actual modal-panel, saved-evidence
recovery and hydration fixes, the test-selector corrections, and execution failures.
The unit runner's existing experimental TypeScript warning and browser tooling's
color warning remain visible in logs. The earlier seven Rust test-tooling warnings
remain documented in the prior readiness package; no dependency was changed here.

The small [navigation comparison](navigation-measurements.json) preserved the new
sidebar across all five transitions; the prior sidebar was replaced in all five.
Heading feedback was approximately 97–231 ms versus 498–846 ms in that local
sample. This measures visible navigation feedback, not complete data arrival or
production throughput. The sample predates the final cache isolation correction
and is not a production latency guarantee.

## Container and cleanup evidence

[container-runtime-report.json](container-runtime-report.json) identifies the actual
images and checks. The frontend image ID is
`sha256:34fadb00c7e909df50a0b723b6a511bd700e5154698cca728880c97955fa4a46`;
the reused backend image is the previously verified `mlat-system:readiness-57a0c7f`.
[check_container_guide.py](check_container_guide.py) extends the unchanged committed
container check with the new page/asset assertions. It ran with:

```sh
python3 check_container_guide.py \
  --backend-image mlat-system:readiness-57a0c7f \
  --frontend-image mlat-frontend:explorer-7aa4a17 \
  --output /tmp/mlat-explorer-container-runtime.json
```

Run that wrapper from the checkout root after building the images. The exact local
Lima invocation is in the command inventory. The checks use disposable synthetic
data, non-root containers and loopback ports. The harness removed its containers,
network and volume. Review browsers/services were closed and the VM was stopped.
The local VM disk/images remain available for reproduction. Same-image restore
passed; target-host deployment and rollback to an approved earlier production
image have not been verified by this check.

## Release gates and remaining work

| Gate | Outcome |
| --- | --- |
| A — Internal validation | Local validation passes, with the public-indexer dependency and earlier test failures explicitly recorded. |
| B — Controlled external testing | Not passed: public CI/publication approval, independent review and authorized operator testnet acceptance remain pending. |
| C — Production consideration | Not passed: real receiver/clock/reference evidence and target-host operations remain unverified. |

The three highest-priority remaining work groups are:

1. Approve the intended public export/CI path and obtain independent review plus an
   authorized operator-managed wallet lifecycle rehearsal. No private keys are needed.
2. Supply authorized multi-receiver observations, clock/location evidence and an
   independent reference window for the live acceptance campaign.
3. Identify the staging host and operational owner, then verify TLS, monitoring,
   retention, backup/restore, incident response and deployment rollback there.

The earlier public push was rejected by automatic approval review because explicit
publication approval was missing. No public push, image publication, wallet
transaction, operator contact or real deployment was performed in this phase.
The [existing operator runbook](../../docs/production-readiness/operator-acceptance-runbook.md)
and [independent review brief](../../docs/production-readiness/independent-review-brief.md)
remain the next executable steps when the required inputs are supplied.

Verify this package from its directory with `shasum -a 256 -c checksums.sha256`.
Integrity of this evidence does not establish production readiness.
