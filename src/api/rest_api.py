"""
REST API for the MLAT system.

This module uses an app-factory pattern and request-scoped database access.
"""

from __future__ import annotations

from collections import deque
from flask import Blueprint, Flask, current_app, g, jsonify, make_response, request, send_from_directory
import json
import logging
import os
from pathlib import Path
import queue
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional

from demo_scenarios import get_demo_scenario, get_scenario_metadata
from runtime_config import load_runtime_settings

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from flask_cors import CORS
except ImportError:
    CORS = None

try:
    from flask_socketio import SocketIO, emit
except ImportError:
    SocketIO = None

from database.mlat_db import MLATDatabase, StoredPosition
import production_main


if load_dotenv is not None:
    env_file = os.getenv("MLAT_ENV_FILE", os.path.join(os.getcwd(), ".env"))
    load_dotenv(dotenv_path=env_file)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(name: str, default: str = "") -> List[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


DEFAULT_ALLOWED_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"
_broadcast_lock = threading.Lock()
_api_latencies_ms = deque(maxlen=1000)


if SocketIO is None:
    class _FallbackSocketIO:
        def __init__(self):
            self.app: Optional[Flask] = None

        def init_app(self, flask_app: Flask, **_kwargs):
            self.app = flask_app

        def on(self, _event):
            def decorator(func):
                return func
            return decorator

        def emit(self, *_args, **_kwargs):
            return None

        def sleep(self, seconds):
            time.sleep(seconds)

        def start_background_task(self, target, *args, **kwargs):
            thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
            thread.start()
            return thread

        def run(self, flask_app: Flask, host='0.0.0.0', port=5000, debug=False):
            flask_app.run(host=host, port=port, debug=debug)

    socketio = _FallbackSocketIO()

    def emit(*_args, **_kwargs):
        return None
else:
    socketio = SocketIO()


api_bp = Blueprint("api", __name__)


def _render_minified_html(filename: str):
    visualization_dir = Path(current_app.config["VISUALIZATION_DIR"])
    html = (visualization_dir / filename).read_text(encoding="utf-8")
    compact = "\n".join(line.rstrip() for line in html.splitlines() if line.strip())
    response = make_response(compact)
    response.mimetype = "text/html"
    return response


def load_app_config() -> Dict[str, object]:
    """Load API configuration from environment."""
    settings = load_runtime_settings(max_receivers_default=10)
    demo_enabled = settings.demo.enabled
    demo_scenario_name = settings.demo.scenario
    demo_scenario = get_demo_scenario(demo_scenario_name)
    demo_label = settings.demo.label
    configured_transport = (settings.network_config.fourdsky_transport or "auto").strip().lower()
    simulation_mode = configured_transport == "simulation"
    cwd_visualization_dir = Path(os.getcwd()) / "src" / "visualization"
    package_visualization_dir = Path(__file__).resolve().parents[1] / "visualization"
    visualization_dir = (
        cwd_visualization_dir
        if cwd_visualization_dir.exists()
        else package_visualization_dir
    )
    return {
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "data/mlat_data.db"),
        "BENCHMARK_REPORT_PATH": os.getenv("BENCHMARK_REPORT_PATH", "benchmark/latest.json"),
        "PERFORMANCE_REPORT_PATH": os.getenv(
            "PERFORMANCE_REPORT_PATH", "benchmark/performance-latest.json"
        ),
        "RELIABILITY_REPORT_PATH": os.getenv(
            "RELIABILITY_REPORT_PATH", "benchmark/reliability-latest.json"
        ),
        "BENCHMARK_MAX_REPORT_BYTES": int(os.getenv("BENCHMARK_MAX_REPORT_BYTES", "5242880")),
        "CORS_ALLOWED_ORIGINS": _split_csv("CORS_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS),
        "ENABLE_ADMIN_API": _env_bool("ENABLE_ADMIN_API", False),
        "ENABLE_BACKGROUND_BROADCASTER": _env_bool("ENABLE_BACKGROUND_BROADCASTER", True),
        "ADMIN_API_KEY": os.getenv("ADMIN_API_KEY") or os.getenv("API_KEY"),
        "API_KEY_HEADER": os.getenv("API_KEY_HEADER", "X-API-Key"),
        "PUBLIC_PLAN_CODE": os.getenv("PUBLIC_PLAN_CODE", "public_demo"),
        "PREMIUM_PLAN_CODE": os.getenv("PREMIUM_PLAN_CODE", "premium"),
        "API_HOST": os.getenv("API_HOST", "0.0.0.0"),
        "API_PORT": int(os.getenv("API_PORT", "5000")),
        "API_DEBUG": _env_bool("API_DEBUG", False),
        "HEALTH_STALE_SIGNAL_SECONDS": int(os.getenv("HEALTH_STALE_SIGNAL_SECONDS", "120")),
        "SIMULATION_MODE": simulation_mode,
        "STRICT_PRODUCTION_MODE": settings.strict_production_mode,
        "CONFIGURED_TRANSPORT": configured_transport,
        "SIMULATE_IF_UNAVAILABLE": settings.network_config.simulate_if_unavailable,
        "RECEIVER_REGISTRY_TYPE_HASH": settings.network_config.receiver_registry_type_hash,
        "DEMO_MODE": demo_enabled,
        "DEMO_SCENARIO": demo_scenario.slug,
        "DEMO_READ_ONLY": settings.demo.read_only,
        "DEMO_LABEL": demo_label,
        "DEMO_AUTO_CONNECT": settings.demo.auto_connect,
        "DEMO_SCENARIO_METADATA": {
            **get_scenario_metadata(demo_scenario.slug),
            "label": demo_label,
        },
        "VISUALIZATION_DIR": str(visualization_dir),
    }


def create_app(config_overrides: Optional[Dict[str, object]] = None) -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.update(load_app_config())
    if config_overrides:
        app.config.update(config_overrides)

    @app.after_request
    def apply_response_headers(response):
        path = request.path or ""
        is_html = path in {"/", "/dashboard.html"} or response.mimetype == "text/html"
        if is_html:
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        elif path.endswith((".css", ".js", ".woff2", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response

    allowed_origins = app.config["CORS_ALLOWED_ORIGINS"]
    if CORS is not None:
        CORS(app, origins=allowed_origins)
    else:
        @app.after_request
        def add_cors_headers(response):
            origin = request.headers.get("Origin")
            if origin and origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,X-API-Key"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            return response

    if SocketIO is not None:
        socketio.init_app(app, cors_allowed_origins=allowed_origins)
    else:
        socketio.init_app(app)

    app.teardown_appcontext(close_db)
    app.register_blueprint(api_bp)

    if app.config["ENABLE_BACKGROUND_BROADCASTER"]:
        _start_background_broadcaster(app)

    return app


def get_db() -> MLATDatabase:
    """Get the request-scoped database connection."""
    if "db" not in g:
        db = MLATDatabase(current_app.config["DATABASE_PATH"])
        db.connect()
        g.db = db
    return g.db


def close_db(_error=None):
    """Close the request-scoped database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _validate_api_key() -> bool:
    api_key = current_app.config.get("ADMIN_API_KEY")
    if not api_key:
        return False
    header_name = current_app.config["API_KEY_HEADER"]
    return request.headers.get(header_name) == api_key


def _resolve_request_auth() -> Optional[Dict[str, Any]]:
    header_name = current_app.config["API_KEY_HEADER"]
    raw_key = request.headers.get(header_name)
    if not raw_key:
        return None

    auth = get_db().authenticate_api_key(raw_key)
    if auth is None:
        return None
    if auth["api_key_status"] != "active" or auth["account_status"] != "active":
        return None

    get_db().touch_api_key(auth["api_key_id"])
    g.auth = auth
    return auth


def get_request_auth() -> Optional[Dict[str, Any]]:
    auth = getattr(g, "auth", None)
    if auth is not None:
        return auth
    return _resolve_request_auth()


def _has_active_entitlement(auth: Dict[str, Any], entitlement_code: str) -> bool:
    for entitlement in auth.get("entitlements", []):
        if entitlement["entitlement_code"] == entitlement_code and entitlement["status"] == "active":
            return True
    return False


def require_plan_access(*, require_premium: bool = False, stream_required: bool = False):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            auth = get_request_auth()
            if auth is None:
                return jsonify({"error": "Unauthorized"}), 403
            if require_premium and not auth.get("can_access_premium", False):
                return jsonify({"error": "Premium plan required"}), 403
            if stream_required and not auth.get("can_stream_live", False):
                return jsonify({"error": "Streaming entitlement required"}), 403
            return func(*args, **kwargs)
        return wrapped
    return decorator


def record_usage(event_type: str, resource: str, quantity: int = 1, metadata: Optional[Dict[str, Any]] = None):
    auth = get_request_auth()
    if auth is None:
        return
    get_db().record_usage_event(
        account_id=auth["account_id"],
        api_key_id=auth["api_key_id"],
        event_type=event_type,
        resource=resource,
        quantity=quantity,
        metadata=metadata,
    )


def _parse_cleanup_days() -> int:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    days = data.get("days", 7)
    if not isinstance(days, int):
        raise ValueError("'days' must be an integer")
    if days < 1 or days > 365:
        raise ValueError("'days' must be between 1 and 365")
    return days


def get_runtime_state(db: Optional[MLATDatabase] = None) -> Optional[Dict[str, object]]:
    """Read runtime telemetry in-process or from processor snapshots in SQLite."""
    runtime = production_main.CURRENT_RUNTIME
    if runtime is not None:
        state = runtime.get_runtime_state()
        state["telemetry_source"] = "in_process"
        state["telemetry_fresh"] = True
    elif db is not None:
        latest_stats = db.get_latest_statistics()
        if latest_stats is None:
            return None

        now = time.time()
        telemetry_age_s = max(0.0, now - float(latest_stats["timestamp"]))
        stale_threshold_s = int(current_app.config["HEALTH_STALE_SIGNAL_SECONDS"])
        telemetry_fresh_s = max(
            stale_threshold_s,
            int(os.getenv("STATS_INTERVAL_SECONDS", "60")) * 2,
        )
        latest_position = db.get_latest_position()
        last_store_age_s = (
            max(0.0, now - latest_position.timestamp)
            if latest_position is not None
            else None
        )
        signal_fresh = bool(
            telemetry_age_s <= telemetry_fresh_s
            and last_store_age_s is not None
            and last_store_age_s <= stale_threshold_s
        )
        state = {
            "is_running": telemetry_age_s <= telemetry_fresh_s,
            "telemetry_source": "database",
            "telemetry_age_s": telemetry_age_s,
            "telemetry_fresh": telemetry_age_s <= telemetry_fresh_s,
            "last_signal_age_s": (
                float(latest_stats["last_signal_age_s"]) + telemetry_age_s
                if latest_stats.get("last_signal_age_s") is not None
                else last_store_age_s
            ),
            "last_successful_solve_age_s": last_store_age_s,
            "last_store_age_s": last_store_age_s,
            "avg_ingest_latency_ms": float(latest_stats.get("avg_ingest_latency_ms", 0.0)),
            "max_ingest_latency_ms": float(latest_stats.get("max_ingest_latency_ms", 0.0)),
            "avg_solve_latency_ms": float(latest_stats.get("avg_latency_ms", 0.0)),
            "max_solve_latency_ms": float(latest_stats.get("max_latency_ms", 0.0)),
            "avg_store_latency_ms": float(latest_stats.get("avg_store_latency_ms", 0.0)),
            "max_store_latency_ms": float(latest_stats.get("max_store_latency_ms", 0.0)),
            "discovery_latency_ms": float(latest_stats.get("discovery_latency_ms", 0.0)),
            "registry_discovery_live": bool(latest_stats.get("registry_discovery_live", 0)),
            "process_rss_mb": float(latest_stats.get("process_rss_mb", 0.0)),
            "uptime_s": float(latest_stats.get("uptime_s", 0.0)),
            "total_signals": int(latest_stats.get("total_signals", 0)),
            "total_positions": int(latest_stats.get("total_positions", 0)),
            "successful_solves": int(latest_stats.get("successful_solves", 0)),
            "failed_solves": int(latest_stats.get("failed_solves", 0)),
            "rejected_groups": int(latest_stats.get("rejected_groups", 0)),
            "active_receivers": int(latest_stats.get("active_receivers", 0)),
            "signal_fresh": signal_fresh,
            "strict_production_mode": bool(current_app.config.get("STRICT_PRODUCTION_MODE")),
            "synthetic_feed_mode": bool(
                latest_stats.get("synthetic_feed_mode", 0)
                or (latest_position and _is_synthetic_solver_method(latest_position.solver_method))
            ),
        }
        uptime_s = float(state["uptime_s"])
        total_positions = int(state["total_positions"])
        state["signals_per_second"] = (
            int(state["total_signals"]) / uptime_s if uptime_s else 0.0
        )
        state["positions_per_second"] = total_positions / uptime_s if uptime_s else 0.0
        state["solve_success_percent"] = (
            100.0 * int(state["successful_solves"]) / total_positions
            if total_positions else 0.0
        )
    else:
        return None

    latencies = list(_api_latencies_ms)
    state["avg_api_latency_ms"] = sum(latencies) / len(latencies) if latencies else 0.0
    state["max_api_latency_ms"] = max(latencies) if latencies else 0.0
    return state


def record_api_latency(started_at: float):
    elapsed_ms = (time.time() - started_at) * 1000
    _api_latencies_ms.append(elapsed_ms)
    runtime = production_main.CURRENT_RUNTIME
    if runtime is not None:
        runtime.api_latencies_ms.append(elapsed_ms)


def _is_synthetic_solver_method(method: Optional[str]) -> bool:
    return method in {"simulated_replay", "simulation", "unknown"}



def _load_benchmark_report() -> tuple[Optional[Dict[str, Any]], str]:
    """Load and minimally validate the configured public evidence artifact."""
    report_path = Path(str(current_app.config["BENCHMARK_REPORT_PATH"]))
    if not report_path.exists():
        return None, "not_found"
    if not report_path.is_file():
        return None, "invalid"
    if report_path.stat().st_size > int(current_app.config["BENCHMARK_MAX_REPORT_BYTES"]):
        return None, "too_large"

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        logger.exception("Failed to load benchmark report from %s", report_path)
        return None, "invalid"

    required_objects = ("provenance", "sample", "accuracy", "freshness")
    if (
        not isinstance(report, dict)
        or report.get("schema_version") != 1
        or report.get("evidence_status") not in {"publishable", "pipeline_only"}
        or not isinstance(report.get("generated_at"), str)
        or any(not isinstance(report.get(field), dict) for field in required_objects)
    ):
        return None, "invalid"
    return report, "available"


def _load_operational_report(config_key: str) -> tuple[Optional[Dict[str, Any]], str]:
    """Load a bounded, versioned operational evidence artifact."""
    report_path = Path(str(current_app.config[config_key]))
    if not report_path.exists():
        return None, "not_found"
    if not report_path.is_file() or report_path.stat().st_size > int(
        current_app.config["BENCHMARK_MAX_REPORT_BYTES"]
    ):
        return None, "invalid"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid"
    if (
        not isinstance(report, dict)
        or report.get("schema_version") != 1
        or not isinstance(report.get("generated_at"), str)
        or not isinstance(report.get("provenance"), dict)
        or not isinstance(report.get("metrics"), dict)
    ):
        return None, "invalid"
    return report, "available"


def _evidence_history(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize cumulative statistics into chart-ready interval samples."""
    samples: List[Dict[str, Any]] = []
    previous: Optional[Dict[str, Any]] = None
    for row in rows:
        timestamp = float(row["timestamp"])
        uptime_s = float(row.get("uptime_s", 0.0))
        counters_are_monotonic = bool(
            previous is not None
            and int(row["total_signals"]) >= int(previous["total_signals"])
            and int(row["total_positions"]) >= int(previous["total_positions"])
            and uptime_s >= float(previous.get("uptime_s", 0.0))
        )
        if counters_are_monotonic and previous is not None:
            interval_s = max(0.001, timestamp - float(previous["timestamp"]))
            signal_delta = max(0, int(row["total_signals"]) - int(previous["total_signals"]))
            position_delta = max(0, int(row["total_positions"]) - int(previous["total_positions"]))
        elif uptime_s > 0:
            # A process restart resets cumulative counters. Use its own uptime
            # instead of comparing it with the previous process snapshot.
            interval_s = max(1.0, uptime_s)
            signal_delta = int(row["total_signals"])
            position_delta = int(row["total_positions"])
        else:
            # Pre-telemetry schema rows have no trustworthy rate denominator.
            interval_s = 1.0
            signal_delta = 0
            position_delta = 0

        total_positions = int(row["total_positions"])
        successful_solves = int(row.get("successful_solves", 0))
        samples.append({
            "timestamp": timestamp,
            "signals_per_minute": round(signal_delta * 60.0 / interval_s, 2),
            "positions_per_minute": round(position_delta * 60.0 / interval_s, 2),
            "total_signals": int(row["total_signals"]),
            "total_positions": total_positions,
            "solve_success_percent": round(
                100.0 * successful_solves / total_positions, 2
            ) if total_positions else 0.0,
            "active_aircraft": int(row["active_aircraft"]),
            "active_receivers": int(row["active_receivers"]),
            "avg_quality_score": float(row.get("avg_quality_score", 0.0)),
            "avg_uncertainty_m": float(row.get("avg_uncertainty", 0.0)),
            "avg_ingest_latency_ms": float(row.get("avg_ingest_latency_ms", 0.0)),
            "avg_solve_latency_ms": float(row.get("avg_latency_ms", 0.0)),
            "avg_store_latency_ms": float(row.get("avg_store_latency_ms", 0.0)),
            "discovery_latency_ms": float(row.get("discovery_latency_ms", 0.0)),
            "registry_discovery_live": bool(row.get("registry_discovery_live", 0)),
            "process_rss_mb": float(row.get("process_rss_mb", 0.0)),
            "uptime_s": uptime_s,
            "last_signal_age_s": row.get("last_signal_age_s"),
            "last_store_age_s": row.get("last_store_age_s"),
            "failed_solves": int(row.get("failed_solves", 0)),
            "rejected_groups": int(row.get("rejected_groups", 0)),
            "synthetic_feed_mode": bool(row.get("synthetic_feed_mode", 0)),
        })
        previous = row
    return samples


def _parse_receiver_ids(raw_receiver_ids: Any) -> List[str]:
    if isinstance(raw_receiver_ids, list):
        return [str(receiver_id) for receiver_id in raw_receiver_ids if receiver_id]
    if isinstance(raw_receiver_ids, str):
        try:
            parsed = json.loads(raw_receiver_ids)
        except json.JSONDecodeError:
            return [raw_receiver_ids] if raw_receiver_ids else []
        if isinstance(parsed, list):
            return [str(receiver_id) for receiver_id in parsed if receiver_id]
    return []



def _build_position_payload(position: StoredPosition) -> Dict:
    receiver_ids = _parse_receiver_ids(position.receiver_ids)
    return {
        "id": position.id,
        "aircraft_id": position.aircraft_id,
        "timestamp": position.timestamp,
        "position": {
            "latitude": position.latitude,
            "longitude": position.longitude,
            "altitude": position.altitude,
        },
        "uncertainty": position.uncertainty,
        "num_receivers": position.num_receivers,
        "quality": {
            "score": position.quality_score,
            "bucket": position.quality_bucket,
            "uncertainty_m": position.uncertainty,
        },
        "solver": {
            "method": position.solver_method,
            "residual_m": position.solver_residual_m,
            "iterations": position.solver_iterations,
        },
        "correlation": {
            "time_span_s": position.correlation_time_span_s,
            "receiver_count": position.receiver_count,
            "receiver_ids": receiver_ids,
        },
        "created_at": position.created_at,
    }


def broadcast_position_update(aircraft_id: str, position_data: Dict):
    """Broadcast a position update to websocket clients."""
    payload = {
        "aircraft_id": aircraft_id,
        "position": position_data,
    }
    socketio.emit("position_update", payload)
    socketio.emit("position_update", payload, room=aircraft_id)


def _start_background_broadcaster(app: Flask):
    """Emit websocket updates from the local DB event queue with DB fallback polling."""
    with _broadcast_lock:
        if app.extensions.get("mlat_broadcaster_started"):
            return
        app.extensions["mlat_broadcaster_started"] = True

    def _poll_new_positions():
        poll_db = MLATDatabase(app.config["DATABASE_PATH"])
        poll_db.connect()
        position_queue = poll_db.get_or_create_position_queue()
        last_position_id = 0

        try:
            existing = poll_db.get_recent_positions(seconds=86400, limit=1)
            if existing and existing[0].id is not None:
                last_position_id = existing[0].id

            while True:
                try:
                    position_id = position_queue.get(timeout=1.0)
                    position = poll_db.get_position_by_id(position_id)
                    if position is None:
                        continue
                    last_position_id = max(last_position_id, position.id or 0)
                    payload = _build_position_payload(position)
                    broadcast_position_update(
                        aircraft_id=position.aircraft_id,
                        position_data=payload,
                    )
                except queue.Empty:
                    new_positions = poll_db.get_positions_after_id(last_position_id, limit=200)
                    for position in new_positions:
                        last_position_id = max(last_position_id, position.id or 0)
                        payload = _build_position_payload(position)
                        broadcast_position_update(
                            aircraft_id=position.aircraft_id,
                            position_data=payload,
                        )
        finally:
            poll_db.close()

    socketio.start_background_task(_poll_new_positions)


@api_bp.before_app_request
def _start_request_timer():
    g.request_started_at = time.time()


@api_bp.after_app_request
def _record_request_latency(response):
    started_at = getattr(g, "request_started_at", None)
    if started_at is not None:
        record_api_latency(started_at)
    return response


@api_bp.route("/healthz", methods=["GET"])
def liveness_check():
    """Return process liveness without depending on SQLite or the processor."""
    return jsonify({
        "status": "ok",
        "service": "MLAT API",
        "timestamp": datetime.now().isoformat(),
    })


@api_bp.route("/api/health", methods=["GET"])
def health_check():
    db = get_db()
    db_stats = db.get_database_stats()
    runtime_state = get_runtime_state(db) or {}
    recent_receivers = db.get_receivers()
    now = time.time()
    receiver_freshness = [max(0.0, now - receiver.last_seen) for receiver in recent_receivers]
    last_signal_age_s = runtime_state.get("last_signal_age_s")
    status = "ok"
    if last_signal_age_s is None or last_signal_age_s > current_app.config["HEALTH_STALE_SIGNAL_SECONDS"]:
        status = "degraded"

    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "service": "MLAT API",
        "database": {
            "path": current_app.config["DATABASE_PATH"],
            "journal_mode": db_stats.get("journal_mode"),
            "sqlite_single_node_only": db_stats.get("sqlite_single_node_only", True),
            "size_mb": db_stats.get("database_size_mb", 0),
        },
        "runtime": runtime_state,
        "freshness": {
            "last_signal_age_s": last_signal_age_s,
            "last_successful_solve_age_s": runtime_state.get("last_successful_solve_age_s"),
            "last_store_age_s": runtime_state.get("last_store_age_s"),
            "receiver_last_seen_age_s": min(receiver_freshness) if receiver_freshness else None,
            "receiver_stale_count": sum(1 for age in receiver_freshness if age > current_app.config["HEALTH_STALE_SIGNAL_SECONDS"]),
        },
        "broadcaster": {
            "enabled": bool(current_app.config["ENABLE_BACKGROUND_BROADCASTER"]),
            "started": bool(current_app.extensions.get("mlat_broadcaster_started")),
            "websocket_available": SocketIO is not None,
        },
    })


@api_bp.route("/api/readiness", methods=["GET"])
def readiness_check():
    """
    Summarize whether the current runtime looks operationally ready on
    quality, freshness, reliability, and packaging dimensions.
    """
    db = get_db()
    runtime_state = get_runtime_state(db) or {}
    recent_positions = db.get_recent_positions(seconds=300, limit=500)
    receiver_rows = db.get_receivers()

    position_count = len(recent_positions)
    avg_quality_score = (
        sum(position.quality_score for position in recent_positions) / position_count
        if position_count else 0.0
    )
    avg_uncertainty = (
        sum(position.uncertainty for position in recent_positions) / position_count
        if position_count else 0.0
    )
    avg_residual = (
        sum(position.solver_residual_m for position in recent_positions) / position_count
        if position_count else 0.0
    )
    avg_receiver_count = (
        sum(position.receiver_count for position in recent_positions) / position_count
        if position_count else 0.0
    )
    simulated_positions = sum(
        1 for position in recent_positions
        if _is_synthetic_solver_method(position.solver_method)
    )
    benchmarkable_output = position_count > 0 and simulated_positions == 0
    max_last_store_age = runtime_state.get("last_store_age_s")
    if max_last_store_age is None and recent_positions:
        max_last_store_age = max(0.0, time.time() - recent_positions[0].timestamp)
    signal_fresh = bool(runtime_state.get("signal_fresh"))
    failed_solves = int(runtime_state.get("failed_solves", 0))
    rejected_groups = int(runtime_state.get("rejected_groups", 0))
    active_receivers = int(runtime_state.get(
        "active_receivers",
        len([row for row in receiver_rows if row.status == "online"]),
    ))

    quality_ready = position_count > 0 and avg_quality_score >= 0.65 and avg_receiver_count >= 4
    freshness_ready = max_last_store_age is not None and max_last_store_age <= 30
    reliability_ready = signal_fresh and active_receivers >= 4 and failed_solves == 0
    packaging_ready = True
    benchmark_report, benchmark_status = _load_benchmark_report()

    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "ready": quality_ready and freshness_ready and reliability_ready and packaging_ready,
        "dimensions": {
            "quality": {
                "ready": quality_ready,
                "recent_position_count": position_count,
                "avg_quality_score": avg_quality_score,
                "avg_uncertainty_m": avg_uncertainty,
                "avg_solver_residual_m": avg_residual,
                "avg_receiver_count": avg_receiver_count,
                "simulated_positions": simulated_positions,
                "benchmarkable_output": benchmarkable_output,
            },
            "freshness": {
                "ready": freshness_ready,
                "last_store_age_s": max_last_store_age,
                "avg_ingest_latency_ms": runtime_state.get("avg_ingest_latency_ms", 0.0),
                "avg_solve_latency_ms": runtime_state.get("avg_solve_latency_ms", 0.0),
                "avg_store_latency_ms": runtime_state.get("avg_store_latency_ms", 0.0),
                "avg_api_latency_ms": runtime_state.get("avg_api_latency_ms", 0.0),
            },
            "reliability": {
                "ready": reliability_ready,
                "signal_fresh": signal_fresh,
                "active_receivers": active_receivers,
                "failed_solves": failed_solves,
                "rejected_groups": rejected_groups,
                "uptime_s": runtime_state.get("uptime_s", 0.0),
            },
            "packaging": {
                "ready": packaging_ready,
                "premium_statistics_endpoint": True,
                "health_endpoint": True,
                "positions_endpoint": True,
                "track_endpoint": True,
                "quality_fields_exposed": position_count > 0,
            },
        },
        "not_yet_proven": {
            "more_accurate_than_incumbents": False,
            "more_complete_than_incumbents": False,
            "cheaper_than_incumbents": False,
            "faster_than_incumbents": False,
            "better_coverage_than_incumbents": False,
            "better_analytics_than_incumbents": False,
            "reason": (
                "The project captures internal quality/freshness/reliability metrics, "
                "but it still lacks external benchmark evidence against trusted competitors "
                "and reference feeds. If output is simulated or replay-derived, the current "
                "dataset is not benchmarkable for real-world quality claims."
            ),
        },
        "external_benchmark": {
            "available": benchmark_report is not None,
            "publishable": bool(
                benchmark_report
                and benchmark_report.get("provenance", {}).get("benchmarkable") is True
                and benchmark_report.get("evidence_status") == "publishable"
            ),
            "status": benchmark_status,
            "generated_at": benchmark_report.get("generated_at") if benchmark_report else None,
        },
    })


