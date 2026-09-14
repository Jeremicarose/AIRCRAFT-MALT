# CKB Spark Grant Analysis

Status date: 2026-09-14

## Executive conclusion

AIRCRAFT-MALT should not ask Spark to fund a first MVP. The technical
foundation already exists: Registry V2 contract rules, Python and TypeScript
clients, a CCC signer workflow, cross-language conformance tests, an immutable
Pudge deployment, signed lifecycle evidence, and an operator-facing Registry
directory.

The honest grant case is narrower. Spark support would fund the work needed to
learn whether independently owned receiver networks value portable,
owner-controlled identity enough to use it instead of a spreadsheet or one
network administrator's database.

The proposal should therefore be framed as:

> Validate, review, and package an existing CKB Receiver Registry so receiver
> operators and network coordinators can test portable identity across network
> boundaries.

## Problem and target user

The primary users are:

- ADS-B or Mode S receiver operators who own their hardware and records;
- coordinators who assemble receivers owned by different people; and
- developers integrating receiver infrastructure into more than one network.

The problem is not basic receiver registration. Existing networks and ordinary
databases already provide registration, discovery, device management, and
provenance. Registry V2 is useful only if users need one or more of these extra
properties:

- one identity that can be consumed by several applications or networks;
- ownership changes authorized by the current owner rather than one directory
  administrator;
- a verifiable sequence of metadata changes and transfers;
- permanent, inspectable revocation rather than silent deletion; and
- shared discovery rules that no single coordinator can rewrite privately.

If operators and coordinators do not value those properties, a centralized
directory is the simpler product. The pilot must be allowed to reach that
conclusion.

## Why CKB

CKB is used for the part that benefits from shared verification:

```text
owner lock authorizes change
  -> Type ID preserves the 32-byte Receiver Identity
  -> Registry V2 validates the next lifecycle state
  -> indexer exposes the current or historical cell
  -> coordinators and applications verify the same lineage
```

The human `receiver_id` is only a label. It is not the canonical key. CKB does
not prove that hardware exists, coordinates are honest, clocks are synchronized,
or stream data is truthful. Those claims require operational evidence outside
the Registry.

## Actual status

| Area | Status | Evidence | Remaining |
|---|---|---|---|
| Registry V2 contract | COMPLETE | 5 Rust host and 11 CKB-VM lifecycle/attack tests | Independent review |
| Canonical identity and discovery | COMPLETE | Python and TypeScript key by 32-byte Type ID, paginate to exhaustion, quarantine duplicates, and exclude revoked tombstones from active results | Monitor public indexer behavior during pilots |
| Cross-language protocol | COMPLETE | 57 shared cases and 171 Rust/Python/TypeScript assertions pass | Extend only when protocol scope changes |
| TypeScript SDK | COMPLETE IN SOURCE | 72 tests cover codec, Type ID, cursor-exhaustive discovery and history, deployment checks, and CCC signer transaction construction | First npm release and an external developer install |
| Immutable testnet lifecycle | COMPLETE | `data1` deployment plus CKB CLI-signed create, update, transfer, revoke, seven rejected attacks, local CI, and 100 live-chain checks pass | GitHub CI provenance and independent review for release use |
| Browser Registry workflow | PARTIAL | Registry opens first; My receivers, history, JSON export, and SDK-backed lifecycle controls are implemented; 22 current unit checks pass, while the pinned `4fc8fce` evidence records 9 production-browser checks | Run the current 12-check browser suite on a clean final commit and complete a funded CCC wallet rehearsal |
| MLAT consumer | PARTIAL | Replay integration and strict live gates pass automated tests | Four synchronized physical feeds and independent position reference data |
| Pilot and demand | MISSING | Materials and recruitment research exist; 0 participants are claimed | Recruit, observe, and report real sessions |
| Production service | MISSING | Local/reference deployment only | Reviewed public pilot deployment and operating evidence |

The complete status and claim limits are maintained in
[Project Status](PROJECT_STATUS.md) and [Pilot Readiness](../PILOT_READINESS.md).

## What Spark support should fund

### 1. Independent technical review

Review the exact source and binary already deployed with `data1`. Publish the
review, fix confirmed findings, and deploy a new immutable binary only if those
fixes change the contract. This work reduces risk; it does not manufacture a
claim that the current contract is audited.

### 2. Wallet and developer acceptance

Run the existing create, discover, update, transfer, and revoke journey through
normal CCC wallet approvals. Test the package from a clean external project and
publish the SDK only after its protected release checks pass. No raw private key
workflow should be introduced.

### 3. Operator and coordinator pilot

Observe real operators and coordinators completing the documented tasks. Ask
them to compare Registry V2 with their current directory process. Capture where
portable ownership or lifecycle proof changes a decision, and where it adds
cost without value.

### 4. Evidence and adoption decision

Publish anonymized task results, technical failures, objections, requested
integrations, and concrete follow-up commitments. End with an evidence-based
decision: continue, change the target user, narrow the protocol, or stop.

## Pilot evidence to collect

The pilot should answer these questions without leading participants:

- Can an owner understand which identity remains stable across an update or
  transfer?
- Can a coordinator independently verify the current owner, sequence, status,
  provenance, and revoked history?
- Does using the same identity in two receiver-network contexts solve a real
  coordination problem?
- Are public coordinates acceptable, or does the current schema prevent use?
- Does wallet approval give useful ownership control, or create unacceptable
  operational friction?
- Would the participant continue testing, integrate the SDK, introduce another
  evaluator, or return to a centralized tool?

Preparation, repository tests, maintainer observations, and recruitment leads
are not participant validation. Only completed sessions and explicit follow-up
actions may be reported as user evidence.

## Deliverables suitable for a Spark proposal

1. Independent Registry V2 review report tied to exact source and binary hashes.
2. Clean CI and release evidence for Rust, Python, TypeScript, browser QA,
   conformance, dependency scanning, SBOM, and provenance.
3. One CCC wallet-driven Pudge lifecycle with public transaction evidence.
4. A published or commit-pinned SDK journey tested by an external developer.
5. A working public pilot environment with Registry as the first screen and
   MLAT clearly labeled as a reference consumer.
6. Real operator/coordinator session records using the existing consent and
   feedback templates.
7. A final demand report containing both positive and negative findings and a
   justified next product decision.

## Claims that must not appear

Do not claim any of the following without new external evidence:

- customers, partners, adoption, revenue, or production deployment;
- confirmed pilot participants;
- an independent audit;
- a browser or TypeScript SDK-driven lifecycle;
- live MLAT accuracy from physical receivers;
- proof that on-chain coordinates, hardware, or data streams are truthful; or
- a general physical-infrastructure protocol. Registry V2 currently requires
  the receiver-specific `mode-s` capability.

## Short proposal sequence

The shortest credible sequence is:

```text
pin final source and evidence
  -> independent contract review
  -> funded CCC wallet rehearsal
  -> clean public CI and pilot deployment
  -> operator/coordinator sessions
  -> publish evidence and product decision
```

This sequence uses the grant to test usefulness and demand. It does not ask the
grant to fund technology that the repository already contains.
