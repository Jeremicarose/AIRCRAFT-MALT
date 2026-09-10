# Pilot Session Guide

Target duration: 40 minutes. Maximum: 45 minutes.

Before starting, record the participant ID, role, consent version, application
build, browser, Registry deployment, and whether screenshots or public testnet
identifiers may be retained. Confirm that the participant is external to the
project and has relevant receiver or network experience.

## 1. Context, 5 minutes

Do not explain the product yet. Ask:

- How do you currently manage and identify receivers?
- Tell me about the last replacement, relocation, transfer, or retirement.
- What records or systems had to change?
- Do you work across multiple receiver networks?
- Which ownership or provenance facts matter to you?
- What did the last coordination problem cost in time, engineering work, risk,
  trust, or maintenance?

Record concrete past behavior. Do not turn a hypothetical concern into a
validated problem.

## 2. First use, 8 minutes

Give the participant the application without a tour. Say only:

> Please explore this application as if you had received the link from a
> colleague. Tell me what you think is real, what you think is simulated, and
> what you would do first.

Record the first click, time to first meaningful task, misunderstood terms,
dead ends, expectations, and every facilitator intervention.

## 3. Registry workflow, 10 minutes

Ask the participant to:

1. Confirm that the application is on CKB testnet.
2. Connect their testnet wallet without exposing credentials.
3. Register a non-sensitive test receiver.
4. Discover it by label or canonical identity.
5. Explain the difference between the label and the 32-byte identity.
6. Update allowed metadata and confirm the identity is unchanged.
7. Transfer a maintainer-provided test identity to the designated test wallet.
8. Inspect owner and lifecycle history.
9. Revoke a maintainer-provided disposable test identity.
10. Confirm that revocation is terminal and the identity is unchanged.

Do not ask a participant to revoke a record they expect to keep. Stop the
session if the app is not on testnet or asks for a secret.

## 4. MLAT workflow, 9 minutes

State clearly whether aircraft and observations are live or replay data. Then
ask the participant to:

1. Find an aircraft on Live Map.
2. Select it and describe its current state.
3. Inspect the contributing receivers.
4. Open one receiver.
5. Find its Registry identity, owner, lifecycle state, and operational state.
6. Explain what CKB proves and what MLAT proves.
7. Return to the same aircraft without losing context.

## 5. Interview, 8 minutes

Use [interview-guide.md](interview-guide.md). Ask for criticism before asking
about adoption. End with one concrete seven-day action or explicitly record
`no further action`.

## Completion rules

A task is `passed` only when the participant performs it. Use `passed with
intervention` when the facilitator explains or repairs something. Use `failed`
when the task cannot be completed. `Not attempted` is not a pass.

A session reaches `PILOT RUN` when a real participant begins the first-use test.
It reaches `INTERVIEWED` only after the product tasks and interview are complete.
