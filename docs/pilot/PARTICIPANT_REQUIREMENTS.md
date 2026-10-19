# Pilot Participant Requirements

This document defines who the pilot needs, what each person will do, and the
practical cost of taking part. It is the internal selection specification. The
public summary is in [PROJECT_ONE_PAGER.md](PROJECT_ONE_PAGER.md), and the
screening questions are in [APPLICATION_FORM.md](APPLICATION_FORM.md).

## Cohort

Recruit eight eligible people so that six can participate and two can remain as
backups.

| Role | Pilot places | Backups | Purpose |
|---|---:|---:|---|
| Receiver owner or operator | 4 | 1 | Test registration, updates, owner control, history, and wallet burden |
| Network coordinator or developer | 2 | 1 | Test discovery, record interpretation, export, and integration value |

The six selected participants must represent at least two independent receiver
projects or communities. Prefer no more than two people from the same project.
Project contributors and people with only CKB development experience do not
count as external participants.

## Eligibility

### Receiver owner or operator

The person must:

- operate an ADS-B or Mode S receiver now, or have operated one during the last
  12 months;
- be able to describe a real receiver addition, replacement, relocation,
  transfer, or retirement; and
- verify that experience with a public profile or project link, a redacted
  software status screen, or a redacted photograph of the receiver setup.

The person does not need to connect a physical receiver or share live aircraft
data during the pilot.

### Network coordinator or developer

The person must currently maintain, integrate, monitor, or make inventory
decisions for more than one receiver. At least one selected coordinator should
have changed a real receiver inventory or the software that consumes it.

Relevant experience may include feeder management, receiver directories,
multi-receiver monitoring, MLAT infrastructure, APIs, data export, or network
operations. It must be verified through a public project or profile, or through
private evidence that is not published without separate permission.

## Participant Tasks

### Receiver owner or operator

The participant will:

1. describe how they currently identify and manage receivers;
2. use a supported wallet on CKB Pudge testnet;
3. create a receiver record with a non-sensitive label and fictional or coarse
   study coordinates;
4. find the record in the public directory;
5. update it and confirm that its permanent identity did not change;
6. inspect its owner and change history;
7. explain what the registry proves and what it cannot prove; and
8. return within seven days and find the record without live help.

### Network coordinator or developer

The participant will:

1. describe their current receiver inventory and integration process;
2. find assigned records in the public directory without being given their
   blockchain storage locations;
3. identify each record's current owner, status, version, and history;
4. distinguish records that have the same human-readable label but different
   permanent identities;
5. export or consume the documented JSON data; and
6. complete a small follow-up, such as testing an import, reviewing the API and
   estimating integration work, or recording a decision and its blockers.

Coordinators do not need a wallet unless they separately choose to test owner
actions.

## Practical Requirements

| Requirement | Receiver owner or operator | Network coordinator or developer |
|---|---|---|
| Time | 10-15 minutes preparation; up to 45 minutes testing; up to 20 minutes interview; 10-15 minute return task | 5-10 minutes preparation; up to 45 minutes testing; up to 20 minutes interview; about 20-45 minutes for the integration follow-up |
| Total estimated time | 85-95 minutes | 90-120 minutes |
| Computer | Laptop or desktop that can run a current Chromium-based browser and a video call | Laptop or desktop that can run a current Chromium-based browser, a video call, and open a JSON file |
| Wallet | Supported CKB wallet configured for Pudge testnet; testnet CKB supplied through the normal faucet process | Not required for directory and export tasks |
| Receiver hardware | Not required during the session | Not required |
| Audio/video | Working microphone; screen sharing is strongly preferred; camera is optional | Working microphone; screen sharing is strongly preferred; camera is optional |
| Internet | Stable connection suitable for a video call, screen sharing, the pilot site, the CKB testnet, and a block explorer | Same, plus the ability to download a small JSON export |
| Planning bandwidth | At least 5 Mbps download and 2 Mbps upload; 10 Mbps download and 5 Mbps upload is preferred | Same |
| Location | Remote participation from any country where the participant may lawfully use the test software | Remote participation from any country where the participant may lawfully use the test software |
| Location data shared | No home address or exact receiver location; use fictional or deliberately coarse study coordinates | No physical location data required |
| Technical knowledge | Comfortable operating common receiver hardware or software; no CKB or blockchain knowledge required | Comfortable with multi-receiver operations, inventory, APIs, or data integration; no CKB knowledge required |

The bandwidth values are planning estimates for screen sharing, not measured
limits of the application. Offer an audio-only call and participant-controlled
screen sharing when video quality is poor. Do not exclude an otherwise qualified
person solely because their camera is unavailable.

## Time And Programme Cost

Using the upper end of the estimates:

- four owner participants require about 6 hours 20 minutes of participant time;
- two coordinator participants require about 4 hours of participant time;
- the complete six-person cohort requires about 10 hours 20 minutes of
  participant time; and
- six proposed incentives at $30 each require $180.

The $30 incentive is conditional on grant approval. It is paid only after the
participant completes the test, interview, and agreed follow-up. Recruitment
messages and the application must not imply that payment is already funded.

The maintainer should reserve at least 12 hours for the six live sessions,
session setup, notes, and follow-up review. This does not include recruitment,
product fixes, deployment, or final analysis.

## Safety And Privacy Boundaries

Never request or record a private key, seed phrase, password, exchange login,
receiver-network login, feed key, private feed URL, IP address, or exact private
receiver location. A participant approves every testnet transaction in their own
wallet. The maintainer may explain or recover a failed step but may not sign or
submit a participant transaction.

Use a pseudonymous participant ID in repository evidence. Keep names and contact
details in an access-controlled system outside the repository. Public wallet
addresses, transaction identifiers, screenshots, quotations, and organization
names require explicit publication permission when they can identify a person.

## Selection Rules

Select participants using the same rules for every applicant:

1. Confirm role eligibility and relevant experience.
2. Confirm the full time commitment and availability.
3. Confirm the required computer, internet access, and wallet readiness for the
   person's role.
4. Build a cohort representing at least two independent communities.
5. Prefer recent, concrete operating experience over general interest.
6. Record an applicant as confirmed only after they explicitly agree in writing.

An application, reaction, referral, or general expression of interest is not a
confirmed place in the pilot.

## Start Gate

Applications and non-binding expressions of interest may be collected before the
product is ready. Do not schedule a transaction session until the readiness gate
in [READINESS_GATE.md](READINESS_GATE.md) passes. In particular, the exact
contract binary needs independent review, the browser wallet flow needs a funded
rehearsal, and a complete hosted pilot environment must be available.
