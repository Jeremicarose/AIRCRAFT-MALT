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

- [Brand and positioning](BRAND_AND_POSITIONING.md): product promise, audience
  messages, evidence boundaries, voice, visual language, and public status terms
- [Programme launch plan](PROGRAMME_LAUNCH_PLAN.md): two-stage recruitment,
  four-week operating sequence, funnel targets, stop rules, and owner actions
- [Funding proposal draft](FUNDING_PROPOSAL_DRAFT.md): milestone-based community
  funding request, budget, payment gates, and smaller sponsorship options
- [Participant consent](CONSENT_FORM.md): public-chain warning, private-data
  handling, payment status, recording choices, and withdrawal terms
- [Participant requirements](PARTICIPANT_REQUIREMENTS.md): exact roles,
  eligibility, tasks, time, equipment, internet, location, and skill requirements
- [Public project one-pager](PROJECT_ONE_PAGER.md): applicant-facing pilot summary
- [Application form](APPLICATION_FORM.md): form-ready screening questions and
  publication checklist
- [Visual assets](assets/README.md): editable Registry lifecycle, responsibility
  boundary, and receiver workflow diagrams with PNG exports
- [Video storyboard](video/README.md): nine ordered 16:9 frames with suggested
  timing and narration for a 60-90 second pilot overview
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

The maintainer-local recruitment tracker is
`artifacts/receiver-pilot-tracker.csv`. It is intentionally excluded from source
control because it may contain contact and recruitment status data.

The public pilot page is available at `/pilot`. It remains in `Programme
preparation` by default. The application link appears only when the deployment
provides a private HTTPS form URL and an explicit recruitment state. A paid
application opens only when funding is also explicitly marked as confirmed.

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
