# File Disposition Ledger

Generated: 2026-08-05

This ledger is the exhaustive version-controlled transition from the pre-audit
tree at `ba0f87f` to the reorganized repository. A previous tracked path that
changed location is listed in **Move And Rename**, a removed path in **Delete**,
and a same-path retention in **Update** or **Keep**. Every final repository path
is listed once in **Update** or **Keep**. Ignored operator state is separate
because it is not repository source.

Actions:

- **DELETE**: remove from the active tree; Git history remains the archive.
- **MOVE**: retain behavior under a clearer ownership path.
- **RENAME**: retain or merge behavior under a new authoritative name.
- **UPDATE**: retain as an authority but rewrite for the current implementation.
- **KEEP**: retain without a disposition concern.
- **ARCHIVE**: keep outside Git only when an operator still needs private state.
- **NEEDS REVIEW**: owner decision required before local deletion.

## Summary

| Action | Count |
|---|---:|
| MOVE / RENAME | 103 |
| DELETE | 60 |
| UPDATE | 47 |
| KEEP | 236 |
| Final repository paths | 283 |

## Move And Rename

| Action | Previous path | Authoritative path |
|---|---|---|
| RENAME | `benchmark/BENCHMARKS.md` | `docs/reference/mlat/BENCHMARKING.md` |
| MOVE | `benchmark/fixtures/reproducible-mlat.jsonl` | `reference/mlat/benchmarks/fixtures/reproducible-mlat.jsonl` |
| MOVE | `benchmark/fixtures/reproducible-readiness.json` | `reference/mlat/benchmarks/fixtures/reproducible-readiness.json` |
| MOVE | `benchmark/fixtures/reproducible-reference.jsonl` | `reference/mlat/benchmarks/fixtures/reproducible-reference.jsonl` |
| RENAME | `benchmark/performance-latest.json` | `evidence/mlat-reference/experimental/performance-local-simulation.json` |
| RENAME | `benchmark/reliability-latest.json` | `evidence/mlat-reference/experimental/reliability-local-simulation.json` |
| MOVE | `benchmark/reproducible/accuracy.json` | `evidence/mlat-reference/reproducible-benchmark-v1/accuracy.json` |
| MOVE | `benchmark/reproducible/checksums.sha256` | `evidence/mlat-reference/reproducible-benchmark-v1/checksums.sha256` |
| MOVE | `benchmark/reproducible/inputs/mlat.jsonl` | `evidence/mlat-reference/reproducible-benchmark-v1/inputs/mlat.jsonl` |
| MOVE | `benchmark/reproducible/inputs/readiness.json` | `evidence/mlat-reference/reproducible-benchmark-v1/inputs/readiness.json` |
| MOVE | `benchmark/reproducible/inputs/reference.jsonl` | `evidence/mlat-reference/reproducible-benchmark-v1/inputs/reference.jsonl` |
| MOVE | `benchmark/reproducible/manifest.json` | `evidence/mlat-reference/reproducible-benchmark-v1/manifest.json` |
| MOVE | `benchmark/reproducible/source/benchmark_mlat_against_reference.py` | `evidence/mlat-reference/reproducible-benchmark-v1/source/benchmark_mlat_against_reference.py` |
| MOVE | `benchmark/reproducible/source/Dockerfile` | `evidence/mlat-reference/reproducible-benchmark-v1/source/Dockerfile` |
| MOVE | `benchmark/reproducible/source/pyproject.toml` | `evidence/mlat-reference/reproducible-benchmark-v1/source/pyproject.toml` |
| MOVE | `benchmark/reproducible/source/python-version.txt` | `evidence/mlat-reference/reproducible-benchmark-v1/source/python-version.txt` |
| MOVE | `benchmark/reproducible/source/reproducibility-workflow.yml` | `evidence/mlat-reference/reproducible-benchmark-v1/source/reproducibility-workflow.yml` |
| MOVE | `benchmark/reproducible/source/requirements-build.in` | `evidence/mlat-reference/reproducible-benchmark-v1/source/requirements-build.in` |
| MOVE | `benchmark/reproducible/source/requirements-dev.lock` | `evidence/mlat-reference/reproducible-benchmark-v1/source/requirements-dev.lock` |
| MOVE | `benchmark/reproducible/source/requirements.lock` | `evidence/mlat-reference/reproducible-benchmark-v1/source/requirements.lock` |
| MOVE | `benchmark/reproducible/source/run_reproducible_benchmark.py` | `evidence/mlat-reference/reproducible-benchmark-v1/source/run_reproducible_benchmark.py` |
| MOVE | `contracts/receiver-registry/.cargo/config.toml` | `contracts/registry-v2/.cargo/config.toml` |
| MOVE | `contracts/receiver-registry/Cargo.lock` | `contracts/registry-v2/Cargo.lock` |
| MOVE | `contracts/receiver-registry/Cargo.toml` | `contracts/registry-v2/Cargo.toml` |
| MOVE | `contracts/receiver-registry/Makefile` | `contracts/registry-v2/Makefile` |
| MOVE | `contracts/receiver-registry/README.md` | `contracts/registry-v2/README.md` |
| MOVE | `contracts/receiver-registry/rust-toolchain.toml` | `contracts/registry-v2/rust-toolchain.toml` |
| MOVE | `contracts/receiver-registry/src/entry.rs` | `contracts/registry-v2/src/entry.rs` |
| MOVE | `contracts/receiver-registry/src/error.rs` | `contracts/registry-v2/src/error.rs` |
| MOVE | `contracts/receiver-registry/src/lib.rs` | `contracts/registry-v2/src/lib.rs` |
| MOVE | `contracts/receiver-registry/src/main.rs` | `contracts/registry-v2/src/main.rs` |
| MOVE | `contracts/receiver-registry/src/record.rs` | `contracts/registry-v2/src/record.rs` |
| MOVE | `contracts/receiver-registry/tests/lifecycle.rs` | `contracts/registry-v2/tests/lifecycle.rs` |
| RENAME | `docs/BENCHMARK_DATA_FORMAT.md` | `docs/reference/mlat/BENCHMARKING.md` |
| RENAME | `docs/BENCHMARK_REPORT_TEMPLATE.md` | `docs/reference/mlat/BENCHMARKING.md` |
| RENAME | `docs/CKB_INTEGRATION_GUIDE.md` | `docs/registry/INTEGRATION.md` |
| RENAME | `docs/MULTI_RECEIVER_BEAST_BRIDGE_CONFIG.example.json` | `reference/mlat/config/beast-receivers.example.json` |
| RENAME | `docs/MULTI_RECEIVER_RUNTIME.md` | `docs/reference/mlat/LIVE_INGEST.md` |
| RENAME | `docs/READINESS_BENCHMARK.md` | `docs/reference/mlat/BENCHMARKING.md` |
| RENAME | `docs/READSB_BEAST_JSONL_MAPPING.md` | `docs/reference/mlat/BEAST_TIMING.md` |
| RENAME | `docs/REGISTRY_V2_SECURITY_REVIEW_REQUEST.md` | `docs/registry/SECURITY_REVIEW_REQUEST.md` |
| MOVE | `docs/REPRODUCIBILITY.md` | `REPRODUCIBILITY.md` |
| MOVE | `scripts/apply_receiver_type_script.py` | `tools/registry/apply_receiver_type_script.py` |
| MOVE | `scripts/beast_tcp_adapter.py` | `tools/mlat/beast_tcp_adapter.py` |
| MOVE | `scripts/benchmark_mlat_against_reference.py` | `tools/mlat/benchmark_mlat_against_reference.py` |
| MOVE | `scripts/benchmark_operational_performance.py` | `tools/mlat/benchmark_operational_performance.py` |
| MOVE | `scripts/bridge_adapter.py` | `tools/mlat/bridge_adapter.py` |
| MOVE | `scripts/capture_grant_evidence.py` | `tools/mlat/capture_grant_evidence.py` |
| MOVE | `scripts/capture_registry_v2_local_ci.py` | `tools/registry/capture_registry_v2_local_ci.py` |
| MOVE | `scripts/capture_reliability_window.py` | `tools/mlat/capture_reliability_window.py` |
| MOVE | `scripts/check_live_ingest_readiness.py` | `tools/mlat/check_live_ingest_readiness.py` |
| MOVE | `scripts/export_positions_for_benchmark.py` | `tools/mlat/export_positions_for_benchmark.py` |
| MOVE | `scripts/fetch_opensky_reference.py` | `tools/mlat/fetch_opensky_reference.py` |
| MOVE | `scripts/generate_receiver_registration_tx_template.py` | `tools/registry/generate_receiver_registration_tx_template.py` |
| MOVE | `scripts/generate_receiver_registry_deploy_config.py` | `tools/registry/generate_receiver_registry_deploy_config.py` |
| MOVE | `scripts/generate_receiver_registry_record.py` | `tools/registry/generate_receiver_registry_record.py` |
| MOVE | `scripts/generate_registry_v2_checksums.py` | `tools/registry/generate_registry_v2_checksums.py` |
| MOVE | `scripts/multi_receiver_beast_bridge.py` | `tools/mlat/multi_receiver_beast_bridge.py` |
| MOVE | `scripts/print_receiver_registration_commands.py` | `tools/registry/print_receiver_registration_commands.py` |
| MOVE | `scripts/print_receiver_registration_instructions.py` | `tools/registry/print_receiver_registration_instructions.py` |
| MOVE | `scripts/registry_v2_testnet_lifecycle.py` | `tools/registry/registry_v2_testnet_lifecycle.py` |
| MOVE | `scripts/run_reproducible_benchmark.py` | `tools/mlat/run_reproducible_benchmark.py` |
| MOVE | `scripts/sample_live_bridge.py` | `tools/mlat/sample_live_bridge.py` |
| MOVE | `scripts/update_env_type_hash.py` | `tools/registry/update_env_type_hash.py` |
| MOVE | `scripts/verify_registry_v2_evidence.py` | `tools/registry/verify_registry_v2_evidence.py` |
| MOVE | `src/api/__init__.py` | `src/mlat_reference/api/__init__.py` |
| MOVE | `src/api/rest_api.py` | `src/mlat_reference/api/rest_api.py` |
| MOVE | `src/correlation/__init__.py` | `src/mlat_reference/correlation/__init__.py` |
| MOVE | `src/correlation/correlator.py` | `src/mlat_reference/correlation/correlator.py` |
| MOVE | `src/database/__init__.py` | `src/mlat_reference/database/__init__.py` |
| RENAME | `src/database/mlat_db.py` | `src/mlat_reference/database/database.py` |
| RENAME | `src/demo_scenarios.py` | `src/mlat_reference/demo.py` |
| RENAME | `src/mlat_runtime.py` | `src/mlat_reference/base.py` |
| MOVE | `src/mlat/__init__.py` | `src/mlat_reference/solver/__init__.py` |
| RENAME | `src/mlat/robust_solver.py` | `src/mlat_reference/solver/robust.py` |
| MOVE | `src/network/__init__.py` | `src/mlat_reference/ingest/__init__.py` |
| RENAME | `src/network/ckb_client.py` | `src/mlat_reference/ingest/client.py` |
| RENAME | `src/network/ckb_discovery.py` | `src/ckb_registry/discovery.py` |
| MOVE | `src/network/feed_transports.py` | `src/mlat_reference/ingest/feed_transports.py` |
| RENAME | `src/network/receiver_registry.py` | `src/ckb_registry/record.py` |
| RENAME | `src/production_main.py` | `src/mlat_reference/runtime.py` |
| RENAME | `src/runtime_config.py` | `src/mlat_reference/config.py` |
| MOVE | `tests/test_api.py` | `tests/mlat/test_api.py` |
| MOVE | `tests/test_apply_receiver_type_script.py` | `tests/registry/test_apply_receiver_type_script.py` |
| MOVE | `tests/test_beast_tcp_adapter.py` | `tests/mlat/test_beast_tcp_adapter.py` |
| MOVE | `tests/test_benchmark_script.py` | `tests/mlat/test_benchmark_script.py` |
| MOVE | `tests/test_ckb_client.py` | `tests/registry/test_ckb_client.py` |
| MOVE | `tests/test_ckb_registry.py` | `tests/registry/test_ckb_registry.py` |
| MOVE | `tests/test_contract_layout.py` | `tests/registry/test_contract_layout.py` |
| MOVE | `tests/test_correlator.py` | `tests/mlat/test_correlator.py` |
| MOVE | `tests/test_database.py` | `tests/mlat/test_database.py` |
| MOVE | `tests/test_deploy_helpers.py` | `tests/registry/test_deploy_helpers.py` |
| MOVE | `tests/test_feed_transports.py` | `tests/mlat/test_feed_transports.py` |
| MOVE | `tests/test_live_ingest_readiness.py` | `tests/mlat/test_live_ingest_readiness.py` |
| MOVE | `tests/test_operational_evidence.py` | `tests/mlat/test_operational_evidence.py` |
| MOVE | `tests/test_receiver_record_generator.py` | `tests/registry/test_receiver_record_generator.py` |
| MOVE | `tests/test_receiver_registration_commands.py` | `tests/registry/test_receiver_registration_commands.py` |
| MOVE | `tests/test_receiver_registration_template.py` | `tests/registry/test_receiver_registration_template.py` |
| MOVE | `tests/test_registry_v2_evidence_verifier.py` | `tests/registry/test_registry_v2_evidence_verifier.py` |
| MOVE | `tests/test_registry_v2_lifecycle_tool.py` | `tests/registry/test_registry_v2_lifecycle_tool.py` |
| MOVE | `tests/test_reproducible_benchmark.py` | `tests/mlat/test_reproducible_benchmark.py` |
| MOVE | `tests/test_runtime_guardrails.py` | `tests/mlat/test_runtime_guardrails.py` |
| MOVE | `tests/test_solver.py` | `tests/mlat/test_solver.py` |

