# Operator Pilot Launch Plan

Status date: 2026-10-07

This plan turns the existing research package into a recruitable programme. It
does not count prepared documents, maintainers, CKB-only testers, or simulated
receivers as external receiver-operator evidence.

## Outcome

Complete six moderated sessions and six seven-day follow-ups:

- four current or recent ADS-B / Mode S receiver operators;
- two coordinators or developers responsible for multiple receivers; and
- two qualified backups who may replace cancellations.

The study answers one decision: does a persistent, owner-controlled receiver
identity solve enough cross-network coordination pain to justify further
development and integration work?

## Two-stage recruitment

### Stage A: problem interviews while readiness is incomplete

Run up to five 20-minute conversations without wallet actions or product tasks.
Ask about the last receiver move, replacement, transfer, retirement, or network
migration. These calls test the problem and recruitment message. They do not
count as pilot completions.

State clearly that these are unpaid discovery conversations unless a separate
payment has been approved. Do not imply that a later paid place is guaranteed.

### Stage B: funded product pilot

Open the formal application only after participant money is reserved and the
readiness gate passes. Selected participants complete the role-specific tasks,
interview, and seven-day follow-up described in
[PARTICIPANT_REQUIREMENTS.md](PARTICIPANT_REQUIREMENTS.md).

## Recruitment funnel

The current 13 researched leads are not enough for a reliable six-person cohort.
Use this planning funnel:

| Stage | Target | Evidence |
|---|---:|---|
| Relevant leads | 40 | Public role or project evidence |
| Permission requests or direct messages | 24 | Dated outbound message |
| Responses | 12 | Reply from the person or community moderator |
| Applications | 10 | Private application submission |
| Eligible applicants | 8 | Screening criteria passed |
| Confirmed participants | 6 + 2 backups | Written agreement to scope and timing |
| Completed | 6 | Session, interview, and follow-up complete |

These are operating targets, not evidence of current traction.

## Channel order

1. Ask moderators for permission in established receiver communities. Start
   with the FlightAware ADS-B discussion forum and the ADS-B / SDR Feeder Image
   community. Do not post until a moderator approves the wording and channel.
2. Contact maintainers and operators through contact methods they explicitly
   publish. Do not use unrelated GitHub issues as recruitment messages.
3. Ask every eligible respondent for one introduction after their session.
4. Invite CKB community members only when they also meet the operator or
   coordinator criteria. CKB experience alone does not qualify someone.
5. If fewer than four eligible applicants exist after 14 days, use a paid
   specialist research panel or a recruiting contractor. Apply the same role
   verification and privacy rules.

## Four-week operating sequence

### Week 0: funding and readiness

- publish the funding pre-discussion;
- reserve participant incentives in a separate budget line;
- complete the independent deployment review and wallet rehearsal;
- deploy the exact tested build; and
- publish the private application form and retention policy.

### Week 1: permission and direct outreach

- request permission from four relevant community moderators;
- send eight personalized direct invitations using published contact routes;
- publish the pilot page and 60-90 second overview; and
- respond to questions publicly so later applicants see the same answers.

### Week 2: screening

- send one follow-up to non-responders, then stop;
- screen applications twice during the week;
- keep role and community balance visible in the private tracker; and
- schedule only after written consent.

### Week 3: sessions

- run no more than two sessions per day;
- record every facilitator intervention and technical failure;
- stop immediately for wallet-network, secret-handling, or readiness failures;
- send the seven-day task before the call ends.

### Week 4: follow-up and report

- close every follow-up with a result or `no further action`;
- separate usability findings from product-value findings;
- publish only consented, redacted evidence; and
- make a continue, change, or stop recommendation.

## Daily dashboard

Record only evidence-backed counts:

```text
Leads / contacted / responses / applications / eligible
Confirmed / scheduled / completed / follow-ups complete
Declined / unreachable / disqualified, with reason category
Operator places filled / coordinator places filled / communities represented
Participant budget committed / paid / remaining
```

Response rate is responses divided by contacted people. Completion rate is
completed sessions divided by scheduled sessions. Never use all researched leads
as the denominator for either figure.

## Stop and change rules

- If fewer than two of 12 contacted operators describe the identity problem,
  pause product testing and revise the problem statement.
- If the wallet blocks two sessions, stop owner sessions and fix or remove the
  wallet-dependent task before recruiting more owners.
- If fewer than four eligible applicants exist after the second channel wave,
  use paid specialist recruitment or reduce the cohort only with a documented
  methodology change.
- If participants consistently value export/discovery but reject blockchain
  ownership, treat that as a product-direction result, not a usability defect.
- If funding is not confirmed, keep the public page in `preparing` or `interest`
  state and do not advertise a paid study.

## Actions that require the maintainer

1. Choose the private application service and project contact address.
2. Approve the funding amount and receiving arrangement.
3. Submit or authorize the public funding discussion.
4. Approve each community post or direct-message batch.
5. Hold and pay participant funds lawfully in each participant's location.
6. Moderate sessions and make selection decisions using the published rules.

The repository can prepare these actions but cannot truthfully perform or claim
them without the maintainer.
