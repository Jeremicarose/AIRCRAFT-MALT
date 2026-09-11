# Live Pilot Operations

This directory contains the working system for a real CKB Receiver Registry V2
and MLAT pilot. Preparation is not counted as execution. A session counts only
when a real external receiver operator, coordinator, or developer uses the
application and gives direct feedback.

## Pilot question

Does a persistent, owner-controlled, cross-network receiver identity provide
enough value over receiver-network-specific systems that receiver operators or
coordinators would use or integrate it?

The pilot must test the connected flow:

```text
Receiver -> Registry identity -> Discovery -> MLAT pool
         -> Observations -> Aircraft localization

Aircraft -> Contributing receivers -> Registry identity
         -> Current owner, status, and lifecycle history
```

## Current factual status

- Pilot state: `NOT READY`
- Public researched leads: 13
- Contacted: 0
- Interested: 0
- Confirmed: 0
- Completed: 0
- Participant evidence: none
- Qualified client or partner opportunities: none

The immutable Pudge `data1` deployment and a complete CKB CLI-signed lifecycle
now exist. The historical mutable type-hash deployment remains read-only. Before
external participants are asked to transact, the exact deployed binary still
needs independent review, the browser flow needs a funded CCC wallet rehearsal,
and clean source-bound CI evidence must be published.

## Working documents

- [Recruitment](recruitment.md): cohort, status rules, tracker, and outreach copy
- [Session guide](session-guide.md): 30 to 45 minute moderated session
- [Test plan](test-plan.md): product, security, and clean-user acceptance tests
- [Interview guide](interview-guide.md): neutral discovery questions
- [Participant template](participant-template.md): one privacy-safe session record
- [Results](results.md): current counts and final reporting structure
- [Lessons learned](lessons-learned.md): confirmed pre-pilot findings only
- [Follow-up](follow-up.md): seven-day follow-up and opportunity qualification
- [Quick start](QUICK_START.md): maintainer setup and readiness gate
- [Implementation status](IMPLEMENTATION_STATUS_2026-09-11.md): verified
  repository changes and remaining external gates
- [Evidence template](EVIDENCE_TEMPLATE.md): technical artifact manifest

The working recruitment tracker is
[`artifacts/receiver-pilot-tracker.csv`](../../artifacts/receiver-pilot-tracker.csv).

## Status definitions

- `Prepared`: product and recruitment process are ready.
- `Running`: at least one real external participant has started.
- `Completed`: that participant finished the tasks and interview.
- `Validated`: multiple participants independently confirmed a meaningful
  problem and demonstrated useful value.
- `Traction`: participants committed to continued testing, integration,
  partnership, or another concrete next step.
- `Client opportunity`: a specific person or organization has a real problem,
  decision relevance, product fit, continued interest, and one dated next step.

No weaker evidence may be promoted into a stronger status.
