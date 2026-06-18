# Readiness Benchmark

This file is the explicit benchmark surface for deciding whether the project is
commercially ready on the dimensions that matter most:

- quality
- latency / freshness
- reliability
- packaging

It also forces discipline around claims such as:

- more accurate
- more complete
- cheaper
- faster
- better coverage
- better analytics

Those claims are **not considered proven** until benchmark evidence exists.

---

## 1. Readiness Dimensions

### Quality

Measured internally today by:

- `quality_score`
- `quality_bucket`
- `uncertainty`
- `solver_residual_m`
- `receiver_count`
- `correlation_time_span_s`

Commercially credible only when combined with external comparison against
trusted reference tracks.

### Latency / Freshness

Measured internally today by:

- `avg_ingest_latency_ms`
- `avg_solve_latency_ms`
- `avg_store_latency_ms`
- `avg_api_latency_ms`
- `last_signal_age_s`
- `last_store_age_s`

The customer-facing metric is:

> how old is the position when the customer sees it?

### Reliability

Measured internally today by:

- runtime uptime
- signal freshness
- active receiver count
- failed solves
- rejected groups
- API health status

### Packaging

Measured by whether the product exposes:

- health endpoint
- positions endpoint
- track endpoint
- premium statistics endpoint
- quality metadata in the payload

Packaging is not just design polish. It is the product’s ability to expose its
value in a form a buyer can adopt.

---

## 2. Current Internal Signals

The project already has internal signals for:

- quality
- freshness
- reliability
- packaging

These are visible through:

- `/api/health`
- `/api/statistics`
- `/api/readiness`

What is **still missing** is external benchmark proof.

### Benchmarkability rule

Not all output is equally suitable for benchmarking.

If recent positions are produced by:

- `simulated_replay`
- synthetic traffic
- demo-only aircraft identities

then the dataset is useful for:

- pipeline validation
- UI validation
- storage and API validation

but **not** for real external benchmark claims.

The project should only treat output as benchmarkable when the recent position set
contains real aircraft identities and non-simulated solve provenance.

---

## 3. Claims That Are Still Unproven

The following claims must remain unproven until benchmark evidence is captured:

- more accurate than incumbents
- more complete than incumbents
- cheaper than incumbents
- faster than incumbents
- better coverage than incumbents
- better analytics than incumbents

Comparison set should include at least:

- FlightRadar24
- OpenSky
- ADS-B Exchange
- relevant commercial feeds
- any trusted local authority data where available

---

## 4. Minimum Internal Readiness Gates

These are suggested internal gates, not final commercial guarantees:

### Quality gate

- recent positions exist
- average quality score >= `0.65`
- average receiver count >= `4`
- benchmarkable output = `true`

### Freshness gate

- last stored position age <= `30s`

### Reliability gate

- signal freshness healthy
- at least `4` active receivers
- failed solves = `0` during current healthy window

### Packaging gate

- positions endpoint available
- track endpoint available
- health endpoint available
- quality fields exposed in payloads

---

## 5. Benchmark Table Template

| Dimension | Internal Metric | Current Status | External Comparator | Proven? |
|---|---|---|---|---|
| Quality | Avg quality score, uncertainty, residual | Instrumented | FlightRadar24 / OpenSky / ADS-B Exchange | No |
| Freshness | Ingest/solve/store/API latency | Instrumented | Commercial/live feeds | No |
| Reliability | Health, uptime, signal freshness | Instrumented | Hosted production services | No |
| Packaging | API/dashboard/quality fields | Instrumented | Commercial API products | Partially |
| Completeness | Coverage ratio | Not benchmarked | Trusted reference feeds | No |
| Cost | Buyer pricing comparison | Not benchmarked | Incumbent plans/feeds | No |
| Coverage | Geography-specific success | Not benchmarked | Competitor coverage areas | No |
| Analytics | Insight layer usefulness | Conceptual / partial | Competitor analytics products | No |

---

## 6. Immediate Recommendation

The project should currently say:

> We have internal instrumentation for quality, freshness, reliability, and packaging readiness, but we have not yet proven superiority against incumbents.

That is the honest and technically defensible position.
