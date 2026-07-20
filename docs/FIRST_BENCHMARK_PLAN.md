# First Benchmark Plan

## Recommended first benchmark

The best first benchmark region for this project is the **Northeast corridor** footprint already reflected in the project’s current demo/receiver geometry:

- New York
- Boston
- Philadelphia
- Washington
- Buffalo

### Why this is the best first choice

This is the best first benchmark because it aligns with the project’s current operating assumptions:

1. the receiver model and demo scenario are already built around this footprint
2. the map bounds are already defined in code
3. it avoids inventing a new benchmark geography before the first workflow is proven
4. it gives you a dense, familiar corridor where a reference comparison is easier to interpret

Current scenario source:
- [src/demo_scenarios.py](/Users/jeremicarose/Downloads/mlat-system%202/src/demo_scenarios.py:1)

Current demo map bounds:

- `north`: `43.25`
- `south`: `38.55`
- `east`: `-70.6`
- `west`: `-79.2`

---

## Benchmark goal

The goal of the first benchmark is **not** to prove market superiority.

The goal is to prove that the workflow works and produce the first real external evidence for:

- accuracy
- completeness
- freshness context
- geographic reliability framing

---

## Scope of the first run

### Region

Use the Northeast corridor bounds:

```text
lamin=38.55
lomin=-79.2
lamax=43.25
lomax=-70.6
```

### Time window

Use a **short, clearly bounded, recent time window** first.

Recommended first run:

- one current or near-current snapshot from OpenSky
- one matching MLAT export window from your DB

This first run is about validating the pipeline, not yet building a publication-grade benchmark set.

### Why not start with a long window?

Because the first benchmark should answer:

> can we export, fetch, compare, and interpret the result correctly?

A long window adds operational complexity before the benchmark pipeline itself is proven.

---

## Preconditions

Before running the first benchmark, make sure:

1. `mlat-processor` has written recent positions into the SQLite DB
2. the benchmark region and time correspond to actual data in your DB
3. OpenSky access is available
4. you understand whether the positions in the DB are:
   - hybrid/demo positions
   - or real live positions

### Important warning

If the DB currently contains only:

- demo replay positions
- or synthetic positions

then the first benchmark is useful for **pipeline validation**, but **not yet valid as a commercial quality proof**.

That distinction must stay explicit.

---

## Exact first-benchmark workflow

### Step 1. Export MLAT positions

```bash
python3 scripts/export_positions_for_benchmark.py \
  --db data/mlat_data.db \
  --output benchmark/mlat.jsonl \
  --seconds 3600
```

This exports the last hour of positions from your MLAT DB.

### Step 2. Fetch OpenSky reference data

Authenticated version:

```bash
export OPENSKY_CLIENT_ID=your_client_id
export OPENSKY_CLIENT_SECRET=your_client_secret

python3 scripts/fetch_opensky_reference.py \
  --output benchmark/reference.jsonl \
  --time 1710000000 \
  --lamin 38.55 \
  --lomin -79.2 \
  --lamax 43.25 \
  --lomax -70.6
```

Anonymous version for a quick current snapshot:

```bash
python3 scripts/fetch_opensky_reference.py \
  --anonymous \
  --output benchmark/reference.jsonl \
  --lamin 38.55 \
  --lomin -79.2 \
  --lamax 43.25 \
  --lomax -70.6
```

### Step 3. Compare

```bash
python3 scripts/benchmark_mlat_against_reference.py \
  --mlat benchmark/mlat.jsonl \
  --reference benchmark/reference.jsonl \
  --runtime-snapshot benchmark/readiness.json \
  --reference-source OpenSky \
  --region "Northeast corridor" \
  --data-provenance live \
  --output benchmark/latest.json
```

### Step 4. Write the result

Use:
- [docs/BENCHMARK_REPORT_TEMPLATE.md](/Users/jeremicarose/Downloads/mlat-system%202/docs/BENCHMARK_REPORT_TEMPLATE.md:1)

Document:

- matched record count
- coverage ratio
- median horizontal error
- p95 horizontal error
- median altitude error
- p95 altitude error

The generated artifact is served at `/api/benchmark/latest` and displayed on
`/app/analytics.html`. See [GRANT_EVIDENCE_RUNBOOK.md](GRANT_EVIDENCE_RUNBOOK.md)
for the full receiver-registration-to-public-report sequence.

---

## What a successful first benchmark looks like

A successful first benchmark is not:

- “we are already better than FlightRadar24”

A successful first benchmark is:

1. the export and reference fetch both work
2. record matching succeeds
3. you get non-zero matched records
4. you get interpretable error and coverage numbers
5. you can identify where the workflow still needs refinement

That is enough to move from:

- architecture claims

to:

- first external evidence

---

## How to interpret the first results

### If matched record count is low

Possible reasons:

- wrong time alignment
- aircraft IDs not lining up
- low overlap between MLAT output and reference snapshot
- DB contains too few relevant positions

### If horizontal error is very high

Possible reasons:

- demo/synthetic positions are being benchmarked
- timing mismatch between datasets
- wrong aircraft matching
- poor solve quality

### If coverage ratio is low

Possible reasons:

- the system is missing aircraft
- the comparison window is wrong
- the system only has a small or synthetic traffic set

---

## What this first benchmark does **not** prove

Even if it runs successfully, the first benchmark does **not** prove:

- more accurate than incumbents
- more complete than incumbents
- cheaper than incumbents
- faster than incumbents
- better coverage than incumbents
- better analytics than incumbents

It proves only:

> the project can now compare itself to an external reference source in a structured way.

That is the correct first milestone.

---

## Next benchmark after the first one

Once the first Northeast benchmark runs successfully, the next step should be:

### A repeated-window benchmark

Run the same benchmark:

- across multiple times of day
- with more than one snapshot
- ideally with real live positions rather than replay/synthetic positions

That is where the project begins moving from:

- proof of workflow

to:

- proof of product quality
