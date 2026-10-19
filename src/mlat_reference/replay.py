"""Historical dataset adapter with honest, recorded limits at every stage.

The compact source is already grouped and has no raw frames. It must never be
fed into the live frame correlator with fabricated messages or clock evidence.
"""

import hashlib
import json
import logging
from pathlib import Path

from mlat_reference.benchmarks.compact_solver import load_compact_source
from mlat_reference.benchmarks.diagnostics import DiagnosticSolver
from mlat_reference.database.database import MLATDatabase
from mlat_reference.diagnostics import event
from mlat_reference.ingest.validation import integer_nanoseconds
from mlat_reference.solver.robust import SignalObservation

logger = logging.getLogger(__name__)


def replay_compact_dataset(database_path, sensors_path, measurements_path, source_manifest_path):
    sensors, rows, manifest = load_compact_source(
        sensors_path, measurements_path, source_manifest_path
    )
    solver_bytes = Path(__file__).with_name("solver").joinpath("robust.py").read_bytes()
    run_id = hashlib.sha256(
        Path(measurements_path).read_bytes() + Path(sensors_path).read_bytes() + solver_bytes
    ).hexdigest()[:24]
    source_id = manifest["source_id"]
    context = {
        "replay_status": "running",
        "replay_run_id": run_id,
        "source": manifest["dataset"] if "dataset" in manifest else source_id,
        "source_manifest": manifest,
        "timestamp_context": "Dataset-relative nanoseconds. UTC epoch is not supplied; timestamps are never rewritten to current time.",
        "production_pipeline_validated": False,
        "limitations": manifest["limitations"],
        "event_count": len(rows),
        "solver_sha256": hashlib.sha256(solver_bytes).hexdigest(),
    }
    database = MLATDatabase(str(database_path))
    database.connect()
    solved = 0
    failures = {}
    solver = DiagnosticSolver()
    try:
        database.bind_runtime_provenance("HISTORICAL_REPLAY", source_id, context)
        used = {
            str(serial)
            for row in rows
            for serial, _timestamp, _strength in json.loads(row["measurements"])
        }
        for serial in sorted(used):
            if serial not in sensors:
                raise ValueError("Historical receiver geometry is missing")
            receiver = sensors[serial]
            database.store_receiver(
                receiver.receiver_id,
                receiver.latitude,
                receiver.longitude,
                receiver.altitude,
                "historical",
                0,
                ["historical-timestamps"],
                data_source="historical_replay",
                receiver_label=f"Dataset receiver {serial}",
            )
            database.store_receiver_qualification(
                receiver.receiver_id,
                {
                    "state": "UNQUALIFIED",
                    "scope": "LIVE",
                    "historical_solver_eligible": True,
                    "reason": "No historical CKB identity, original frame, or per-observation clock uncertainty supplied.",
                    "action": "Use this receiver for the historical numerical benchmark only.",
                    "data_provenance": "HISTORICAL_REPLAY",
                },
            )

        for ordinal, row in enumerate(rows):
            observations = []
            raw = json.loads(row["measurements"])
            if len({str(item[0]) for item in raw}) != len(raw):
                raise ValueError("Historical event contains duplicate receivers")
            for serial, timestamp_ns, _strength in raw:
                if integer_nanoseconds(timestamp_ns) is None:
                    raise ValueError(
                        "Historical arrival timestamp is not a positive integer nanosecond count"
                    )
                receiver = sensors[str(serial)]
                observations.append(
                    SignalObservation(
                        receiver.receiver_id,
                        timestamp_ns / 1e9,
                        f"dataset-event:{row['id']}",
                        receiver,
                        timestamp_ns,
                    )
                )
            correlation_id = f"{run_id}:{row['id']}"
            geometry = [
                {
                    "receiver_id": item.receiver_id,
                    "latitude": item.receiver_position.latitude,
                    "longitude": item.receiver_position.longitude,
                    "altitude_m": item.receiver_position.altitude,
                }
                for item in observations
            ]
            result = {
                "event_id": row["id"],
                "ordinal": ordinal,
                "aircraft_dataset_id": row["aircraft"],
                "data_provenance": "HISTORICAL_REPLAY",
                "source_id": source_id,
                "correlation_id": correlation_id,
                "source_timestamp_ns": str(min(item.timestamp_ns for item in observations)),
                "source_time_seconds": float(row["timeAtServer"]),
                "receiver_geometry": geometry,
                "observations": [
                    {
                        "receiver_id": item.receiver_id,
                        "timestamp_ns": str(item.timestamp_ns),
                        "clock_uncertainty_ns": None,
                        "clock_source": "GPS according to upstream selection; not independently attested",
                    }
                    for item in observations
                ],
                "stages": [
                    {
                        "stage": "ingestion",
                        "status": "ACCEPTED",
                        "detail": "Read checksum-verified historical CSV observations.",
                    },
                    {
                        "stage": "validation",
                        "status": "ACCEPTED",
                        "detail": "Unique dataset identities, integer arrival timestamps and finite receiver geometry.",
                    },
                    {
                        "stage": "correlation",
                        "status": "PUBLISHED_GROUP",
                        "detail": "The source groups this event. Raw Mode-S frame correlation cannot be tested.",
                    },
                    {
                        "stage": "receiver_qualification",
                        "status": "BENCHMARK_ONLY",
                        "detail": "Geometry is available. Live CKB identity and clock qualification remain unvalidated.",
                    },
                ],
            }
            event(
                logger,
                "solver_started",
                correlation_id=correlation_id,
                data_provenance="HISTORICAL_REPLAY",
            )
            position = solver.solve_position(observations)
            result["solved"] = position is not None
            result["diagnostics"] = dict(solver.diagnostics)
            result["stages"].append(
                {
                    "stage": "solver",
                    "status": "SOLVED" if position else "REJECTED",
                    "detail": (
                        "Unchanged robust MLAT solver."
                        if position
                        else solver.diagnostics["failure_category"]
                    ),
                }
            )
            if position:
                position_id = database.store_position(
                    aircraft_id=f"DATASET-{row['aircraft']}",
                    timestamp=position.timestamp,
                    latitude=position.latitude,
                    longitude=position.longitude,
                    altitude=position.altitude,
                    uncertainty=position.uncertainty,
                    num_receivers=position.num_receivers,
                    receiver_ids=position.receiver_ids,
                    residual=position.residual,
                    quality_score=position.quality_score,
                    quality_bucket=position.quality_bucket,
                    solver_method=position.solver_method,
                    solver_residual_m=position.residual,
                    solver_iterations=position.iterations,
                    correlation_time_span_s=position.correlation_time_span_s,
                    receiver_count=position.num_receivers,
                    data_provenance="HISTORICAL_REPLAY",
                    source_id=source_id,
                    timestamp_ns=position.timestamp_ns,
                    source_timestamp_ns=position.timestamp_ns,
                    receiver_geometry=geometry,
                    correlation_id=correlation_id,
                    replay_run_id=run_id,
                    observation_evidence={
                        "raw_mode_s_frame_available": False,
                        "correlation_method": "published_event_group",
                        "clock_uncertainty_available": False,
                        "registry_identity_verified": False,
                        "live_qualified": False,
                    },
                )
                result["position_id"] = position_id
                result["stages"].append(
                    {
                        "stage": "storage",
                        "status": "STORED",
                        "detail": "Persisted with original dataset time and HISTORICAL_REPLAY provenance.",
                    }
                )
                solved += 1
                event(
                    logger,
                    "aircraft_solution_created",
                    position_id=position_id,
                    correlation_id=correlation_id,
                    data_provenance="HISTORICAL_REPLAY",
                )
            else:
                reason = solver.diagnostics["failure_category"]
                failures[reason] = failures.get(reason, 0) + 1
                event(logger, "solver_failed", correlation_id=correlation_id, reason=reason)
            database.store_replay_event(row["id"], ordinal, result)
        context.update(
            replay_status="completed",
            successful_solves=solved,
            failed_solves=len(rows) - solved,
            failure_categories=failures,
        )
        database.bind_runtime_provenance("HISTORICAL_REPLAY", source_id, context)
        return context
    finally:
        database.close()
