# Operational Benchmarks

Generated: `2026-07-20T17:02:00.228224Z`  
Commit: `34b7567e276ce9f64f4873c20438ee3413682c8f`  
Worktree dirty: `true`  
Provenance: `local_non_live_baseline`  
Live data: `false`

These are reproducible operational baselines, not MLAT accuracy claims. Accuracy is published separately through the external reference benchmark.

| Measurement | Median | P95 | Sample |
| --- | ---: | ---: | ---: |
| Receiver database lookup | 0.091 ms | 0.165 ms | 100 |
| SQLite position insert | 0.133 ms | 0.273 ms | 250 |
| Health API latency | 42.603 ms | 149.310 ms | 50 |

API throughput: `139.4 requests/s` at concurrency `10`.  
Successful API requests: `100.00%`.  
Benchmark process peak RSS: `25.6 MB`.

Reproduce with:

```bash
python3 scripts/benchmark_operational_performance.py --api-base http://127.0.0.1:5057
```
