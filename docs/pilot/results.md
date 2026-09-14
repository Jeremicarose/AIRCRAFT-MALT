# Live Pilot Status

Status date: 2026-09-14

## Product readiness

- Registry: current source and SDK pass lifecycle and conformance tests. The
  historical testnet deployment is read-only because its code binding is mutable.
- MLAT: replay workflow is implemented. Live field validation with four
  physically synchronized receivers has not happened.
- Security: code-level P0 feed binding and refresh propagation fixes pass. H-01
  now has immutable `data1` testnet lifecycle evidence, but the exact deployed
  binary still requires independent review and GitHub CI provenance.
- UI: the Receiver Registry is the first operational screen. MLAT tools are
  grouped under a secondary `MLAT reference` area, and Registry versus replay
  provenance is visible. Registry identity and lifecycle history remain
  available through receiver drill-down. Nine production browser checks passed
  on the clean source commit, but no browser-wallet lifecycle has run.
- Deployment: an immutable Pudge contract lifecycle is saved and verifies
  offline, through saved RPC/indexer reports, and through a fresh public-RPC
  recheck with passing local CI provenance. GitHub CI is missing, and no
  complete public frontend URL has been verified.
- Known blockers: GitHub evidence CI, funded browser-wallet rehearsal,
  independent review, public frontend, and real participants.

## Recruitment

- Leads: 13
- Contacted: 0
- Interested: 0
- Confirmed: 0
- Completed: 0

## Pilot results

- Participants: 0
- Successful participant workflows: none
- Failed participant workflows: none
- Critical usability problems from participants: no evidence yet
- Technical problems during participant sessions: no evidence yet

Maintainer browser QA found and resolved one pre-pilot functional issue: replay
aircraft contribution IDs were not resolving to receiver buttons. The corrected
Live Map now lists all four replay contributors and opens a receiver inspector.
This is maintainer evidence, not participant evidence.

## User evidence

- Most common problem: unknown
- Current workaround: unknown
- Value demonstrated to external users: none
- Main objections: unknown
- Adoption blockers from users: unknown

Repository research and maintainer testing are not user evidence.

## Potential clients or partners

No person or organization currently meets the qualification rule. The researched
organizations and public contributors are speculative leads only. None has been
contacted or expressed interest.

## Product changes required

### P0

- Obtain independent review of the exact deployed contract binary.
- Publish GitHub CI provenance for the existing `data1` lifecycle and a public
  CI result for the final source revision.
- Verify that the final hosted browser build and MLAT runtime both use the
  pinned immutable deployment values.
- Complete a funded browser create, update, transfer, history, and revoke rehearsal.

### P1

- Run the clean external-user installation and recovery plan.
- Repeat the passing desktop and mobile flow on the final canonical commit.
- Deploy a complete shareable frontend, API, and processor environment.

### P2

- Generate clean source-bound evidence for the final pilot commit.
- Run the automated browser accessibility and end-to-end suite in clean CI.
- Recheck the remaining low-severity upstream npm advisory before deployment.

## Commercial or partnership opportunities

- Confirmed opportunity: none
- Promising lead: none
- Speculative opportunity: the 13 public research leads in the tracker, with no
  interest or product-fit evidence yet

## Final conclusion

`NOT READY`

The immutable contract lifecycle now exists, but the defined pilot still
requires a funded browser-wallet rehearsal, clean source-bound CI evidence, and
real external users. Those conditions do not exist yet, so the pilot is not
running, completed, validated, or producing traction.
