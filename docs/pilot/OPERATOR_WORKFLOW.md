# Pilot Operator Workflow

Use one pseudonymous task ID for each participant. Do not enter a private home
location, private feed URL, seed phrase, or raw private key.

## Receiver owner task

1. Confirm that the environment identifies a reviewed immutable Registry
   deployment on CKB Pudge testnet, then connect a supported testnet wallet.
2. Create a test receiver record with a non-sensitive label and approximate or
   explicitly fictional coordinates approved for the study.
3. Wait for transaction confirmation.
4. Find the record in discovery without using its cell outpoint.
5. Confirm that the displayed `receiver_identity` is a 32-byte `0x` value and
   is different from the human receiver label.
6. Update an allowed field. Confirm that the identity is unchanged and the
   sequence increases by exactly one.
7. Explain, in your own words, what the owner lock and history prove and what
   they do not prove about the physical receiver.
8. Return within seven days and find the record again without a live maintainer
   call.

The transfer and revoke identities used in a participant session should be
maintainer-owned test records unless the consent and task script explicitly
explains the permanent effect. Revocation cannot be undone.

## Network coordinator task

1. Open the public receiver directory without receiving participant outpoints.
2. Find assigned identities by canonical `receiver_identity`.
3. Distinguish two records that deliberately share the same human label but
   have different CKB identities.
4. Identify the current status, owner lock, sequence, transaction, and outpoint.
5. Confirm that a revoked tombstone appears only in historical results.
6. Export or consume the documented JSON representation.
7. Compare this workflow with the coordinator's current inventory system.
8. Complete one follow-up: a small import, an integration-effort review, or a
   dated decision with the next step and blocking conditions.

## Facilitator rules

- Record every prompt, recovery step, and technical failure.
- The facilitator may explain the task but may not sign or submit for a participant.
- Do not count a task as completed if the facilitator performed the key action.
- Do not turn confusion into a positive result. Capture it as product evidence.
- Stop immediately if the participant is asked for a secret or the network is
  not Pudge testnet.
- Stop if Environment reports `Historical mutable type` or Owner actions reports
  that the deployment is read-only.
