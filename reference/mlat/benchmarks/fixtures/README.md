# Compact Public MLAT Fixtures

These files define a small, reproducible **solver-only** benchmark. They do not
represent live receiver traffic, CKB Registry identities, or a complete
production observation pipeline.

`mpyc-gps-five-source.json` pins the two external CSV files by version, byte
size, Git blob identifier, and SHA-256 checksum. The unmodified third-party CSV files are now retained under `compact-public/`,
with attribution and their upstream CC BY-SA 4.0 licence, for offline reproduction.

`mpyc-gps-five-event.json` is a transformed extract of historical event
`5711382`. It includes the published receiver coordinates and timestamps, plus
an explicitly synthetic exact-propagation timing control.

## Attribution And Licence

The historical values are based on the MPyC MLAT example data, which is derived
from LocaRDS:

- M. Schäfer, M. Strohmeier, M. Leonardi, and V. Lenders, "LocaRDS: A
  Localization Reference Data Set," *Sensors*, 2021.
- Original dataset: <https://doi.org/10.5281/zenodo.4739276>
- Filtered MPyC example: <https://github.com/lschoe/mpyc/tree/v0.11/demos/data/mlat>

The dataset-derived fixture content is provided under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The repository's
MIT licence continues to apply to original benchmark code.
