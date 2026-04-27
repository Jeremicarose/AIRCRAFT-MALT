"""
REST API for MLAT System

Provides HTTP endpoints for:
- Getting current aircraft positions
- Retrieving historical tracks
- System status and statistics
- Live position streaming (WebSocket)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mlat_db import MLATDatabase

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web access
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
db = MLATDatabase("mlat_data.db")
db.connect()


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'MLAT API'
    })


@app.route('/api/aircraft', methods=['GET'])
def get_aircraft_list():
    """
    Get list of active aircraft.
    
    Query params:
        - seconds: Time window (default: 300)
    
    Example: GET /api/aircraft?seconds=60
    """
    seconds = request.args.get('seconds', default=300, type=int)
    
    aircraft_ids = db.get_active_aircraft(seconds=seconds)
    
    return jsonify({
        'aircraft': aircraft_ids,
        'count': len(aircraft_ids),
        'time_window_seconds': seconds
    })


@app.route('/api/positions/recent', methods=['GET'])
def get_recent_positions():
    """
    Get recent positions for all aircraft.
    
    Query params:
        - seconds: How far back to look (default: 60)
        - limit: Max positions to return (default: 100)
    
    Example: GET /api/positions/recent?seconds=30&limit=50
    """
    seconds = request.args.get('seconds', default=60, type=int)
    limit = request.args.get('limit', default=100, type=int)
    
    positions = db.get_recent_positions(seconds=seconds, limit=limit)
    
    # Convert to JSON-friendly format
    positions_data = [
        {
            'id': p.id,
            'aircraft_id': p.aircraft_id,
            'timestamp': p.timestamp,
            'position': {
                'latitude': p.latitude,
                'longitude': p.longitude,
                'altitude': p.altitude
            },
            'uncertainty': p.uncertainty,
            'num_receivers': p.num_receivers,
            'created_at': p.created_at
        }
        for p in positions
    ]
    
    return jsonify({
        'positions': positions_data,
        'count': len(positions_data),
        'time_window_seconds': seconds
    })


@app.route('/api/aircraft/<aircraft_id>/track', methods=['GET'])
def get_aircraft_track(aircraft_id: str):
    """
    Get historical track for specific aircraft.
    
    Query params:
        - start_time: Unix timestamp (optional)
        - end_time: Unix timestamp (optional)
        - limit: Max positions (default: 1000)
    
    Example: GET /api/aircraft/ABC123/track?limit=500
    """
    start_time = request.args.get('start_time', type=float)
    end_time = request.args.get('end_time', type=float)
    limit = request.args.get('limit', default=1000, type=int)
    
    track = db.get_aircraft_track(
        aircraft_id=aircraft_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    # Convert to JSON
    positions_data = [
        {
            'timestamp': p.timestamp,
            'latitude': p.latitude,
            'longitude': p.longitude,
            'altitude': p.altitude,
            'uncertainty': p.uncertainty,
            'num_receivers': p.num_receivers
        }
        for p in track.positions
    ]
    
    return jsonify({
        'aircraft_id': track.aircraft_id,
        'start_time': track.start_time,
        'end_time': track.end_time,
        'num_positions': track.num_positions,
        'positions': positions_data
    })


@app.route('/api/aircraft/<aircraft_id>/latest', methods=['GET'])
def get_latest_position(aircraft_id: str):
    """
    Get most recent position for specific aircraft.
    
    Example: GET /api/aircraft/ABC123/latest
    """
    track = db.get_aircraft_track(aircraft_id=aircraft_id, limit=1)
    
    if track.num_positions == 0:
        return jsonify({
            'error': 'Aircraft not found or no recent positions'
        }), 404
    
    latest = track.positions[0]
    
    return jsonify({
        'aircraft_id': aircraft_id,
        'timestamp': latest.timestamp,
        'position': {
            'latitude': latest.latitude,
            'longitude': latest.longitude,
            'altitude': latest.altitude
        },
        'uncertainty': latest.uncertainty,
        'num_receivers': latest.num_receivers,
        'created_at': latest.created_at
    })


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get system statistics.
    
    Query params:
        - hours: History to include (default: 24)
    
    Example: GET /api/statistics?hours=12
    """
    hours = request.args.get('hours', default=24, type=int)
    
    # Get database stats
    db_stats = db.get_database_stats()
    
    # Get statistics history
    stats_history = db.get_statistics_history(hours=hours)
    
    # Get current active aircraft
    active_aircraft = db.get_active_aircraft(seconds=300)
    
    return jsonify({
        'current': {
            'active_aircraft': len(active_aircraft),
            'timestamp': datetime.now().isoformat()
        },
        'database': db_stats,
        'history': stats_history
    })


