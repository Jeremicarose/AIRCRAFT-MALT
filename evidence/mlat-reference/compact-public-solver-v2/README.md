# Compact public solver benchmark v2

Complete 362-event historical numerical baseline with a synthetic control.
Report generation is deterministic in the recorded Python/NumPy environment.
The numerical algorithm and all rejection thresholds are unchanged; typing-only
annotations were added, with executable AST equivalence recorded in the audit.

- `report.json`: all outcomes, errors, diagnostics, geometry, hashes and runtime.
- `report.sha256`: exact report checksum.
- `source/`: exact solver/benchmark code corresponding to the report hashes.
- `checksums.sha256`: all files in this package.

Run the current command from the repository root:

```bash
python tools/mlat/run_compact_solver_benchmark.py --output /tmp/compact/report.json
```

The bundled MPyC v0.11/LocaRDS CSVs under
`reference/mlat/benchmarks/fixtures/compact-public/` carry CC BY-SA 4.0 attribution.
No data is live. Raw Mode-S frames, per-observation clock uncertainty and CKB
identities are absent; the compact replay adapter explicitly preserves those limits.
