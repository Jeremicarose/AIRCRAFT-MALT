# Spark Program | CKB Receiver Registry Validation Pilot

> **Review draft:** This proposal is designed for the product-validation stage,
> not the idea-to-MVP stage. No external participant, customer, or partner is
> claimed yet. The items in "Before submission" must be completed before this
> draft is posted as a final application.

## 1. Project overview

**Project name:** CKB Receiver Registry Validation Pilot

**One-line summary:** A four-week sponsored pilot that will test whether small,
multi-owner Mode S/ADS-B receiver networks need a shared receiver directory on
CKB, whether operators will complete the workflow in practice, and whether a
network coordinator sees enough value to justify a real integration discussion.

**Project type:** Product-validation pilot with a small CKB testnet DApp.

### Product definition

The product being tested is a browser-based receiver coordination tool for
small or community-run aircraft receiver networks where receiver ownership is
distributed across more than one person.

It is not a general aviation dashboard and it is not an MLAT-accuracy product.
Its narrow job is to let a receiver owner control and update their own receiver
identity while giving a network coordinator a public directory of current
records, authorisation history, and revocation status.

In practical terms, the product promises four things:

1. **Owner-controlled registration:** each receiver owner creates and updates
   their own record through their own wallet instead of asking a central admin
   to edit a shared spreadsheet or database.
2. **Shared discovery:** a coordinator can discover current receiver records in
   one public format without relying on a project-owned directory server.
3. **Inspectable history:** a coordinator can see who authorised each accepted
   change and how the record evolved.
4. **Permanent retirement:** a revoked identity stays visibly retired instead of
   silently disappearing from an internal admin system.

The technical prototype already works. The missing evidence is product demand,
user behaviour, and partner relevance. This grant will fund a structured pilot
with real receiver operators and network coordinators. It will answer three
practical questions:

1. Does the multi-owner coordination problem occur often enough to matter?
2. Do owner control, public discovery, change history, and permanent revocation
   provide enough value to justify wallet and blockchain complexity?
3. Is there enough demonstrated interest to support a later integration with a
   receiver network?

The pilot may produce a **continue**, **change**, or **stop** decision. A
negative result is valid if the test follows the published method and releases
the evidence.

## 2. Team profile

**Applicant:** Jeremic_Arose

**Role:** Solo developer, researcher, and maintainer of Registry V2 and its MLAT
reference implementation.