@api_bp.route("/api/benchmark/latest", methods=["GET"])
def get_latest_benchmark():
    """Publish the latest versioned benchmark evidence artifact."""
    report, status = _load_benchmark_report()
    if report is None:
        status_code = 404 if status == "not_found" else 503
        return jsonify({
            "available": False,
            "status": status,
            "message": "No valid benchmark evidence report is currently published.",
        }), status_code
    return jsonify(report)


@api_bp.route("/api/evidence/performance/latest", methods=["GET"])
def get_latest_performance_evidence():
    """Publish the latest reproducible local performance baseline."""
    report, status = _load_operational_report("PERFORMANCE_REPORT_PATH")
    if report is None:
        return jsonify({
            "available": False,
            "status": status,
            "message": "No valid performance evidence report is currently published.",
        }), 404 if status == "not_found" else 503
    return jsonify(report)


@api_bp.route("/api/evidence/reliability/latest", methods=["GET"])
def get_latest_reliability_evidence():
    """Publish the latest sampled API/runtime reliability window."""
    report, status = _load_operational_report("RELIABILITY_REPORT_PATH")
    if report is None:
        return jsonify({
            "available": False,
            "status": status,
            "message": "No valid reliability evidence report is currently published.",
        }), 404 if status == "not_found" else 503
    return jsonify(report)