## Delete

These paths contradicted the current product, duplicated an authority, or were
generated/misleading output without durable evidence value.

- `benchmark/mlat.jsonl`
- `docs/DEPLOYMENT_GUIDE.md`
- `docs/GETTING_STARTED.md`
- `docs/GRANT_DEMO_SCRIPT.md`
- `docs/GRANT_EVIDENCE_RUNBOOK.md`
- `docs/INTEGRATION_GUIDE.md`
- `docs/PROJECT_SUMMARY.md`
- `docs/PUBLIC_PROGRESS_UPDATE.md`
- `docs/archive/project-history/FIRST_BENCHMARK_PLAN.md`
- `docs/archive/project-history/FRONTEND_REFACTOR_PLAN.md`
- `docs/archive/project-history/PROJECT_AUDIT_PROPOSAL.md`
- `docs/archive/project-history/WEEKLY_STATUS_REPORT.md`
- `docs/archive/project-history/grant-outline.md`
- `docs/archive/project-history/informal-review-issue.md`
- `docs/archive/project-history/nervos-talk-post.md`
- `docs/archive/project-history/spark-proposal-draft.md`
- `docs/archive/project-history/weekly-reports/week-13-dev-log.md`
- `docs/archive/project-history/weekly-reports/week-14-dev-log.md`
- `docs/archive/project-history/weekly-reports/week-15-dev-log.md`
- `docs/archive/project-history/weekly-reports/week-16-dev-log.md`
- `docs/archive/root-history/IMPLEMENTATION_COMPLETE.md`
- `docs/archive/root-history/PRODUCT.md`
- `docs/archive/root-history/README_FINAL.md`
- `examples/bridge.py`
- `examples/simple_demo.py`
- `examples/simulation_demo.py`
- `nginx.conf`
- `src/__init__.py`
- `src/main.py`
- `src/mlat/enhanced_solver.py`
- `src/mlat/solver.py`
- `src/network/neuron_client.py`
- `src/visualization/app-agent.js`
- `src/visualization/app-aircraft.js`
- `src/visualization/app-analytics.js`
- `src/visualization/app-overview.js`
- `src/visualization/app-payments.js`
- `src/visualization/app-pipeline.js`
- `src/visualization/app-receivers.js`
- `src/visualization/app-settings.js`
- `src/visualization/app-shell.css`
- `src/visualization/app-shell.html`
- `src/visualization/app-shell.js`
- `src/visualization/app/agent.html`
- `src/visualization/app/aircraft.html`
- `src/visualization/app/analytics.html`
- `src/visualization/app/localization.html`
- `src/visualization/app/overview.html`
- `src/visualization/app/payments.html`
- `src/visualization/app/pipeline.html`
- `src/visualization/app/receivers.html`
- `src/visualization/app/settings.html`
- `src/visualization/dashboard.html`
- `src/visualization/dashboard.js`
- `src/visualization/index.html`
- `src/visualization/styles.css`
- `src/visualization/vendor/leaflet.css`
- `src/visualization/vendor/leaflet.js`
- `src/visualization/vendor/socket.io.min.js`
- `start.sh`

