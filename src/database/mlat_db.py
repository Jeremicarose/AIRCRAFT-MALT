"""
Database Layer for MLAT System

Stores:
- Aircraft positions
- Historical tracks
- Receiver information
- System statistics
"""

import sqlite3
import os
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoredPosition:
    """Aircraft position stored in database"""
    id: Optional[int]
    aircraft_id: str
    timestamp: float
    latitude: float
    longitude: float
    altitude: float
    uncertainty: float
    num_receivers: int
    receiver_ids: str  # JSON array
    residual: float
    created_at: str


@dataclass
class AircraftTrack:
    """A collection of positions forming a track"""
    aircraft_id: str
    start_time: float
    end_time: float
    num_positions: int
    positions: List[StoredPosition]


@dataclass
class StoredReceiver:
    """Receiver metadata stored in the database."""
    receiver_id: str
    latitude: float
    longitude: float
    altitude: float
    status: str
    last_seen: float
    capabilities: str
    updated_at: str


class MLATDatabase:
    """
    SQLite database for MLAT system.
    
    Stores aircraft positions, tracks, and system metadata.
    """
    
    def __init__(self, db_path: str = "mlat_data.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database and create tables if needed"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Connected to database: {self.db_path}")
    
    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aircraft_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                altitude REAL NOT NULL,
                uncertainty REAL NOT NULL,
                num_receivers INTEGER NOT NULL,
                receiver_ids TEXT NOT NULL,
                residual REAL NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(aircraft_id, timestamp)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aircraft_time 
            ON positions(aircraft_id, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON positions(timestamp)
        """)
        
        # Receivers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receivers (
                receiver_id TEXT PRIMARY KEY,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                altitude REAL NOT NULL,
                status TEXT NOT NULL,
                last_seen REAL NOT NULL,
                capabilities TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                total_signals INTEGER NOT NULL,
                total_positions INTEGER NOT NULL,
                active_aircraft INTEGER NOT NULL,
                active_receivers INTEGER NOT NULL,
                avg_uncertainty REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def store_position(
        self,
        aircraft_id: str,
        timestamp: float,
        latitude: float,
        longitude: float,
        altitude: float,
        uncertainty: float,
        num_receivers: int,
        receiver_ids: List[str],
        residual: float = 0.0
    ) -> int:
        """
        Store a single aircraft position.
        
        Returns: position ID
        """
        cursor = self.conn.cursor()
        
        created_at = datetime.now().isoformat()
        receiver_ids_json = json.dumps(receiver_ids)
        
        try:
            cursor.execute("""
                INSERT INTO positions (
                    aircraft_id, timestamp, latitude, longitude, altitude,
                    uncertainty, num_receivers, receiver_ids, residual, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                aircraft_id, timestamp, latitude, longitude, altitude,
                uncertainty, num_receivers, receiver_ids_json, residual, created_at
            ))
            
            self.conn.commit()
            position_id = cursor.lastrowid
            
            logger.debug(f"Stored position {position_id} for aircraft {aircraft_id}")
            return position_id
            
        except sqlite3.IntegrityError:
            # Duplicate position - update instead
            cursor.execute("""
                SELECT id FROM positions
                WHERE aircraft_id = ? AND timestamp = ?
            """, (aircraft_id, timestamp))
            existing_row = cursor.fetchone()
            existing_id = existing_row['id'] if existing_row else None

            cursor.execute("""
                UPDATE positions SET
                    latitude = ?, longitude = ?, altitude = ?,
                    uncertainty = ?, num_receivers = ?, receiver_ids = ?,
                    residual = ?, created_at = ?
                WHERE aircraft_id = ? AND timestamp = ?
            """, (
                latitude, longitude, altitude, uncertainty, num_receivers,
                receiver_ids_json, residual, created_at, aircraft_id, timestamp
            ))
            
            self.conn.commit()
            logger.debug(f"Updated position for aircraft {aircraft_id}")
            return existing_id
    
    def get_aircraft_track(
        self,
        aircraft_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000
    ) -> AircraftTrack:
        """
        Get historical track for an aircraft.
        
        Args:
            aircraft_id: Aircraft identifier
            start_time: Start of time range (optional)
            end_time: End of time range (optional)
            limit: Maximum number of positions
        
        Returns:
            AircraftTrack object with positions
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM positions WHERE aircraft_id = ?"
        params = [aircraft_id]
        
        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return AircraftTrack(
                aircraft_id=aircraft_id,
                start_time=0,
                end_time=0,
                num_positions=0,
                positions=[]
            )
        
        positions = [
            StoredPosition(
                id=row['id'],
                aircraft_id=row['aircraft_id'],
                timestamp=row['timestamp'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                altitude=row['altitude'],
                uncertainty=row['uncertainty'],
                num_receivers=row['num_receivers'],
                receiver_ids=row['receiver_ids'],
                residual=row['residual'],
                created_at=row['created_at']
            )
            for row in rows
        ]
        
        return AircraftTrack(
            aircraft_id=aircraft_id,
            start_time=positions[0].timestamp,
            end_time=positions[-1].timestamp,
            num_positions=len(positions),
            positions=positions
        )
    
    def get_recent_positions(
        self,
        seconds: int = 60,
        limit: int = 100
    ) -> List[StoredPosition]:
        """
        Get all recent positions across all aircraft.
        
        Args:
            seconds: How far back to look
            limit: Maximum positions to return
        """
        cursor = self.conn.cursor()
        
        cutoff_time = datetime.now().timestamp() - seconds
        
        cursor.execute("""
            SELECT * FROM positions
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (cutoff_time, limit))
        
        rows = cursor.fetchall()
        
        return [
            StoredPosition(
                id=row['id'],
                aircraft_id=row['aircraft_id'],
                timestamp=row['timestamp'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                altitude=row['altitude'],
                uncertainty=row['uncertainty'],
                num_receivers=row['num_receivers'],
                receiver_ids=row['receiver_ids'],
                residual=row['residual'],
                created_at=row['created_at']
            )
            for row in rows
        ]
    
    def get_active_aircraft(self, seconds: int = 300) -> List[str]:
        """
        Get list of aircraft seen in last N seconds.
        
        Args:
            seconds: Time window to check
        """
        cursor = self.conn.cursor()
        
        cutoff_time = datetime.now().timestamp() - seconds
        
        cursor.execute("""
            SELECT DISTINCT aircraft_id FROM positions
            WHERE timestamp >= ?
            ORDER BY aircraft_id
        """, (cutoff_time,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def store_statistics(
        self,
        total_signals: int,
        total_positions: int,
        active_aircraft: int,
        active_receivers: int,
        avg_uncertainty: float
    ):
        """Store system statistics snapshot"""
        cursor = self.conn.cursor()
        
        timestamp = datetime.now().timestamp()
        created_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO statistics (
                timestamp, total_signals, total_positions,
                active_aircraft, active_receivers, avg_uncertainty, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, total_signals, total_positions,
            active_aircraft, active_receivers, avg_uncertainty, created_at
        ))
        
        self.conn.commit()

    def store_receiver(
        self,
        receiver_id: str,
        latitude: float,
        longitude: float,
        altitude: float,
        status: str,
        last_seen: float,
        capabilities: List[str],
    ):
        """Insert or update a receiver record."""
        cursor = self.conn.cursor()
        updated_at = datetime.now().isoformat()
        capabilities_json = json.dumps(capabilities)

        cursor.execute("""
            INSERT INTO receivers (
                receiver_id, latitude, longitude, altitude,
                status, last_seen, capabilities, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(receiver_id) DO UPDATE SET
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                altitude = excluded.altitude,
                status = excluded.status,
                last_seen = excluded.last_seen,
                capabilities = excluded.capabilities,
                updated_at = excluded.updated_at
        """, (
            receiver_id,
            latitude,
            longitude,
            altitude,
            status,
            last_seen,
            capabilities_json,
            updated_at,
        ))

        self.conn.commit()

    def get_receivers(self) -> List[StoredReceiver]:
        """Return all receivers ordered by receiver id."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM receivers
            ORDER BY receiver_id ASC
        """)

        rows = cursor.fetchall()
        return [
            StoredReceiver(
                receiver_id=row["receiver_id"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                altitude=row["altitude"],
                status=row["status"],
                last_seen=row["last_seen"],
                capabilities=row["capabilities"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_positions_after_id(self, last_id: int, limit: int = 100) -> List[StoredPosition]:
        """Return positions with id greater than last_id in ascending order."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM positions
            WHERE id > ?
            ORDER BY id ASC
            LIMIT ?
        """, (last_id, limit))

        rows = cursor.fetchall()
        return [
            StoredPosition(
                id=row['id'],
                aircraft_id=row['aircraft_id'],
                timestamp=row['timestamp'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                altitude=row['altitude'],
                uncertainty=row['uncertainty'],
                num_receivers=row['num_receivers'],
                receiver_ids=row['receiver_ids'],
                residual=row['residual'],
                created_at=row['created_at']
            )
            for row in rows
        ]
    
    def get_statistics_history(self, hours: int = 24) -> List[Dict]:
        """Get statistics for last N hours"""
        cursor = self.conn.cursor()
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        cursor.execute("""
            SELECT * FROM statistics
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (cutoff_time,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days: int = 7):
        """
        Remove data older than N days.
        
        Args:
            days: Keep data from last N days
        """
        cursor = self.conn.cursor()
        
        cutoff_time = datetime.now().timestamp() - (days * 86400)
        
        # Delete old positions
        cursor.execute("DELETE FROM positions WHERE timestamp < ?", (cutoff_time,))
        positions_deleted = cursor.rowcount
        
        # Delete old statistics
        cursor.execute("DELETE FROM statistics WHERE timestamp < ?", (cutoff_time,))
        stats_deleted = cursor.rowcount
        
        self.conn.commit()
        
        logger.info(f"Cleaned up {positions_deleted} positions and {stats_deleted} statistics")
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        # Total positions
        cursor.execute("SELECT COUNT(*) FROM positions")
        total_positions = cursor.fetchone()[0]
        
        # Unique aircraft
        cursor.execute("SELECT COUNT(DISTINCT aircraft_id) FROM positions")
        unique_aircraft = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM positions")
        min_time, max_time = cursor.fetchone()
        
        # Database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        
        return {
            'total_positions': total_positions,
            'unique_aircraft': unique_aircraft,
            'earliest_position': datetime.fromtimestamp(min_time).isoformat() if min_time else None,
            'latest_position': datetime.fromtimestamp(max_time).isoformat() if max_time else None,
            'database_size_bytes': db_size,
            'database_size_mb': db_size / (1024 * 1024)
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Example usage
if __name__ == "__main__":
    import time
    
    # Create database
    db = MLATDatabase("test_mlat.db")
    db.connect()
    
    # Store some test positions
    print("Storing test positions...")
    
    for i in range(5):
        db.store_position(
            aircraft_id="TEST123",
            timestamp=time.time() + i,
            latitude=40.5 + i * 0.01,
            longitude=-74.0 + i * 0.01,
            altitude=9000 + i * 100,
            uncertainty=150.0,
            num_receivers=5,
            receiver_ids=["RCV1", "RCV2", "RCV3", "RCV4", "RCV5"],
            residual=45.2
        )
    
    # Get track
    print("\nRetrieving track...")
    track = db.get_aircraft_track("TEST123")
    print(f"Track: {track.num_positions} positions")
    print(f"From: {datetime.fromtimestamp(track.start_time)}")
    print(f"To: {datetime.fromtimestamp(track.end_time)}")
    
    # Get stats
    print("\nDatabase stats:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    db.close()