@api_bp.route("/api/evidence/metrics", methods=["GET"])
def get_public_evidence_metrics():
    """Expose bounded operational history without premium aircraft tracks."""
    hours = min(168, max(1, request.args.get("hours", default=24, type=int)))
    limit = min(1000, max(1, request.args.get("limit", default=500, type=int)))
    db = get_db()
    rows = db.get_statistics_history(hours=hours)[-limit:]
    history = _evidence_history(rows)
    runtime_state = get_runtime_state(db) or {}
    current = dict(history[-1]) if history else {
        "total_signals": 0,
        "total_positions": 0,
        "solve_success_percent": 0.0,
        "active_aircraft": 0,
        "active_receivers": 0,
        "failed_solves": 0,
        "rejected_groups": 0,
        "synthetic_feed_mode": bool(runtime_state.get("synthetic_feed_mode")),
    }
    current["avg_api_latency_ms"] = round(
        float(runtime_state.get("avg_api_latency_ms", 0.0)), 3
    )
    current["last_signal_age_s"] = runtime_state.get("last_signal_age_s")
    current["last_store_age_s"] = runtime_state.get("last_store_age_s")

    receiver_ready_samples = sum(1 for item in history if item["active_receivers"] >= 4)
    fresh_samples = [
        item for item in history if item.get("last_signal_age_s") is not None
    ]
    fresh_signal_samples = sum(
        1 for item in fresh_samples
        if float(item["last_signal_age_s"]) <= int(current_app.config["HEALTH_STALE_SIGNAL_SECONDS"])
    )
    sample_count = len(history)
    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "window_hours": hours,
        "sample_count": sample_count,
        "provenance": {
            "mode": "replay" if current.get("synthetic_feed_mode") else "live",
            "live_data": not bool(current.get("synthetic_feed_mode")),
            "source": "processor_statistics",
        },
        "current": current,
        "reliability": {
            "receiver_availability_percent": round(
                100.0 * receiver_ready_samples / sample_count, 2
            ) if sample_count else None,
            "signal_freshness_percent": round(
                100.0 * fresh_signal_samples / len(fresh_samples), 2
            ) if fresh_samples else None,
            "solve_success_percent": current.get("solve_success_percent", 0.0),
            "api_availability_percent": None,
            "api_availability_note": (
                "Run capture_reliability_window.py to measure API availability over time."
            ),
        },
        "history": history,
    })