**GitHub:** [Jeremicarose](https://github.com/Jeremicarose)

**Project repository:**
[Jeremicarose/AIRCRAFT-MALT](https://github.com/Jeremicarose/AIRCRAFT-MALT)

**Public project discussion:**
[MLAT Airspace Console - CKB-Based Receiver Registry for Aviation Data Infrastructure](https://talk.nervos.org/t/mlat-airspace-console-ckb-based-receiver-registry-for-aviation-data-infrastructure/10438)

**Discord:** **BLOCKED before submission:** the applicant must provide the
preferred public contact handle.

**Email:** **BLOCKED before submission:** the applicant must provide the
preferred application contact address.

Relevant completed work includes:

- a Rust `no_std` Registry V2 type script for CKB-VM;
- Rust host tests and CKB-VM lifecycle tests;
- Python record validation and paginated CKB indexer discovery;
- one signed create, update, transfer, and revoke lifecycle on CKB testnet;
- a replay-capable MLAT backend and Next.js receiver operations console; and
- an MIT-licensed repository with reproducibility and evidence tooling.

This is a solo application. No external adopter, security auditor, production
deployment, confirmed pilot participant, or commercial partner is claimed in
this draft.

## 3. Project background

### The real-world situation

A small receiver network may combine radio receivers owned by several
volunteers, researchers, or independent operators. The network coordinator
needs to know which receiver is active, who controls it, what capabilities it
declares, and whether its record has changed.

Today this can be managed in a spreadsheet or central database. That is the
right solution when one trusted organisation owns and administers every
receiver. The product hypothesis applies only when receiver ownership is
distributed. In that situation, the central coordinator becomes responsible
for every identity change, and other participants cannot independently verify
who authorised a change or whether an old identity was permanently retired.

Registry V2 uses CKB to give each owner control over their own record while
preserving a public, ordered lifecycle that network software can inspect.

### What is proven and what is not

The repository proves that CKB can enforce the receiver lifecycle. Invalid
sequence changes, identity duplication, deletion, and revoked-identity
resurrection are rejected by the contract. One complete lifecycle has been
executed on CKB testnet and saved in a verifiable evidence bundle.

The repository does **not** prove that receiver operators need this product,
that wallet onboarding is acceptable, or that a network coordinator would
integrate it. That commercial and user evidence is the purpose of this pilot.

### Target market

The first narrow market is community, research, and open-source Mode S/ADS-B
projects with roughly 4-20 receivers owned by more than one person.

The proposal distinguishes two roles:

- **Initial customer or adoption partner:** the network coordinator or developer
  responsible for receiver inventory and network integration.
- **Primary end user:** the person who owns, installs, or maintains a receiver
  and needs to create or update its record.

The proposal does not target airlines, airports, national surveillance
networks, air-traffic controllers, or general consumers. This is not an
air-traffic-control product and must not be used for aviation safety decisions.

### Product-market-fit hypotheses

The pilot will test the following assumptions instead of presenting them as
facts:

- independent receiver owners experience a real coordination or trust problem;
- owners value controlling their own receiver records;
- coordinators value a shared discovery format and inspectable history;
- the value is large enough to justify CKB wallet onboarding; and
- a coordinator who sees the value will take a concrete follow-up step toward
  an integration.

## 4. Solution and validation programme

### Product being tested

The pilot will use the focused browser workflow in the existing Next.js
reference application. After the required funded-wallet rehearsal, a participant
will be able to:

1. connect a supported CKB Pudge testnet wallet;
2. register one receiver using non-sensitive, operator-declared metadata;
3. find the confirmed receiver identity in a public directory;
4. update an allowed field without changing the stable identity;
5. inspect the owner lock, lifecycle sequence, status, transaction, and
   outpoint; and
6. compare the active record with a controlled revoked identity.

The application will not accept raw private keys. Participants sign through a
supported wallet. The schema requires coordinates, so participants will use a
deliberately coarse or fictional study location instead of a private exact
receiver location. They will not be required to publish a feed endpoint or raw
aircraft observations.

This small DApp is an instrument for testing the product. The main outcome is
the validation evidence, not the number of interface features delivered.

### Pilot participants

The pilot will include six eligible participants:

- four people who currently operate, or operated within the previous 12
  months, a Mode S/ADS-B receiver; and
- two people who coordinate a receiver network, maintain relevant software, or
  consume multi-receiver inventory data.

The cohort must represent at least two independent receiver projects or
communities. The applicant, close project contributors, and people whose only
qualification is CKB development will not count toward the six participants.

Eligibility will be checked using one of the following:

- a public feeder or project profile;
- a redacted receiver-software status screen;
- a redacted photograph of the receiver setup; or
- a public repository or project page showing relevant network work.

Private evidence will not be published without consent.

### Recruitment and engagement

Participants will be recruited through direct, individual outreach to public
Mode S/ADS-B feeder profiles, receiver forums, and open-source receiver
projects. These channels are recruitment sources, not claimed partners.

The recruitment funnel will be recorded so the pilot measures whether the
target audience can actually be reached:

```text
people contacted -> replies -> eligible candidates -> written interest
-> scheduled sessions -> completed sessions -> seven-day follow-up
```

Before the proposal is submitted, all six participants must provide a written,
non-binding expression of interest that explains the tasks, time commitment,
data collection, privacy terms, and $30 completion incentive. A redacted
recruitment summary will be attached to the application.

Each participant receives:

- one short eligibility and consent form;
- the same wallet preparation and task guide;
- one observed remote session of up to 45 minutes;
- one post-task questionnaire and interview of up to 20 minutes;
- one independent follow-up action within seven days; and
- a $30 equivalent incentive after the session and follow-up are complete.

### What each role will test

Each receiver owner will describe their current process, create and update a
testnet receiver identity, inspect its history, explain what CKB proves, and
return within seven days without a live maintainer call.

Each network coordinator will describe their current inventory process,
discover participant records without being given their cell outpoints, identify
the current owner and status, export the records in the documented JSON format,
and complete one follow-up action. The follow-up must be one of:

- importing the export into a small test or existing workflow;
- reviewing the public API/schema and documenting the integration effort; or
- writing a dated integration decision that states the next step and any
  blocking conditions.

The maintainer may explain the task and help recover from testnet or wallet
faults. The maintainer may not sign or submit a participant transaction. Every
intervention will be recorded.

### Go-to-market path being tested

This pilot tests a partner-led route to market:

1. Reach network coordinators through communities where receiver operators are
   already active.
2. Offer a small, free testnet evaluation using their real operating context.
3. Let the coordinator invite or refer receiver owners instead of acquiring
   every operator separately.
4. Use observed completion, return use, and integration work to decide whether
   a larger field integration is justified.
5. If the thresholds pass, approach one receiver network with a separate,
   evidence-backed integration proposal.

The likely adoption decision is made by the network coordinator, while receiver
owners must accept the workflow for adoption to succeed. This is why the pilot
tests both roles.

The pilot does not claim broad product-market fit and does not test pricing.
Possible later revenue from implementation support or managed services remains
a hypothesis for a later stage. Spark will test the problem, product value,
user behaviour, and first acquisition channel.

### Data and decision method

The consent form, task scripts, event schema, questionnaires, interview guide,
and decision rules will be committed before the first session. This prevents
the success criteria from being changed after the results are known.

The dataset will contain pseudonymous roles, eligibility method, task results,
timestamps, errors, assistance, public testnet transaction hashes,
questionnaire scores, coded interview responses, and follow-up actions. It will
not contain private keys, seed phrases, exact private locations, private stream
endpoints, or participant names without explicit consent.

#### Success measures

| Question | Measure | Continue threshold |
|---|---|---:|
| Can the target audience be reached? | Written eligible expressions of interest before submission | 6 |
| Is the problem real? | Participants describing a concrete current multi-owner coordination problem or workaround | At least 4 of 6, including both coordinators |
| Can owners use the product? | Owners completing create and update without maintainer signing or submission | At least 3 of 4 |
| Can coordinators consume the records? | Coordinators discovering and correctly reading assigned records | 2 of 2 |
| Is CKB-specific value understood? | Participants correctly separating on-chain lifecycle proof from physical truth | At least 5 of 6 |
| Is CKB-specific value wanted? | Participants rating owner control, public discovery, history, or permanent revocation as materially useful | At least 4 of 6, including one coordinator |
| Is there behavioural demand? | Participants completing the defined follow-up within seven days | At least 3 of 6, including one coordinator |
| Is a partner conversation justified? | Coordinators producing a concrete integration test or written integration decision | At least 1 of 2 |
| Is the evidence valid? | Included pilot transactions passing the offline verifier | 100% |

The final decision will be:

- **Continue:** all technical evidence passes, the owner and coordinator task
  thresholds pass, at least four participants see material CKB-specific value,
  at least three complete a follow-up, and one coordinator produces a concrete
  integration result.
- **Change and retest:** participants demonstrate value and follow-up interest,
  but task completion fails because of fixable wallet, wording, or interface
  problems.
- **Stop the standalone product direction:** the problem, CKB-specific value,
  behavioural follow-up, or coordinator integration threshold fails. Registry
  V2 may remain an internal technical component, but the pilot will not be used
  to claim market demand.

These are directional results from a small pilot. They cannot prove market size
or broad product-market fit.

## 5. Technical approach

### Architecture

```text
Receiver owner                      Network coordinator
      |                                      |
      v                                      v
Pilot browser application (Next.js + CKB-CCC)
  - wallet connection and participant task ID
  - receiver create/update workflow
  - public directory, provenance, and JSON export
  - consented task events and error logging
      |
      +---- CCC wallet/signing ----> CKB Pudge testnet
      |                                  |
      |                                  v
      |                         Registry V2 live cell
      |                         - stable Type ID
      |                         - owner lock
      |                         - ordered lifecycle
      |                         - terminal revocation
      |
      +---- CKB indexer/RPC <---- discovery and evidence
      |
      v
Anonymised pilot dataset and evidence bundle
```

### Technology

- **Frontend:** existing Next.js and TypeScript reference application.
- **Wallet and transactions:** CKB-CCC with a supported Pudge testnet wallet.
- **On-chain rules:** the existing Rust Registry V2 type script.
- **Discovery:** CKB RPC/indexer plus the existing Registry V2 validation rules.
- **Research evidence:** privacy-safe event records, JSON/CSV export, checksums,
  metric calculation, and an offline verifier.

CKB proves that an owner lock authorised a contract-valid state change. It does
not prove that the physical receiver exists, that its coordinates are correct,
or that its radio observations are honest. Participant eligibility is research
evidence, not on-chain hardware attestation.

Live MLAT processing is not part of this pilot. It would add hardware, timing,
coverage, and reference-data questions that do not help answer the product
demand question.

## 6. Execution plan

Recruitment is completed before funding so the grant does not depend on access
to an audience that has not been demonstrated.

| Week | Work | Milestone and evidence |
|---|---|---|
| Before submission | Confirm six eligible participants, collect written expressions of interest, add contact details, create the applicant-owned Spark repository, and publish a redacted recruitment summary | **Recruitment gate:** the complete target cohort exists before review |
| Week 1 | Add CCC wallet connection, Registry V2 create/update, directory, provenance, JSON export, and privacy-safe task events. Publish and lock the research protocol | **Pilot ready:** public test deployment, commit, CI result, test report, and dated protocol files |
| Week 2 | Run four receiver-owner sessions. Publish one controlled revoked identity. Record blocking fixes and application versions | **Owner testing complete:** four session records plus participant-created testnet lifecycle evidence |
| Week 3 | Run two coordinator sessions. Freeze the primary-session dataset. Start all seven-day follow-ups | **Coordinator testing complete:** six primary sessions, two discovery/export records, and validated anonymised data |
| Week 4 | Complete follow-ups, run the metric script, publish the report, partner-readiness brief, spending record, demo, and tagged release | **Validation complete:** reproducible continue/change/stop result and public evidence bundle |

Only defects that block a participant from continuing will be fixed after the
protocol is locked. Every change will be versioned so later participants are
not silently tested against a different product.

## 7. Required funding and breakdown

**Total requested: $1,000 USD equivalent, paid under the current Spark payment
policy.**

| Category | Work | Amount |
|---|---|---:|
| Technical work | Pilot browser workflow, wallet integration, discovery/export, telemetry, validation, and evidence tools | $480 |
| User research | Protocol preparation, six moderated sessions, follow-up coordination, and issue handling | $220 |
| Analysis and release | Metric analysis, final report, partner-readiness brief, demo, tagged release, and funding disclosure | $120 |
| Participant incentives | Six completion incentives at $30 each | $180 |
| **Total** |  | **$1,000** |

Infrastructure cost is $0. The pilot uses CKB Pudge testnet, the public
repository and CI, and a free public test deployment. It does not require a
server purchase, paid aviation feed, domain, or physical receiver purchase.

An incentive is paid only after the participant completes the agreed session
and follow-up. Unused participant funds will not become developer compensation
without committee approval and public disclosure.

## 8. Deliverables and how to verify

| Deliverable and format | Completion standard | Independent verification |
|---|---|---|
| Public pilot DApp and source repository | A supported Pudge wallet can create and update a Registry V2 identity; the directory can discover it and export provenance | Open the deployment, complete the written workflow, inspect the transaction links, then run the documented frontend tests and production build |
| Locked research and recruitment pack in Markdown/JSON | Eligibility, consent, recruitment funnel, tasks, questionnaires, event schema, intervention rules, and decision thresholds are committed before session one | Compare the protocol commit time with the first pseudonymous session timestamp |
| Six-participant anonymised dataset in JSON/CSV | Four verified receiver owners and two verified coordinators complete the primary protocol; withdrawals and missing data are reported | Run the dataset validator and compare its participant, role, and session counts with the redacted eligibility summary |
| CKB pilot evidence bundle | Participant transactions, saved RPC/indexer responses, source commit, manifest, and checksums are complete | Inspect explorer links and run the offline verifier; no code review is required |
| Reproducible analysis script and output | Every published metric and the continue/change/stop decision are calculated from the frozen dataset | Run one documented command and compare the generated table and decision with the report |
| Product-validation report in Markdown/PDF | Reports recruitment, problem evidence, task results, CKB value, follow-up behaviour, limitations, deviations, spending, and the decision | Check the report against the fixed outline and the pre-published thresholds |
| Partner-readiness brief in Markdown/PDF | Defines the validated target profile, acquisition funnel, strongest use case, objections, integration requirements, and recommended next partner action | Confirm every claim links to a result in the anonymised dataset or testnet evidence |
| Short public demonstration video | Shows owner registration/update and coordinator discovery without exposing private data | Follow the same path in the public DApp and compare the resulting transaction evidence |

Expected release commands will include equivalents of:

```bash
cd reference/mlat/frontend
npm ci
npm run typecheck
npm run build

python3 tools/registry/verify_pilot_dataset.py evidence/receiver-pilot-v1
python3 tools/registry/analyse_pilot.py evidence/receiver-pilot-v1
python3 tools/registry/verify_pilot_evidence.py evidence/receiver-pilot-v1
```

The exact commands and expected outputs will be pinned in the tagged release.
The demonstration video will help reviewers understand the workflow, but it
will not replace the dataset, transactions, tests, or evidence verifier.

## 9. Current state versus funded work

### Already completed and not funded

- Registry V2 contract and create/update/transfer/revoke rules;
- Rust host and CKB-VM lifecycle tests;
- Python validation and read-only indexer discovery;
- maintainer-operated command-line transaction tooling;
- one signed testnet lifecycle and rejected-attack evidence;
- replay MLAT backend and read-only receiver operations console; and
- MIT licence, deployment, security, and evidence documentation.

### Funded by this grant

- the minimum wallet-based browser workflow required for participant testing;
- public discovery, provenance, and JSON export in the pilot interface;
- the locked product-validation protocol and recruitment funnel evidence;
- six tests with qualified target users and seven-day follow-ups;
- participant incentives;
- anonymised data, reproducible analysis, and CKB evidence; and
- the final validation report and partner-readiness brief.

### Outside this grant

- a separately packaged TypeScript SDK;
- Registry V3 or a general physical-infrastructure contract;
- mainnet deployment or a security audit;
- live receiver feeds, MLAT accuracy, coverage, or reliability testing;
- physical hardware installation;
- ownership-transfer interface work;
- production hosting or service-level guarantees;
- paid marketing, commercial rollout, or a claimed partner integration; and
- airline, airport, or air-traffic-control use.

## 10. CKB alignment

CKB is part of the product behaviour being tested, not an added payment method.

- A live CKB cell represents the current receiver state.
- The owner lock authorises an update without a registry administrator signing
  for the owner.
- Registry V2 enforces the record format, exact lifecycle sequence, stable
  receiver label, and permanent revocation.
- Type ID keeps one receiver identity stable across transactions.
- The CKB indexer allows public discovery without relying on a project-owned
  directory server.
- Transaction history gives coordinators inspectable lifecycle provenance.

The practical alternative is a central database. It is simpler and should be
preferred when one trusted organisation controls every receiver. CKB is useful
only if independently owned receivers need separate control and shared,
inspectable state. The pilot is designed to find out whether that distinction
matters to the target users.

The existing V2 contract is receiver-specific and requires the `mode-s`
capability. It is unaudited and will remain on testnet during this pilot. It
must not be presented as a general physical-infrastructure protocol or a
production-ready service.

## After the pilot

If the continue thresholds pass, the evidence will support a conversation with
one receiver network about a separately scoped physical integration. That next
stage would test repeated live use, operational integration, and willingness to
pay for implementation or managed support.

If users see the value but cannot complete the workflow, the interface will be
changed and tested again before partner outreach.

If participants do not experience the problem, do not value the CKB-specific
properties, or do not take follow-up action, the project will stop presenting
Registry V2 as a standalone operator product. The result will be published so
that a larger grant is not requested on the basis of demand that was never
shown.

All original pilot software will remain available under the MIT License. The
blank research instruments, anonymised data, and report will be released under
CC BY 4.0 where participant consent and third-party rights allow it.

## Before submission

- [ ] Add the applicant's Discord account and email address.
- [ ] Confirm six eligible participants from at least two independent receiver
      projects or communities.
- [ ] Collect six written, non-binding expressions of interest.
- [ ] Publish a privacy-safe recruitment summary.
- [ ] Create the corresponding Spark project repository under the applicant's
      GitHub account and replace the repository link if needed.
- [ ] Confirm the reviewed baseline commit is public.
- [ ] Replace all remaining placeholders.
- [ ] Post the proposal in the Nervos Talk Spark subsection.
