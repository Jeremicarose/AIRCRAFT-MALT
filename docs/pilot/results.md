# Live Pilot Status

Status date: 2026-09-09

## Product readiness

- Registry: current source and SDK pass lifecycle and conformance tests. The
  historical testnet deployment is read-only because its code binding is mutable.
- MLAT: replay workflow is implemented. Live field validation with four
  physically synchronized receivers has not happened.
- Security: code-level P0 feed binding and refresh propagation fixes pass. H-01
  still requires an independently reviewed immutable testnet deployment.
- UI: production build passes. Live Map is the first screen and Registry versus
  replay provenance is visible. A funded browser lifecycle has not run.
- Deployment: local/reference deployment only. No complete public frontend URL
  has been verified.
- Known blockers: immutable testnet deployment, funded wallet rehearsal,
  independent contract review, clean-checkout acceptance test, hosted frontend,
  and real participants.

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

- Obtain independent review of the current contract candidate.
- Deploy it on CKB testnet with `hash_type=data1` and publish source-bound evidence.
- Configure the browser SDK and MLAT runtime to that deployment.
- Complete a funded browser create, update, transfer, history, and revoke rehearsal.

### P1

- Run the clean external-user installation and recovery plan.
- Verify the updated desktop and mobile flow in a production browser.
- Deploy a complete shareable frontend, API, and processor environment.

### P2

- Generate an immutable evidence bundle for the final pilot commit.
- Add automated browser accessibility and end-to-end regression coverage.
- Recheck the remaining low-severity upstream npm advisory before deployment.

## Commercial or partnership opportunities

- Confirmed opportunity: none
- Promising lead: none
- Speculative opportunity: the 13 public research leads in the tracker, with no
  interest or product-fit evidence yet

## Final conclusion

`NOT READY`

The software preparation has advanced, but the defined pilot requires real
wallet lifecycle tasks against an immutable deployment and real external users.
Neither condition exists yet, so the pilot is not running, completed, validated,
or producing traction.