@api_bp.route("/api/pipeline", methods=["GET"])
def get_pipeline_evidence():
    """Describe the full receiver-to-dashboard path with explicit provenance."""
    db = get_db()
    runtime_state = get_runtime_state(db) or {}
    latest_stats = db.get_latest_statistics() or {}
    receivers = db.get_receivers()
    positions = db.get_recent_positions(seconds=300, limit=500)
    registry_hash = str(current_app.config.get("RECEIVER_REGISTRY_TYPE_HASH") or "")
    registry_configured = bool(registry_hash)
    registry_discovery_live = bool(runtime_state.get("registry_discovery_live"))
    synthetic = bool(runtime_state.get("synthetic_feed_mode"))
    demo = bool(current_app.config.get("DEMO_MODE"))
    signal_fresh = bool(runtime_state.get("signal_fresh"))
    total_signals = int(runtime_state.get("total_signals", latest_stats.get("total_signals", 0)))
    total_positions = int(runtime_state.get("total_positions", latest_stats.get("total_positions", 0)))
    latest_position = positions[0] if positions else None
    benchmarkable = bool(
        positions
        and not synthetic
        and all(not _is_synthetic_solver_method(item.solver_method) for item in positions)
    )
    benchmark_report, benchmark_status = _load_benchmark_report()
    benchmark_publishable = bool(
        benchmark_report
        and benchmark_report.get("evidence_status") == "publishable"
        and benchmark_report.get("provenance", {}).get("benchmarkable") is True
    )
    provenance_mode = "replay" if synthetic or demo else "live"

    def stage(
        stage_id: str,
        label: str,
        status: str,
        detail: str,
        **metrics: Any,
    ) -> Dict[str, Any]:
        return {
            "id": stage_id,
            "label": label,
            "status": status,
            "detail": detail,
            "metrics": metrics,
        }

    registry_status = (
        "pass" if registry_configured and registry_discovery_live
        else "demo" if demo
        else "blocked"
    )
    discovery_status = (
        "pass" if registry_configured and registry_discovery_live and receivers
        else "demo" if demo and receivers
        else "waiting"
    )
    ingest_status = (
        "demo" if synthetic and signal_fresh
        else "pass" if signal_fresh and total_signals > 0
        else "waiting"
    )
    processing_status = (
        "demo" if synthetic and total_positions > 0
        else "pass" if total_positions > 0
        else "waiting"
    )
    solve_status = (
        "demo" if synthetic and latest_position
        else "pass" if latest_position and benchmarkable
        else "waiting"
    )

    stages = [
        stage(
            "registry", "CKB registration", registry_status,
            "Receiver cells were discovered through the configured CKB type hash." if registry_discovery_live
            else "Demo receivers are local; configure the CKB registry type hash for live proof." if demo
            else "A type hash is configured, but live CKB discovery is not verified." if registry_configured
            else "Receiver registry type hash is not configured.",
            configured=registry_configured,
            live_discovery=registry_discovery_live,
            type_hash_prefix=f"{registry_hash[:18]}..." if registry_hash else None,
        ),
        stage(
            "discovery", "Receiver discovery", discovery_status,
            f"{len(receivers)} receiver records available to the runtime.",
            receiver_count=len(receivers),
            discovery_latency_ms=runtime_state.get("discovery_latency_ms", 0.0),
        ),
        stage(
            "ingest", "Observation ingest", ingest_status,
            "Receiver observations are arriving." if signal_fresh
            else "Waiting for a receiver observation source.",
            total_signals=total_signals,
            signals_per_second=runtime_state.get("signals_per_second", 0.0),
            last_signal_age_s=runtime_state.get("last_signal_age_s"),
        ),
        stage(
            "correlation", "Signal correlation", processing_status,
            "Correlated groups are reaching the solve path." if total_positions
            else "Waiting for at least four synchronized observations per transmission.",
            position_attempts=total_positions,
            rejected_groups=runtime_state.get("rejected_groups", 0),
        ),
        stage(
            "solve", "MLAT solve", solve_status,
            "Replay positions are generated for pipeline validation." if synthetic and latest_position
            else "Robust MLAT positions are available." if latest_position
            else "No solved aircraft position is available yet.",
            solver_method=latest_position.solver_method if latest_position else None,
            successful_solves=runtime_state.get("successful_solves", 0),
            solve_success_percent=runtime_state.get("solve_success_percent", 0.0),
        ),
        stage(
            "storage", "Position storage", "pass" if latest_position else "waiting",
            "Latest position is persisted in SQLite." if latest_position
            else "No position has been stored.",
            recent_positions=len(positions),
            last_store_age_s=runtime_state.get("last_store_age_s"),
            avg_store_latency_ms=runtime_state.get("avg_store_latency_ms", 0.0),
        ),
        stage(
            "api", "Public API", "pass",
            "Health, positions, pipeline, metrics, and evidence routes are responding.",
            avg_api_latency_ms=runtime_state.get("avg_api_latency_ms", 0.0),
        ),
        stage(
            "dashboard", "Dashboard", "pass",
            "Operational pages consume the same public evidence APIs.",
            pipeline_route="/app/pipeline.html",
            metrics_route="/app/analytics.html",
        ),
    ]

    blockers = []
    if not registry_configured:
        blockers.append("CKB registry type hash is not active in this runtime.")
    elif not registry_discovery_live:
        blockers.append("Receiver discovery has not been verified against live CKB cells.")
    if synthetic:
        blockers.append("Observation and solve output is replay/synthetic, not live.")
    if not signal_fresh:
        blockers.append("No fresh receiver observations are arriving.")
    if not benchmarkable:
        blockers.append("Recent positions are not eligible for live external benchmarking.")
    if not benchmark_publishable:
        blockers.append("No publishable external benchmark report is available.")

    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "provenance": {
            "mode": provenance_mode,
            "live_data": provenance_mode == "live",
            "synthetic_feed_mode": synthetic,
            "registry_discovery_live": registry_discovery_live,
            "benchmarkable_output": benchmarkable,
        },
        "pipeline_operational": all(item["status"] in {"pass", "demo"} for item in stages),
        "live_evidence_ready": bool(
            provenance_mode == "live"
            and registry_configured
            and registry_discovery_live
            and signal_fresh
            and benchmarkable
            and benchmark_publishable
        ),
        "benchmark": {
            "status": benchmark_status,
            "publishable": benchmark_publishable,
        },
        "blockers": blockers,
        "stages": stages,
    })


