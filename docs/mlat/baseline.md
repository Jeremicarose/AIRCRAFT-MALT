# MLAT Baseline

## Current Production Pipeline

The production MLAT pipeline requires:

- Stable receiver identity
- Original Mode-S frame
- Receiver timestamp in nanoseconds
- Documented clock source
- Clock uncertainty <= 100 ns
- Receiver latitude
- Receiver longitude
- Receiver altitude
- Valid receiver lifecycle state

## LocaRDS Diagnostic

LocaRDS was evaluated separately from the production pipeline.

Result:

- Decision: NO-GO for unchanged production pipeline
- Held-out transmissions: 300
- Successful solver positions: 236
- Median horizontal error: 34.6 m
- 95th-percentile 3D error: 3.28 km
- Worst 3D error: 52.8 km

## Interpretation

The diagnostic demonstrates that the existing solver can produce useful
positions from calibrated multi-receiver observations.

It does not validate the complete production pipeline because correlation,
CKB receiver identity, clock-source qualification, and the <=100 ns
clock-uncertainty gate were bypassed.

## Tests

117 existing MLAT tests pass.

No LocaRDS adapter or production code was added.
