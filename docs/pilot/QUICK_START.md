# Pilot Quick Start

This guide is for the maintainer preparing a pilot session. It is not evidence
that a participant has completed the pilot.

## 1. Pin and verify the source

Use a clean checkout of the pilot commit and record both identifiers:

```bash
git rev-parse HEAD
git rev-parse HEAD^{tree}
```

Run the Registry V2 implementations against the shared corpus:

```bash
python3 -m pytest -q tests/registry
(cd contracts/registry-v2 && make test && make check)
(cd sdk/typescript && npm ci && npm test)
python3 tools/registry/generate_registry_v2_conformance_report.py
```

Do not start participant sessions if any implementation disagrees with the
corpus.

## 2. Prepare the testnet environment

Use CKB Pudge testnet and a reviewed Registry V2 deployment with
`hash_type=data1`. The historical 2026-07-30 deployment is read-only because its
type-hash binding allows mutable code. Do not use it for participant writes.

The repository currently defaults to the immutable deployment recorded in
`evidence/registry-v2-testnet-2026-09-11-data1-final`. Its lifecycle is
chain-verified but its contract has not been independently reviewed. Use the
public identifiers already pinned in `.env.example`; do not substitute the
historical July values.

Configure the backend with the immutable binary data hash and configure the
frontend build with the same hash and contract outpoint:

```bash
RECEIVER_REGISTRY_TYPE_HASH=0x...
RECEIVER_REGISTRY_HASH_TYPE=data1
ALLOW_MUTABLE_REGISTRY_CODE=false
NEXT_PUBLIC_REGISTRY_CODE_HASH=0x...
NEXT_PUBLIC_REGISTRY_CONTRACT_TX_HASH=0x...
NEXT_PUBLIC_REGISTRY_CONTRACT_INDEX=0
```

Each owner needs a supported wallet with enough testnet CKB for cell capacity
and fees. The maintainer must never request a seed phrase or raw private key.

Before a real session, complete a fresh SDK-driven create, update, transfer, and
revoke using the exact UI build that participants will use. Save the transaction
hashes and verify them through an independent CKB RPC or explorer.

## 3. Apply the readiness gate

A participant session may start only when all of these are true:

- the source commit and UI build are pinned;
- the deployment is independently reviewed and uses immutable `data1` code;
- automated Rust, Python, and TypeScript tests pass;
- the browser can connect to a supported Pudge wallet;
- create and update have passed with a maintainer-owned test identity;
- discovery shows the canonical 32-byte identity and provenance;
- duplicate identities and revoked records fail closed in the UI;
- participant consent, privacy rules, and task IDs are prepared;
- support and recovery steps have been rehearsed.

The browser transaction flow is implemented and points to the immutable
`data1` deployment. Type checking and the production build pass, but the
current source still needs one complete clean browser run. It has not been
executed with a funded CCC signer, and the deployed contract is still unaudited.
All three are readiness dependencies, not participant evidence.

## 4. Run and preserve the session

Use the role-specific steps in `OPERATOR_WORKFLOW.md`. Record interventions and
failures as they happen. Store only the data allowed by the participant's
consent. Use `EVIDENCE_TEMPLATE.md` for the bundle and run the offline verifier
before making any claim from a transaction.