@api_bp.route("/", methods=["GET"])
def landing_page():
    return _render_minified_html("index.html")


@api_bp.route("/dashboard.html", methods=["GET"])
def dashboard_page():
    return _render_minified_html("app/localization.html")


@api_bp.route("/app/<path:page_name>", methods=["GET"])
def app_pages(page_name: str):
    visualization_dir = Path(current_app.config["VISUALIZATION_DIR"]) / "app"
    if not page_name.endswith(".html"):
        return jsonify({"error": "Endpoint not found"}), 404
    candidate = visualization_dir / page_name
    if not candidate.exists():
        return jsonify({"error": "Endpoint not found"}), 404
    response = send_from_directory(str(visualization_dir), page_name)
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@api_bp.route("/<path:asset_path>", methods=["GET"])
def visualization_assets(asset_path: str):
    visualization_dir = Path(current_app.config["VISUALIZATION_DIR"])
    asset = Path(asset_path)
    if asset.name in {"index.html", "dashboard.html"}:
        return _render_minified_html(asset.name)

    response = send_from_directory(str(visualization_dir), asset_path)
    suffix = asset.suffix.lower()
    if suffix in {".css", ".js", ".woff2", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}:
        response.cache_control.public = True
        response.cache_control.max_age = 31536000
        response.cache_control.immutable = True
    return response