## Update

- `.env.example`
- `.flake8`
- `.github/CODEOWNERS`
- `.github/workflows/registry-v2.yml`
- `.github/workflows/release.yml`
- `.github/workflows/reproducibility.yml`
- `.github/workflows/security.yml`
- `.gitignore`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `CODE_OF_CONDUCT.md`
- `CONTEXT.md`
- `CONTRIBUTING.md`
- `DEPLOYMENT.md`
- `Dockerfile`
- `EVIDENCE.md`
- `MAINTAINERS.md`
- `README.md`
- `RELEASE.md`
- `REPRODUCIBILITY.md`
- `ROADMAP.md`
- `SECURITY.md`
- `contracts/README.md`
- `docker-compose.yml`
- `docs/PROJECT_STATUS.md`
- `docs/README.md`
- `docs/adr/0001-receiver-identity-and-lifecycle.md`
- `docs/adr/0002-registry-primary-mlat-reference.md`
- `docs/archive/README.md`
- `docs/audit/FILE_DISPOSITION.md`
- `docs/audit/REPOSITORY_AUDIT.md`
- `docs/reference/mlat/BEAST_TIMING.md`
- `docs/reference/mlat/BENCHMARKING.md`
- `docs/reference/mlat/DESIGN_SYSTEM.md`
- `docs/reference/mlat/FIELD_TRIAL.md`
- `docs/reference/mlat/LIVE_INGEST.md`
- `docs/reference/mlat/OPERATOR_CONSOLE.md`
- `docs/reference/mlat/SOLVER_AND_TIMING.md`
- `docs/registry/INTEGRATION.md`
- `docs/registry/SECURITY_REVIEW_REQUEST.md`
- `pyproject.toml`
- `render-entrypoint.sh`
- `render.yaml`
- `requirements.txt`
- `run-demo.sh`
- `run-live.sh`
- `tests/conftest.py`

