# MLAT Solver And Timing Evidence

## What the replay now proves

Replay generates a transmission and only gives the runtime receiver arrival
times derived from the withheld scenario position. The normal correlator groups
those observations, the production clock gate qualifies them, and
`RobustMLATSolver` estimates a position. Only that estimate is stored with
`solver_method=robust_mlat`.

The scenario position is not copied into the database or dashboard. Tests use
it after the solve solely as an oracle for error assertions. This establishes
that the implemented pipeline performs TDOA localization; it does not establish
accuracy on live hardware.

## Precision contract

TDOA values are hundreds or thousands of nanoseconds. A binary floating-point
Unix timestamp near the current epoch cannot reliably represent all of those
differences. The localization contract therefore uses integer `timestamp_ns`
values and subtracts them before conversion to seconds.

The solver accepts small relative float times for isolated mathematical tests.
It rejects Unix epoch floats without integer nanoseconds and rejects groups
that mix precision modes.

Production additionally requires every observation to declare:

- `clock_synchronized: true`
- a common-timebase `timestamp_ns`
- a named `clock_source`
- `clock_uncertainty_ns <= MAX_CLOCK_UNCERTAINTY_NS`

At least four unique receivers must pass. Network arrival timestamps fail this
gate by design.

## Solver checks

The deterministic solver tests cover:

- a six-receiver exact noiseless localization using integer epoch nanoseconds
- a four-receiver exact noiseless localization using relative TDOA values
- all aircraft states across the complete replay receiver footprint
- rejection of precision-losing epoch float observations
- production replay storage from solver output rather than scenario truth
- rejection of an unsynchronized live group before solver invocation
- Beast clock affine mapping and 48-bit counter wraparound

Run them with:

```bash
python3 -m pytest -q \
  tests/mlat/test_solver.py \
  tests/mlat/test_production_mlat_pipeline.py \
  tests/mlat/test_beast_tcp_adapter.py \
  tests/mlat/test_correlator.py \
  tests/mlat/test_feed_transports.py
```

## What remains unproven

The replay clock has 1 ns declared uncertainty and idealized propagation. Real
receivers add oscillator drift, antenna and cable delay, decoder latency,
multipath, packet loss, bad geometry, and Mode-S correlation ambiguity. A valid
live evidence run still requires calibrated clocks at four or more receivers,
recorded clock metadata, a trusted aligned reference track, and published error
distributions. Replay output remains explicitly non-benchmarkable even though
it is produced by the real solver.