@api_bp.route("/api/system/mode", methods=["GET"])
def get_system_mode():
    """Expose runtime mode and hosted demo metadata for the frontend."""
    demo_mode = bool(current_app.config["DEMO_MODE"])
    db = get_db()
    runtime_state = get_runtime_state(db) or {}
    runtime_status = (
        "active"
        if runtime_state.get("telemetry_fresh") and runtime_state.get("is_running")
        else "stale"
        if runtime_state
        else "unavailable"
    )
    recent_positions = db.get_recent_positions(seconds=300, limit=100)
    benchmarkable_output = bool(
        recent_positions
        and all(not _is_synthetic_solver_method(position.solver_method) for position in recent_positions)
    )
    configured_simulation = bool(current_app.config["SIMULATION_MODE"])
    strict_production_mode = bool(current_app.config["STRICT_PRODUCTION_MODE"])
    synthetic_feed_mode = bool(runtime_state.get("synthetic_feed_mode", configured_simulation))
    startup_guardrail_status = (
        "strict_live"
        if strict_production_mode and runtime_status == "active"
        else "strict_waiting"
        if strict_production_mode
        else "demo"
        if demo_mode
        else "simulation"
        if configured_simulation
        else "standard"
    )
    return jsonify(
        {
            "mode": (
                "demo"
                if demo_mode
                else "simulation"
                if configured_simulation or synthetic_feed_mode
                else "live"
                if runtime_status == "active"
                else "configured_live"
            ),
            "simulation_mode": configured_simulation,
            "demo_mode": demo_mode,
            "strict_production_mode": strict_production_mode,
            "startup_guardrail_status": startup_guardrail_status,
            "configured_transport": current_app.config["CONFIGURED_TRANSPORT"],
            "simulate_if_unavailable": bool(current_app.config["SIMULATE_IF_UNAVAILABLE"]),
            "demo_read_only": bool(current_app.config["DEMO_READ_ONLY"]),
            "demo_label": current_app.config["DEMO_LABEL"],
            "demo_auto_connect": bool(current_app.config["DEMO_AUTO_CONNECT"]),
            "demo_scenario": current_app.config["DEMO_SCENARIO"],
            "scenario": current_app.config["DEMO_SCENARIO_METADATA"],
            "ui": {
                "read_only": bool(current_app.config["DEMO_READ_ONLY"]),
                "auto_connect": bool(current_app.config["DEMO_AUTO_CONNECT"]),
            },
            "receiver_registry_type_hash": os.getenv("RECEIVER_REGISTRY_TYPE_HASH", ""),
            "registry_discovery_live": bool(runtime_state.get("registry_discovery_live")),
            "websocket_available": SocketIO is not None,
            "synthetic_feed_mode": synthetic_feed_mode,
            "runtime_status": runtime_status,
            "runtime_telemetry_source": runtime_state.get("telemetry_source"),
            "benchmarkable_output": benchmarkable_output,
        }
    )