## Keep

- `.impeccable/design.json`
- `.impeccable/live/config.json`
- `.nvmrc`
- `.python-version`
- `contracts/registry-v2/.cargo/config.toml`
- `contracts/registry-v2/Cargo.lock`
- `contracts/registry-v2/Cargo.toml`
- `contracts/registry-v2/Makefile`
- `contracts/registry-v2/README.md`
- `contracts/registry-v2/rust-toolchain.toml`
- `contracts/registry-v2/src/entry.rs`
- `contracts/registry-v2/src/error.rs`
- `contracts/registry-v2/src/lib.rs`
- `contracts/registry-v2/src/main.rs`
- `contracts/registry-v2/src/record.rs`
- `contracts/registry-v2/tests/lifecycle.rs`
- `evidence/README.md`
- `evidence/mlat-reference/README.md`
- `evidence/mlat-reference/experimental/README.md`
- `evidence/mlat-reference/experimental/performance-local-simulation.json`
- `evidence/mlat-reference/experimental/reliability-local-simulation.json`
- `evidence/mlat-reference/reproducible-benchmark-v1/accuracy.json`
- `evidence/mlat-reference/reproducible-benchmark-v1/checksums.sha256`
- `evidence/mlat-reference/reproducible-benchmark-v1/inputs/mlat.jsonl`
- `evidence/mlat-reference/reproducible-benchmark-v1/inputs/readiness.json`
- `evidence/mlat-reference/reproducible-benchmark-v1/inputs/reference.jsonl`
- `evidence/mlat-reference/reproducible-benchmark-v1/manifest.json`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/Dockerfile`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/benchmark_mlat_against_reference.py`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/pyproject.toml`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/python-version.txt`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/reproducibility-workflow.yml`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/requirements-build.in`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/requirements-dev.lock`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/requirements.lock`
- `evidence/mlat-reference/reproducible-benchmark-v1/source/run_reproducible_benchmark.py`
- `evidence/mlat-reference/ui-review-2026-08-05/checksums.sha256`
- `evidence/mlat-reference/ui-review-2026-08-05/manifest.json`
- `evidence/mlat-reference/ui-review-2026-08-05/report.md`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/aircraft-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/command-palette.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/environment-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/initial.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/live-map-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/metrics-corrected.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/metrics-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/overview-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/pipeline-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/receivers-desktop.png`
- `evidence/mlat-reference/ui-review-2026-08-05/screenshots/settings-desktop.png`
- `evidence/registry-v2-testnet-2026-07-30-final/README.md`
- `evidence/registry-v2-testnet-2026-07-30-final/api/create-receivers.json`
- `evidence/registry-v2-testnet-2026-07-30-final/api/revoke-receivers.json`
- `evidence/registry-v2-testnet-2026-07-30-final/api/transfer-receivers.json`
- `evidence/registry-v2-testnet-2026-07-30-final/api/update-receivers.json`
- `evidence/registry-v2-testnet-2026-07-30-final/checksums.sha256`
- `evidence/registry-v2-testnet-2026-07-30-final/ci/github.json`
- `evidence/registry-v2-testnet-2026-07-30-final/ci/local.json`
- `evidence/registry-v2-testnet-2026-07-30-final/contract/receiver-registry`
- `evidence/registry-v2-testnet-2026-07-30-final/contract/receiver-registry-local-darwin`
- `evidence/registry-v2-testnet-2026-07-30-final/deployment/deployment-info.json`
- `evidence/registry-v2-testnet-2026-07-30-final/deployment/deployment.toml`
- `evidence/registry-v2-testnet-2026-07-30-final/deployment/lifecycle-funding.bin`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/create-adapter.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/create-indexer.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/revoke-adapter.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/revoke-indexer.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/transfer-adapter.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/transfer-indexer.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/update-adapter.json`
- `evidence/registry-v2-testnet-2026-07-30-final/discovery/update-indexer.json`
- `evidence/registry-v2-testnet-2026-07-30-final/manifest.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-burn.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-duplicate-output.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-forged-identity.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-label-mutation.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-resurrection.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-sequence-jump.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/attack-tombstone-burn.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/create-submission.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/revoke-submission.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/transfer-submission.json`
- `evidence/registry-v2-testnet-2026-07-30-final/responses/update-submission.json`
- `evidence/registry-v2-testnet-2026-07-30-final/rpc/create-transaction.json`
- `evidence/registry-v2-testnet-2026-07-30-final/rpc/deployment-transaction.json`
- `evidence/registry-v2-testnet-2026-07-30-final/rpc/revoke-transaction.json`
- `evidence/registry-v2-testnet-2026-07-30-final/rpc/transfer-transaction.json`
- `evidence/registry-v2-testnet-2026-07-30-final/rpc/update-transaction.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-burn.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-duplicate-output.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-forged-identity.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-label-mutation.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-resurrection.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-sequence-jump.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/attack-tombstone-burn.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/create.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/revoke.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/transfer.json`
- `evidence/registry-v2-testnet-2026-07-30-final/transactions/update.json`
- `evidence/registry-v2-testnet-2026-07-30-final/verification-live.json`
- `evidence/registry-v2-testnet-2026-07-30-final/verification-offline.json`
- `reference/mlat/README.md`
- `reference/mlat/benchmarks/fixtures/reproducible-mlat.jsonl`
- `reference/mlat/benchmarks/fixtures/reproducible-readiness.json`
- `reference/mlat/benchmarks/fixtures/reproducible-reference.jsonl`
- `reference/mlat/config/beast-receivers.example.json`
- `reference/mlat/frontend/.dockerignore`
- `reference/mlat/frontend/Dockerfile`
- `reference/mlat/frontend/app/app/aircraft/page.tsx`
- `reference/mlat/frontend/app/app/analytics/page.tsx`
- `reference/mlat/frontend/app/app/environment/page.tsx`
- `reference/mlat/frontend/app/app/error.tsx`
- `reference/mlat/frontend/app/app/loading.tsx`
- `reference/mlat/frontend/app/app/localization/page.tsx`
- `reference/mlat/frontend/app/app/metrics/page.tsx`
- `reference/mlat/frontend/app/app/overview/page.tsx`
- `reference/mlat/frontend/app/app/page.tsx`
- `reference/mlat/frontend/app/app/pipeline/page.tsx`
- `reference/mlat/frontend/app/app/receivers/page.tsx`
- `reference/mlat/frontend/app/app/settings/page.tsx`
- `reference/mlat/frontend/app/dashboard/page.tsx`
- `reference/mlat/frontend/app/globals.css`
- `reference/mlat/frontend/app/layout.tsx`
- `reference/mlat/frontend/app/page.tsx`
- `reference/mlat/frontend/components.json`
- `reference/mlat/frontend/components/activity-feed.tsx`
- `reference/mlat/frontend/components/airspace-map.tsx`
- `reference/mlat/frontend/components/app-shell.tsx`
- `reference/mlat/frontend/components/charts.tsx`
- `reference/mlat/frontend/components/lazy-airspace-map.tsx`
- `reference/mlat/frontend/components/lazy-charts.tsx`
- `reference/mlat/frontend/components/operations-ui.tsx`
- `reference/mlat/frontend/components/pages/aircraft-page.tsx`
- `reference/mlat/frontend/components/pages/environment-page.tsx`
- `reference/mlat/frontend/components/pages/live-map-page.tsx`
- `reference/mlat/frontend/components/pages/metrics-page.tsx`
- `reference/mlat/frontend/components/pages/overview-page.tsx`
- `reference/mlat/frontend/components/pages/pipeline-page.tsx`
- `reference/mlat/frontend/components/pages/receivers-page.tsx`
- `reference/mlat/frontend/components/pages/settings-page.tsx`
- `reference/mlat/frontend/components/providers.tsx`
- `reference/mlat/frontend/components/system-flow.tsx`
- `reference/mlat/frontend/components/ui/button.tsx`
- `reference/mlat/frontend/components/ui/command-palette.tsx`
- `reference/mlat/frontend/components/ui/data-grid.tsx`
- `reference/mlat/frontend/components/ui/notification-center.tsx`
- `reference/mlat/frontend/components/ui/relative-time.tsx`
- `reference/mlat/frontend/components/ui/status-chip.tsx`
- `reference/mlat/frontend/components/ui/surface.tsx`
- `reference/mlat/frontend/components/ui/tooltip.tsx`
- `reference/mlat/frontend/lib/api.ts`
- `reference/mlat/frontend/lib/format.ts`
- `reference/mlat/frontend/lib/operator-store.ts`
- `reference/mlat/frontend/lib/routes.ts`
- `reference/mlat/frontend/lib/types.ts`
- `reference/mlat/frontend/lib/utils.ts`
- `reference/mlat/frontend/next-env.d.ts`
- `reference/mlat/frontend/next.config.mjs`
- `reference/mlat/frontend/package-lock.json`
- `reference/mlat/frontend/package.json`
- `reference/mlat/frontend/postcss.config.mjs`
- `reference/mlat/frontend/tsconfig.json`
- `requirements-build.in`
- `requirements-dev.lock`
- `requirements.lock`
- `src/ckb_registry/__init__.py`
- `src/ckb_registry/discovery.py`
- `src/ckb_registry/record.py`
- `src/mlat_reference/__init__.py`
- `src/mlat_reference/api/__init__.py`
- `src/mlat_reference/api/rest_api.py`
- `src/mlat_reference/base.py`
- `src/mlat_reference/config.py`
- `src/mlat_reference/correlation/__init__.py`
- `src/mlat_reference/correlation/correlator.py`
- `src/mlat_reference/database/__init__.py`
- `src/mlat_reference/database/database.py`
- `src/mlat_reference/demo.py`
- `src/mlat_reference/ingest/__init__.py`
- `src/mlat_reference/ingest/client.py`
- `src/mlat_reference/ingest/feed_transports.py`
- `src/mlat_reference/runtime.py`
- `src/mlat_reference/solver/__init__.py`
- `src/mlat_reference/solver/robust.py`
- `tests/mlat/test_api.py`
- `tests/mlat/test_beast_tcp_adapter.py`
- `tests/mlat/test_benchmark_script.py`
- `tests/mlat/test_correlator.py`
- `tests/mlat/test_database.py`
- `tests/mlat/test_feed_transports.py`
- `tests/mlat/test_live_ingest_readiness.py`
- `tests/mlat/test_operational_evidence.py`
- `tests/mlat/test_production_mlat_pipeline.py`
- `tests/mlat/test_receiver_config.py`
- `tests/mlat/test_reproducible_benchmark.py`
- `tests/mlat/test_runtime_guardrails.py`
- `tests/mlat/test_solver.py`
- `tests/registry/test_apply_receiver_type_script.py`
- `tests/registry/test_ckb_client.py`
- `tests/registry/test_ckb_registry.py`
- `tests/registry/test_contract_layout.py`
- `tests/registry/test_deploy_helpers.py`
- `tests/registry/test_receiver_record_generator.py`
- `tests/registry/test_receiver_registration_commands.py`
- `tests/registry/test_receiver_registration_template.py`
- `tests/registry/test_registry_v2_evidence_verifier.py`
- `tests/registry/test_registry_v2_lifecycle_tool.py`
- `tools/__init__.py`
- `tools/check_documentation.py`
- `tools/mlat/__init__.py`
- `tools/mlat/beast_tcp_adapter.py`
- `tools/mlat/benchmark_mlat_against_reference.py`
- `tools/mlat/benchmark_operational_performance.py`
- `tools/mlat/bridge_adapter.py`
- `tools/mlat/capture_grant_evidence.py`
- `tools/mlat/capture_reliability_window.py`
- `tools/mlat/check_live_ingest_readiness.py`
- `tools/mlat/export_positions_for_benchmark.py`
- `tools/mlat/fetch_opensky_reference.py`
- `tools/mlat/multi_receiver_beast_bridge.py`
- `tools/mlat/receiver_config.py`
- `tools/mlat/run_reproducible_benchmark.py`
- `tools/mlat/sample_live_bridge.py`
- `tools/mlat/verify_live_evidence.py`
- `tools/registry/__init__.py`
- `tools/registry/apply_receiver_type_script.py`
- `tools/registry/capture_registry_v2_local_ci.py`
- `tools/registry/generate_receiver_registration_tx_template.py`
- `tools/registry/generate_receiver_registry_deploy_config.py`
- `tools/registry/generate_receiver_registry_record.py`
- `tools/registry/generate_registry_v2_checksums.py`
- `tools/registry/print_receiver_registration_commands.py`
- `tools/registry/print_receiver_registration_instructions.py`
- `tools/registry/registry_v2_testnet_lifecycle.py`
- `tools/registry/update_env_type_hash.py`
- `tools/registry/verify_registry_v2_evidence.py`

