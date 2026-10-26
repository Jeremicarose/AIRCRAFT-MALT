"""Explicit nested export schema; persistent JSON is not an export allowlist."""

import math
from typing import Any


def fields(value: object, names: tuple[str, ...]) -> dict:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for name in names:
        item = value.get(name)
        if item is None or isinstance(item, (str, bool, int)):
            result[name] = item[:500] if isinstance(item, str) else item
        elif isinstance(item, float) and math.isfinite(item):
            result[name] = item
    return result


def public_context(context: dict) -> dict:
    result = fields(
        context,
        (
            "data_provenance",
            "source_id",
            "source",
            "replay_status",
            "replay_run_id",
            "timestamp_context",
            "production_pipeline_validated",
            "event_count",
            "successful_solves",
            "failed_solves",
            "solver_sha256",
        ),
    )
    manifest = context.get("source_manifest", {})
    result["source_manifest"] = fields(
        manifest, ("schema_version", "source_id", "dataset", "license", "expected_event_count")
    )
    if isinstance(manifest, dict) and isinstance(manifest.get("files"), dict):
        result["source_manifest"]["files"] = {
            name: fields(manifest["files"].get(name), ("name", "sha256", "size_bytes"))
            for name in ("sensors", "measurements")
        }
    return result


def public_qualification(value: dict) -> dict:
    return fields(
        value,
        (
            "state",
            "scope",
            "historical_solver_eligible",
            "received_at",
            "source_timestamp_ns",
            "clock_uncertainty_ns",
            "maximum_clock_uncertainty_ns",
            "reason",
            "action",
            "data_provenance",
        ),
    )


def public_runtime(runtime: dict) -> dict:
    result = fields(
        runtime,
        (
            "total_signals",
            "successful_solves",
            "failed_solves",
            "storage_failures",
            "telemetry_fresh",
            "last_signal_age_s",
            "last_store_age_s",
            "correlation_dropped_signals",
        ),
    )
    result["observation_counts"] = fields(
        runtime.get("observation_counts"),
        (
            "accepted",
            "rejected",
            "quarantined",
            "correlated",
            "solver_qualified",
            "contributing",
            "geometry_rejected",
        ),
    )
    result["transport_rejections"] = fields(
        runtime.get("transport_rejections"),
        (
            "invalid_json_payload",
            "batch_limit",
            "invalid_record_type",
            "identity_or_frame_invalid",
            "invalid_timestamp_ns",
            "missing_or_invalid_timestamp",
            "invalid_clock_source",
        ),
    )
    records = runtime.get("observation_diagnostics")
    result["observation_diagnostics"] = (
        [
            fields(item, ("receiver_id", "reason", "disposition", "recorded_at"))
            for item in records[-100:]
        ]
        if isinstance(records, list)
        else []
    )
    return result