@api_bp.route("/api/aircraft", methods=["GET"])
def get_aircraft_list():
    seconds = request.args.get("seconds", default=300, type=int)
    aircraft_ids = get_db().get_active_aircraft(seconds=seconds)
    record_usage("rest_request", "aircraft_list", metadata={"seconds": seconds})
    return jsonify({
        "aircraft": aircraft_ids,
        "count": len(aircraft_ids),
        "time_window_seconds": seconds,
    })


@api_bp.route("/api/positions/recent", methods=["GET"])
def get_recent_positions():
    auth = get_request_auth()
    seconds = request.args.get("seconds", default=60, type=int)
    limit = request.args.get("limit", default=100, type=int)
    if auth is not None:
        seconds = min(seconds, auth["max_history_seconds"])
        if limit > 100 and not auth.get("can_access_premium", False):
            return jsonify({"error": "Premium plan required for deeper recent-position queries"}), 403
    positions = get_db().get_recent_positions(seconds=seconds, limit=limit)
    positions_data = [_build_position_payload(position) for position in positions]
    record_usage("rest_request", "recent_positions", quantity=len(positions_data), metadata={"seconds": seconds, "limit": limit})
    return jsonify({
        "positions": positions_data,
        "count": len(positions_data),
        "time_window_seconds": seconds,
    })


@api_bp.route("/api/receivers", methods=["GET"])
def get_receivers():
    receivers = get_db().get_receivers()
    receiver_data = [
        {
            "receiver_id": receiver.receiver_id,
            "latitude": receiver.latitude,
            "longitude": receiver.longitude,
            "altitude": receiver.altitude,
            "status": receiver.status,
            "last_seen": receiver.last_seen,
            "capabilities": json.loads(receiver.capabilities),
            "updated_at": receiver.updated_at,
        }
        for receiver in receivers
    ]
    return jsonify({"receivers": receiver_data, "count": len(receiver_data)})