@app.route('/api/map/bounds', methods=['GET'])
def get_map_bounds():
    """
    Get bounding box for recent aircraft positions.
    Useful for auto-zooming maps.
    
    Example: GET /api/map/bounds
    """
    positions = db.get_recent_positions(seconds=300, limit=1000)
    
    if not positions:
        return jsonify({
            'error': 'No recent positions available'
        }), 404
    
    lats = [p.latitude for p in positions]
    lons = [p.longitude for p in positions]
    
    return jsonify({
        'bounds': {
            'north': max(lats),
            'south': min(lats),
            'east': max(lons),
            'west': min(lons),
            'center': {
                'latitude': sum(lats) / len(lats),
                'longitude': sum(lons) / len(lons)
            }
        },
        'num_positions': len(positions)
    })


# ============================================================================
# WebSocket for Live Updates
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected to WebSocket"""
    logger.info('Client connected to WebSocket')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected from WebSocket"""
    logger.info('Client disconnected from WebSocket')


@socketio.on('subscribe_aircraft')
def handle_subscribe(data):
    """
    Subscribe to updates for specific aircraft.
    
    Data: {'aircraft_id': 'ABC123'}
    """
    aircraft_id = data.get('aircraft_id')
    logger.info(f'Client subscribed to aircraft: {aircraft_id}')
    
    # Join room for this aircraft
    from flask_socketio import join_room
    join_room(aircraft_id)
    
    emit('subscription_response', {
        'aircraft_id': aircraft_id,
        'status': 'subscribed'
    })


def broadcast_position_update(aircraft_id: str, position_data: Dict):
    """
    Broadcast position update to all subscribed clients.
    
    Call this from the main MLAT system when a new position is calculated.
    """
    socketio.emit('position_update', {
        'aircraft_id': aircraft_id,
        'position': position_data
    }, room=aircraft_id)


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.route('/api/admin/cleanup', methods=['POST'])
def cleanup_old_data():
    """
    Admin endpoint to clean up old data.
    
    Body: {'days': 7}
    """
    data = request.get_json()
    days = data.get('days', 7)
    
    db.cleanup_old_data(days=days)
    
    return jsonify({
        'status': 'success',
        'message': f'Cleaned up data older than {days} days'
    })


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Documentation Endpoint
# ============================================================================

@app.route('/api', methods=['GET'])
def api_documentation():
    """API documentation"""
    return jsonify({
        'version': '1.0.0',
        'name': 'MLAT Aircraft Tracking API',
        'endpoints': {
            'GET /api/health': 'Health check',
            'GET /api/aircraft': 'List active aircraft',
            'GET /api/positions/recent': 'Recent positions for all aircraft',
            'GET /api/aircraft/<id>/track': 'Historical track for aircraft',
            'GET /api/aircraft/<id>/latest': 'Latest position for aircraft',
            'GET /api/statistics': 'System statistics',
            'GET /api/map/bounds': 'Bounding box for map view',
            'POST /api/admin/cleanup': 'Clean up old data (admin only)'
        },
        'websocket': {
            'url': '/socket.io',
            'events': {
                'connect': 'Connect to live updates',
                'subscribe_aircraft': 'Subscribe to aircraft updates',
                'position_update': 'Receive position updates'
            }
        }
    })


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 MLAT REST API Server Starting")
    print("=" * 70)
    print("\nEndpoints available:")
    print("  http://localhost:5000/api - API Documentation")
    print("  http://localhost:5000/api/health - Health Check")
    print("  http://localhost:5000/api/aircraft - Active Aircraft")
    print("  http://localhost:5000/api/positions/recent - Recent Positions")
    print("\nWebSocket available at:")
    print("  ws://localhost:5000/socket.io")
    print("\n" + "=" * 70 + "\n")
    
    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
