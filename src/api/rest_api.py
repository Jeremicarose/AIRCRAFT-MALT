"""
REST API for the MLAT system.

This module uses an app-factory pattern and request-scoped database access.
"""

from __future__ import annotations

from flask import Blueprint, Flask, current_app, g, jsonify, request
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

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

from database.mlat_db import MLATDatabase


if load_dotenv is not None:
    load_dotenv()


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


def load_app_config() -> Dict[str, object]:
    """Load API configuration from environment."""
    return {
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "mlat_data.db"),
        "CORS_ALLOWED_ORIGINS": _split_csv("CORS_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS),
        "ENABLE_ADMIN_API": _env_bool("ENABLE_ADMIN_API", False),
        "ENABLE_BACKGROUND_BROADCASTER": _env_bool("ENABLE_BACKGROUND_BROADCASTER", True),
        "ADMIN_API_KEY": os.getenv("ADMIN_API_KEY") or os.getenv("API_KEY"),
        "API_KEY_HEADER": os.getenv("API_KEY_HEADER", "X-API-Key"),
        "API_HOST": os.getenv("API_HOST", "0.0.0.0"),
        "API_PORT": int(os.getenv("API_PORT", "5000")),
        "API_DEBUG": _env_bool("API_DEBUG", False),
    }


def create_app(config_overrides: Optional[Dict[str, object]] = None) -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.update(load_app_config())
    if config_overrides:
        app.config.update(config_overrides)

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


def broadcast_position_update(aircraft_id: str, position_data: Dict):
    """Broadcast a position update to websocket clients."""
    payload = {
        "aircraft_id": aircraft_id,
        "position": position_data,
    }
    socketio.emit("position_update", payload)
    socketio.emit("position_update", payload, room=aircraft_id)


def _start_background_broadcaster(app: Flask):
    """Poll the database for new positions and emit websocket updates."""
    with _broadcast_lock:
        if app.extensions.get("mlat_broadcaster_started"):
            return
        app.extensions["mlat_broadcaster_started"] = True

    def _poll_new_positions():
        poll_db = MLATDatabase(app.config["DATABASE_PATH"])
        poll_db.connect()
        last_position_id = 0

        try:
            existing = poll_db.get_recent_positions(seconds=86400, limit=1)
            if existing and existing[0].id is not None:
                last_position_id = existing[0].id

            while True:
                new_positions = poll_db.get_positions_after_id(last_position_id, limit=200)
                for position in new_positions:
                    last_position_id = max(last_position_id, position.id or 0)
                    broadcast_position_update(
                        aircraft_id=position.aircraft_id,
                        position_data={
                            "id": position.id,
                            "timestamp": position.timestamp,
                            "latitude": position.latitude,
                            "longitude": position.longitude,
                            "altitude": position.altitude,
                            "uncertainty": position.uncertainty,
                            "num_receivers": position.num_receivers,
                            "created_at": position.created_at,
                        },
                    )

                socketio.sleep(1.0)
        finally:
            poll_db.close()

    socketio.start_background_task(_poll_new_positions)


@api_bp.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "MLAT API",
    })


@api_bp.route("/api/aircraft", methods=["GET"])
def get_aircraft_list():
    seconds = request.args.get("seconds", default=300, type=int)
    aircraft_ids = get_db().get_active_aircraft(seconds=seconds)
    return jsonify({
        "aircraft": aircraft_ids,
        "count": len(aircraft_ids),
        "time_window_seconds": seconds,
    })


@api_bp.route("/api/positions/recent", methods=["GET"])
def get_recent_positions():
    seconds = request.args.get("seconds", default=60, type=int)
    limit = request.args.get("limit", default=100, type=int)
    positions = get_db().get_recent_positions(seconds=seconds, limit=limit)
    positions_data = [
        {
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
            "created_at": position.created_at,
        }
        for position in positions
    ]
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
    start_time = request.args.get("start_time", type=float)
    end_time = request.args.get("end_time", type=float)
    limit = request.args.get("limit", default=1000, type=int)
    track = get_db().get_aircraft_track(
        aircraft_id=aircraft_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
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
    return jsonify({
        "aircraft_id": aircraft_id,
        "timestamp": latest.timestamp,
        "position": {
            "latitude": latest.latitude,
            "longitude": latest.longitude,
            "altitude": latest.altitude,
        },
        "uncertainty": latest.uncertainty,
        "num_receivers": latest.num_receivers,
        "created_at": latest.created_at,
    })


@api_bp.route("/api/statistics", methods=["GET"])
def get_statistics():
    hours = request.args.get("hours", default=24, type=int)
    db = get_db()
    active_aircraft = db.get_active_aircraft(seconds=300)
    return jsonify({
        "current": {
            "active_aircraft": len(active_aircraft),
            "timestamp": datetime.now().isoformat(),
        },
        "database": db.get_database_stats(),
        "history": db.get_statistics_history(hours=hours),
    })


@api_bp.route("/api/map/bounds", methods=["GET"])
def get_map_bounds():
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
            "GET /api/health": "Health check",
            "GET /api/aircraft": "List active aircraft",
            "GET /api/positions/recent": "Recent positions for all aircraft",
            "GET /api/aircraft/<id>/track": "Historical track for aircraft",
            "GET /api/aircraft/<id>/latest": "Latest position for aircraft",
            "GET /api/statistics": "System statistics",
            "GET /api/map/bounds": "Bounding box for map view",
            "POST /api/admin/cleanup": "Clean up old data (admin only)",
        },
        "websocket": {
            "url": "/socket.io",
            "events": {
                "connect": "Connect to live updates",
                "subscribe_aircraft": "Subscribe to aircraft updates",
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
    logger.info("Client subscribed to aircraft: %s", aircraft_id)

    if SocketIO is not None:
        from flask_socketio import join_room

        join_room(aircraft_id)

    emit("subscription_response", {
        "aircraft_id": aircraft_id,
        "status": "subscribed",
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
