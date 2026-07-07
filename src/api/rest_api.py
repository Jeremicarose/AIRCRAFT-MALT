"""
REST API for the MLAT system.

This module uses an app-factory pattern and request-scoped database access.
"""

from __future__ import annotations

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
from production_main import CURRENT_RUNTIME


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
    demo_enabled = _env_bool("DEMO_MODE", False)
    demo_scenario_name = os.getenv("DEMO_SCENARIO", "default")
    demo_scenario = get_demo_scenario(demo_scenario_name)
    demo_label = os.getenv("DEMO_LABEL", demo_scenario.label)
    simulation_mode = os.getenv("FOURDSKY_TRANSPORT", "auto") == "simulation" or _env_bool(
        "SIMULATE_IF_UNAVAILABLE",
        True,
    )
    cwd_visualization_dir = Path(os.getcwd()) / "src" / "visualization"
    package_visualization_dir = Path(__file__).resolve().parents[1] / "visualization"
    visualization_dir = (
        cwd_visualization_dir
        if cwd_visualization_dir.exists()
        else package_visualization_dir
    )
    return {
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "mlat_data.db"),
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
        "DEMO_MODE": demo_enabled,
        "DEMO_SCENARIO": demo_scenario.slug,
        "DEMO_READ_ONLY": _env_bool("DEMO_READ_ONLY", demo_enabled),
        "DEMO_LABEL": demo_label,
        "DEMO_AUTO_CONNECT": _env_bool("DEMO_AUTO_CONNECT", demo_enabled),
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


def get_runtime_state() -> Optional[Dict[str, object]]:
    if CURRENT_RUNTIME is None:
        return None
    return CURRENT_RUNTIME.get_runtime_state()


def record_api_latency(started_at: float):
    runtime = CURRENT_RUNTIME
    if runtime is not None:
        runtime.api_latencies_ms.append((time.time() - started_at) * 1000)


def _build_position_payload(position: StoredPosition) -> Dict:
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
                        position_data={
                            "id": payload["id"],
                            "timestamp": payload["timestamp"],
                            "latitude": payload["position"]["latitude"],
                            "longitude": payload["position"]["longitude"],
                            "altitude": payload["position"]["altitude"],
                            "uncertainty": payload["uncertainty"],
                            "num_receivers": payload["num_receivers"],
                            "quality": payload["quality"],
                            "solver": payload["solver"],
                            "correlation": payload["correlation"],
                            "created_at": payload["created_at"],
                        },
                    )
                except queue.Empty:
                    new_positions = poll_db.get_positions_after_id(last_position_id, limit=200)
                    for position in new_positions:
                        last_position_id = max(last_position_id, position.id or 0)
                        payload = _build_position_payload(position)
                        broadcast_position_update(
                            aircraft_id=position.aircraft_id,
                            position_data={
                                "id": payload["id"],
                                "timestamp": payload["timestamp"],
                                "latitude": payload["position"]["latitude"],
                                "longitude": payload["position"]["longitude"],
                                "altitude": payload["position"]["altitude"],
                                "uncertainty": payload["uncertainty"],
                                "num_receivers": payload["num_receivers"],
                                "quality": payload["quality"],
                                "solver": payload["solver"],
                                "correlation": payload["correlation"],
                                "created_at": payload["created_at"],
                            },
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


@api_bp.route("/api/health", methods=["GET"])
def health_check():
    db = get_db()
    db_stats = db.get_database_stats()
    runtime_state = get_runtime_state() or {}
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
    runtime_state = get_runtime_state() or {}
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
        if position.solver_method in {"simulated_replay", "simulation", "unknown"}
    )
    benchmarkable_output = position_count > 0 and simulated_positions == 0
    max_last_store_age = runtime_state.get("last_store_age_s")
    signal_fresh = bool(runtime_state.get("signal_fresh"))
    failed_solves = int(runtime_state.get("failed_solves", 0))
    rejected_groups = int(runtime_state.get("rejected_groups", 0))
    active_receivers = len([row for row in receiver_rows if row.status == "online"])

    quality_ready = position_count > 0 and avg_quality_score >= 0.65 and avg_receiver_count >= 4
    freshness_ready = max_last_store_age is not None and max_last_store_age <= 30
    reliability_ready = signal_fresh and active_receivers >= 4 and failed_solves == 0
    packaging_ready = True

    return jsonify({
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
    runtime_state = get_runtime_state() or {}
    return jsonify(
        {
            "mode": "demo" if demo_mode else "simulation" if current_app.config["SIMULATION_MODE"] else "live",
            "simulation_mode": bool(current_app.config["SIMULATION_MODE"]),
            "demo_mode": demo_mode,
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
            "websocket_available": SocketIO is not None,
            "synthetic_feed_mode": bool(runtime_state.get("synthetic_feed_mode", current_app.config["SIMULATION_MODE"])),
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
    runtime_state = get_runtime_state() or {}
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
