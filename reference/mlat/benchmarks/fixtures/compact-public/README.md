# Attributed compact historical source

Unmodified `sensors.csv` and `set_1.csv` from the MPyC v0.11 MLAT example,
derived from **LocaRDS: A Localization Reference Data Set**, M. Schäfer,
M. Strohmeier, M. Leonardi and V. Lenders (2021).

- Source: https://github.com/lschoe/mpyc/tree/v0.11/demos/data/mlat
- Original: https://doi.org/10.5281/zenodo.4739276
- Data licence: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- Exact file checksums: [source manifest](../mpyc-gps-five-source.json)

These data files retain the upstream data licence; original application code
remains MIT licensed. No source values were changed. They contain 362 historical
events with five receiver observations each, selected upstream as GPS timed.
The source includes receiver geometry and aircraft-reported reference positions.
Arrival timestamps are **dataset-relative nanoseconds**, not a known UTC epoch.
There are no original Mode-S frames, current CKB identities, or per-observation
clock uncertainty measurements. Their absence must remain explicit in replay.