@api_bp.route("/api/aircraft/<aircraft_id>/track", methods=["GET"])
def get_aircraft_track(aircraft_id: str):
    auth = get_request_auth()
    start_time = request.args.get("start_time", type=float)
    end_time = request.args.get("end_time", type=float)
    limit = request.args.get("limit", default=1000, type=int)
    if auth is not None:
        if limit > 250 and not auth.get("can_access_premium", False):
            return jsonify({"error": "Premium plan required for deep track history"}), 403
        if start_time is not None and end_time is not None:
            requested_window = max(0, end_time - start_time)
            if requested_window > auth["max_history_seconds"]:
                return jsonify({"error": "Requested history exceeds plan limit"}), 403
    track = get_db().get_aircraft_track(
        aircraft_id=aircraft_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    record_usage("rest_request", "aircraft_track", quantity=track.num_positions, metadata={"aircraft_id": aircraft_id, "limit": limit})
    return jsonify({
        "aircraft_id": track.aircraft_id,
        "start_time": track.start_time,
        "end_time": track.end_time,
        "num_positions": track.num_positions,
        "positions": [
            {
                "timestamp": position.timestamp,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "altitude": position.altitude,
                "uncertainty": position.uncertainty,
                "num_receivers": position.num_receivers,
                "quality": {
                    "score": position.quality_score,
                    "bucket": position.quality_bucket,
                    "uncertainty_m": position.uncertainty,
                },
                "solver": {
                    "method": position.solver_method,
                    "residual_m": position.solver_residual_m,
                    "iterations": position.solver_iterations,
                },
                "correlation": {
                    "time_span_s": position.correlation_time_span_s,
                    "receiver_count": position.receiver_count,
                    "receiver_ids": _parse_receiver_ids(position.receiver_ids),
                },
            }
            for position in track.positions
        ],
    })


@api_bp.route("/api/aircraft/<aircraft_id>/latest", methods=["GET"])
def get_latest_position(aircraft_id: str):
    track = get_db().get_aircraft_track(aircraft_id=aircraft_id, limit=1)
    if track.num_positions == 0:
        return jsonify({"error": "Aircraft not found or no recent positions"}), 404

    latest = track.positions[0]
    payload = _build_position_payload(latest)
    payload["aircraft_id"] = aircraft_id
    record_usage("rest_request", "latest_position", metadata={"aircraft_id": aircraft_id})
    return jsonify(payload)


@api_bp.route("/api/statistics", methods=["GET"])
@require_plan_access(require_premium=True)
def get_statistics():
    hours = request.args.get("hours", default=24, type=int)
    db = get_db()
    active_aircraft = db.get_active_aircraft(seconds=300)
    runtime_state = get_runtime_state(db) or {}
    recent_positions = db.get_recent_positions(seconds=300)
    avg_quality_score = (
        sum(position.quality_score for position in recent_positions) / len(recent_positions)
        if recent_positions else 0
    )
    record_usage("rest_request", "statistics", metadata={"hours": hours})
    return jsonify({
        "current": {
            "active_aircraft": len(active_aircraft),
            "timestamp": datetime.now().isoformat(),
            "avg_quality_score": avg_quality_score,
            "avg_ingest_latency_ms": runtime_state.get("avg_ingest_latency_ms", 0.0),
            "avg_solve_latency_ms": runtime_state.get("avg_solve_latency_ms", 0.0),
            "avg_api_latency_ms": runtime_state.get("avg_api_latency_ms", 0.0),
            "failed_solves": runtime_state.get("failed_solves", 0),
            "rejected_groups": runtime_state.get("rejected_groups", 0),
        },
        "runtime": runtime_state,
        "database": db.get_database_stats(),
        "history": db.get_statistics_history(hours=hours),
    })


@api_bp.route("/api/map/bounds", methods=["GET"])
def get_map_bounds():
    scenario = current_app.config.get("DEMO_SCENARIO_METADATA")
    if current_app.config.get("DEMO_MODE") and scenario:
        bounds = scenario.get("map", {}).get("bounds")
        center = scenario.get("map", {}).get("center")
        if bounds and center:
            return jsonify({
                "bounds": {
                    "north": bounds["north"],
                    "south": bounds["south"],
                    "east": bounds["east"],
                    "west": bounds["west"],
                    "center": center,
                },
                "num_positions": 0,
                "source": "demo-scenario",
            })

    positions = get_db().get_recent_positions(seconds=300, limit=1000)
    if not positions:
        return jsonify({"error": "No recent positions available"}), 404

    lats = [position.latitude for position in positions]
    lons = [position.longitude for position in positions]
    return jsonify({
        "bounds": {
            "north": max(lats),
            "south": min(lats),
            "east": max(lons),
            "west": min(lons),
            "center": {
                "latitude": sum(lats) / len(lats),
                "longitude": sum(lons) / len(lons),
            },
        },
        "num_positions": len(positions),
    })


@api_bp.route("/api/admin/cleanup", methods=["POST"])
def cleanup_old_data():
    if not current_app.config["ENABLE_ADMIN_API"]:
        return jsonify({"error": "Admin API is disabled"}), 404
    if not _validate_api_key():
        return jsonify({"error": "Unauthorized"}), 403

    try:
        days = _parse_cleanup_days()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    get_db().cleanup_old_data(days=days)
    return jsonify({
        "status": "success",
        "message": f"Cleaned up data older than {days} days",
    })


@api_bp.route("/api", methods=["GET"])
def api_documentation():
    return jsonify({
        "version": "1.0.0",
        "name": "MLAT Aircraft Tracking API",
        "endpoints": {
            "GET /api/health": "Health and readiness status including DB and runtime freshness",
            "GET /api/aircraft": "List active aircraft",
            "GET /api/positions/recent": "Recent positions for all aircraft",
            "GET /api/aircraft/<id>/track": "Historical track for aircraft",
            "GET /api/aircraft/<id>/latest": "Latest position for aircraft",
            "GET /api/statistics": "Premium operational statistics and latency metrics",
            "GET /api/readiness": "Public internal quality, freshness, reliability, and evidence gates",
            "GET /api/benchmark/latest": "Latest public versioned benchmark evidence artifact",
            "GET /api/pipeline": "Receiver-to-dashboard evidence trace with provenance",
            "GET /api/evidence/metrics": "Bounded public operational history and reliability",
            "GET /api/evidence/performance/latest": "Latest reproducible operational performance report",
            "GET /api/evidence/reliability/latest": "Latest sampled availability and freshness window",
            "GET /api/map/bounds": "Bounding box for map view",
            "POST /api/admin/cleanup": "Clean up old data (admin only)",
        },
        "commercial": {
            "public_plan": current_app.config["PUBLIC_PLAN_CODE"],
            "premium_plan": current_app.config["PREMIUM_PLAN_CODE"],
            "usage_metering": ["rest_request", "stream_subscription"],
            "premium_features": ["statistics", "deep_history", "live_stream"],
        },
        "websocket": {
            "url": "/socket.io",
            "events": {
                "connect": "Connect to live updates",
                "subscribe_aircraft": "Subscribe to aircraft updates (api_key required)",
                "position_update": "Receive position updates",
            },
        },
    })


@api_bp.app_errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found"}), 404


@api_bp.app_errorhandler(500)
def internal_error(error):
    logger.error("Internal server error: %s", error)
    return jsonify({"error": "Internal server error"}), 500


@socketio.on("connect")
def handle_connect():
    logger.info("Client connected to WebSocket")
    emit("connection_response", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected from WebSocket")


@socketio.on("subscribe_aircraft")
def handle_subscribe(data):
    aircraft_id = data.get("aircraft_id")
    api_key = data.get("api_key")
    logger.info("Client subscribed to aircraft: %s", aircraft_id)

    if not api_key:
        emit("subscription_response", {"aircraft_id": aircraft_id, "status": "denied", "error": "API key required"})
        return

    auth = get_db().authenticate_api_key(api_key)
    if auth is None or auth["api_key_status"] != "active" or auth["account_status"] != "active":
        emit("subscription_response", {"aircraft_id": aircraft_id, "status": "denied", "error": "Invalid API key"})
        return
    if not auth.get("can_stream_live", False):
        emit("subscription_response", {"aircraft_id": aircraft_id, "status": "denied", "error": "Streaming plan required"})
        return
    if not _has_active_entitlement(auth, "live_stream"):
        emit("subscription_response", {"aircraft_id": aircraft_id, "status": "denied", "error": "Live stream entitlement required"})
        return

    get_db().touch_api_key(auth["api_key_id"])
    get_db().record_usage_event(
        account_id=auth["account_id"],
        api_key_id=auth["api_key_id"],
        event_type="stream_subscription",
        resource="aircraft_live",
        metadata={"aircraft_id": aircraft_id},
    )

    if SocketIO is not None:
        from flask_socketio import join_room

        join_room(aircraft_id)

    emit("subscription_response", {
        "aircraft_id": aircraft_id,
        "status": "subscribed",
        "plan": auth["plan_code"],
    })


def run_server(app: Optional[Flask] = None):
    """Run the API server."""
    app = app or create_app()
    host = app.config["API_HOST"]
    port = app.config["API_PORT"]
    debug = app.config["API_DEBUG"]

    print("\n" + "=" * 70)
    print("🚀 MLAT REST API Server Starting")
    print("=" * 70)
    print("\nEndpoints available:")
    print(f"  http://localhost:{port}/api - API Documentation")
    print(f"  http://localhost:{port}/api/health - Health Check")
    print(f"  http://localhost:{port}/api/aircraft - Active Aircraft")
    print(f"  http://localhost:{port}/api/positions/recent - Recent Positions")
    print("\nWebSocket available at:")
    if SocketIO is None:
        print("  Socket.IO unavailable in this environment; dashboard will use polling fallback")
    else:
        print(f"  ws://localhost:{port}/socket.io")
    print("\n" + "=" * 70 + "\n")

    socketio.run(app, host=host, port=port, debug=debug)


def main():
    """Console entry point for the REST API."""
    run_server()


app = create_app()


if __name__ == "__main__":
    run_server(app)
