# Registry V2 Cross-Language Conformance

The shared corpus at
`tests/registry/fixtures/registry_v2_conformance.json` is the protocol boundary
for the Rust contract, Python adapter, and TypeScript SDK. Every runtime emits a
normalized result for every case. The report generator fails unless all three
results are identical and match the corpus expectation.

## Run the audit

```bash
PYTHONPATH=src python3 tools/registry/generate_registry_v2_conformance_report.py
```

The command builds the TypeScript SDK, runs the host-side Rust adapter, executes
the Python adapter, and writes
`artifacts/registry-v2/conformance-report.json`. CI uploads the same JSON file as
the `registry-v2-conformance-<commit>` artifact. The report records the tested
Git commit and tree, plus whether tracked files were clean when it was created.

## Compared behavior

The corpus covers record decoding, creation validation, Type ID calculation,
successor ordering, ownership-transfer classification, permanent revocation,
registry script binding, duplicate live identity quarantine, and tombstone
visibility. Accepted records are compared field by field. Unsigned 64-bit
values are represented as decimal strings in the report so JavaScript cannot
lose precision. Coordinates are represented by their IEEE-754 64-bit patterns,
which makes differences such as positive and negative zero machine-visible.

Rust does not query the CKB indexer from inside the contract. For discovery
cases, its adapter applies fail-closed identity grouping to records decoded by
the real contract decoder. The CKB-VM transaction tests separately prove Type
ID creation, script-group continuity, owner authorization, transfer, duplicate
output rejection, burn rejection, and terminal revocation.

## Strict wire decisions

- Cell data is at most 16 KiB.
- JSON numbers use the standard JSON grammar. Leading `+`, leading zeroes, and
  negative spellings of unsigned fields are rejected.
- JSON string escapes are rejected. The on-chain parser does not decode them,
  so accepting them off-chain would let runtimes assign different text to the
  same cell bytes.
- Unknown or duplicate fields are rejected.
- No runtime coerces strings, booleans, floating-point values, or out-of-range
  integers into protocol integer fields.