## Ignored Local State

| Action | Local path | Reason |
|---|---|---|
| NEEDS REVIEW | `.env` | Local secrets/configuration; inspect privately and never commit. |
| NEEDS REVIEW | `ckb-cli/` | Modified nested upstream clone; confirm whether the local signer change matters, then replace it with a documented pinned install. |
| ARCHIVE | `deploy/` | Private operator scratch; canonical public deployment material is already in signed evidence. |
| ARCHIVE | `data/` | Private SQLite/runtime state only when diagnostics are still needed. |
| DELETE | `.pytest_cache/` | Generated test cache. |
| DELETE | `.venv/` | Reproducible local Python development environment. |
| DELETE | `**/__pycache__/` | Generated Python bytecode. |
| DELETE | `contracts/**/target/` | Generated Rust build output. |
| DELETE | `reference/mlat/frontend/.next/` | Generated Next.js build output. |
| DELETE | `reference/mlat/frontend/node_modules/` | Reproducible npm dependency installation. |
| DELETE | `reference/mlat/frontend/tsconfig.tsbuildinfo` | Generated TypeScript incremental build state. |
| DELETE | `logs/` | Run-local logs unless copied into a hashed evidence package. |

No ignored local path is evidence unless it is copied into a versioned,
manifested package under `evidence/`.
