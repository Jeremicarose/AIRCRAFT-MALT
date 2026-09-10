# Pilot Evidence Template

Create one immutable bundle for each pilot revision. The bundle should make
technical claims reproducible while protecting participant privacy.

## Required manifest fields

```json
{
  "schema_version": 1,
  "source_commit": "40 lowercase hex characters",
  "source_tree": "40 lowercase hex characters",
  "ui_build": "identifier or artifact hash",
  "network": "ckb_testnet",
  "registry_code_hash": "0x-prefixed 32-byte hash",
  "contract_outpoint": {
    "tx_hash": "0x-prefixed 32-byte hash",
    "index": "0x0"
  },
  "created_at": "ISO-8601 UTC timestamp",
  "files": [
    {"path": "relative/path", "sha256": "64 lowercase hex characters"}
  ]
}
```

## Technical artifacts

- exact source commit and tree;
- Registry V2 contract binary hashes and deployed script identity;
- Rust, Python, and TypeScript test reports;
- public testnet transaction hashes and relevant cell outpoints;
- decoded records including canonical `receiver_identity`, sequence, owner lock,
  status, and provenance;
- verifier output for lifecycle and discovery claims;
- UI build hash and browser version used for observed tasks.

## Product-validation artifacts

- versioned consent and task scripts;
- pseudonymous eligibility method;
- task outcomes, elapsed time, errors, and facilitator interventions;
- neutral questionnaire and coded interview results;
- seven-day follow-up evidence;
- the precommitted continue/change/stop calculation, including failed measures.

## Excluded data

Never store seed phrases, private keys, unredacted personal contact details,
private exact receiver locations, or private feed credentials. Public wallet
addresses and transaction hashes require explicit consent when linked to a
participant task ID.

Hash every file after redaction. Any changed file creates a new bundle version;
do not overwrite an already published manifest.
