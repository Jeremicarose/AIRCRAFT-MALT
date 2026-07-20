"""
Database Layer for MLAT System

Stores:
- Aircraft positions
- Historical tracks
- Receiver information
- System statistics
"""

import sqlite3
import hashlib
import os
import threading
from typing import Any, List, Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import queue

logger = logging.getLogger(__name__)

_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY_PATHS = set()
_EVENT_QUEUES: Dict[str, queue.Queue] = {}


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
    quality_score: float
    quality_bucket: str
    solver_method: str
    solver_residual_m: float
    solver_iterations: int
    correlation_time_span_s: float
    receiver_count: int
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


@dataclass
class Account:
    id: Optional[int]
    account_name: str
    contact_email: str
    status: str
    created_at: str
    updated_at: str


@dataclass
class Plan:
    id: Optional[int]
    plan_code: str
    display_name: str
    tier: str
    description: str
    max_history_seconds: int
    can_access_premium: bool
    can_stream_live: bool
    created_at: str
    updated_at: str


@dataclass
class ApiKeyRecord:
    id: Optional[int]
    account_id: int
    key_name: str
    key_prefix: str
    key_hash: str
    status: str
    plan_id: int
    created_at: str
    last_used_at: Optional[str]


@dataclass
class EntitlementRecord:
    id: Optional[int]
    account_id: int
    entitlement_code: str
    status: str
    starts_at: Optional[str]
    ends_at: Optional[str]
    metadata_json: str
    created_at: str


class MLATDatabase:
    """
    SQLite database for MLAT system.
    
    Stores aircraft positions, tracks, and system metadata.
    """
    
    def __init__(self, db_path: str = "mlat_data.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database and create tables if needed."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._ensure_schema()
        logger.debug("Connected to database: %s", self.db_path)

    def _ensure_schema(self):
        """Create the database schema once per database path for this process."""
        normalized_path = os.path.abspath(self.db_path)
        if normalized_path in _SCHEMA_READY_PATHS:
            return

        with _SCHEMA_LOCK:
            if normalized_path in _SCHEMA_READY_PATHS:
                return
            self._create_tables()
            _SCHEMA_READY_PATHS.add(normalized_path)
            logger.info("Database tables created/verified for %s", self.db_path)

    def _create_tables(self):
        """Create database schema."""
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
                quality_score REAL NOT NULL DEFAULT 0.0,
                quality_bucket TEXT NOT NULL DEFAULT 'poor',
                solver_method TEXT NOT NULL DEFAULT 'unknown',
                solver_residual_m REAL NOT NULL DEFAULT 0.0,
                solver_iterations INTEGER NOT NULL DEFAULT 0,
                correlation_time_span_s REAL NOT NULL DEFAULT 0.0,
                receiver_count INTEGER NOT NULL DEFAULT 0,
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
                successful_solves INTEGER NOT NULL DEFAULT 0,
                active_aircraft INTEGER NOT NULL,
                active_receivers INTEGER NOT NULL,
                avg_uncertainty REAL NOT NULL,
                avg_quality_score REAL NOT NULL DEFAULT 0.0,
                avg_latency_ms REAL NOT NULL DEFAULT 0.0,
                max_latency_ms REAL NOT NULL DEFAULT 0.0,
                avg_ingest_latency_ms REAL NOT NULL DEFAULT 0.0,
                max_ingest_latency_ms REAL NOT NULL DEFAULT 0.0,
                avg_store_latency_ms REAL NOT NULL DEFAULT 0.0,
                max_store_latency_ms REAL NOT NULL DEFAULT 0.0,
                discovery_latency_ms REAL NOT NULL DEFAULT 0.0,
                registry_discovery_live INTEGER NOT NULL DEFAULT 0,
                process_rss_mb REAL NOT NULL DEFAULT 0.0,
                uptime_s REAL NOT NULL DEFAULT 0.0,
                last_signal_age_s REAL,
                last_store_age_s REAL,
                synthetic_feed_mode INTEGER NOT NULL DEFAULT 0,
                failed_solves INTEGER NOT NULL DEFAULT 0,
                rejected_groups INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL UNIQUE,
                contact_email TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_code TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                tier TEXT NOT NULL,
                description TEXT NOT NULL,
                max_history_seconds INTEGER NOT NULL,
                can_access_premium INTEGER NOT NULL DEFAULT 0,
                can_stream_live INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                key_name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                plan_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                FOREIGN KEY(account_id) REFERENCES accounts(id),
                FOREIGN KEY(plan_id) REFERENCES plans(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entitlements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                entitlement_code TEXT NOT NULL,
                status TEXT NOT NULL,
                starts_at TEXT,
                ends_at TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                api_key_id INTEGER,
                event_type TEXT NOT NULL,
                resource TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id),
                FOREIGN KEY(api_key_id) REFERENCES api_keys(id)
            )
        """)

        self._seed_default_plans(cursor)
        self.conn.commit()
    
    def _seed_default_plans(self, cursor: sqlite3.Cursor):
        created_at = datetime.now().isoformat()
        default_plans = [
            ("public_demo", "Public Demo", "public", "Public demo access with shallow history and no premium outputs.", 900, 0, 0, created_at, created_at),
            ("premium", "Premium", "premium", "Premium access to quality-enriched outputs, live streams, and deeper history.", 86400, 1, 1, created_at, created_at),
        ]
        cursor.executemany(
            """
            INSERT INTO plans (
                plan_code, display_name, tier, description, max_history_seconds,
                can_access_premium, can_stream_live, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plan_code) DO UPDATE SET
                display_name = excluded.display_name,
                tier = excluded.tier,
                description = excluded.description,
                max_history_seconds = excluded.max_history_seconds,
                can_access_premium = excluded.can_access_premium,
                can_stream_live = excluded.can_stream_live,
                updated_at = excluded.updated_at
            """,
            default_plans,
        )

    def _hash_api_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

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
        residual: float = 0.0,
        quality_score: float = 0.0,
        quality_bucket: str = "poor",
        solver_method: str = "unknown",
        solver_residual_m: float = 0.0,
        solver_iterations: int = 0,
        correlation_time_span_s: float = 0.0,
        receiver_count: int = 0,
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
                    uncertainty, num_receivers, receiver_ids, residual,
                    quality_score, quality_bucket, solver_method, solver_residual_m,
                    solver_iterations, correlation_time_span_s, receiver_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                aircraft_id, timestamp, latitude, longitude, altitude,
                uncertainty, num_receivers, receiver_ids_json, residual,
                quality_score, quality_bucket, solver_method, solver_residual_m,
                solver_iterations, correlation_time_span_s, receiver_count, created_at
            ))
            
            self.conn.commit()
            position_id = cursor.lastrowid
            self.publish_position_event(position_id)

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
                    residual = ?, quality_score = ?, quality_bucket = ?,
                    solver_method = ?, solver_residual_m = ?, solver_iterations = ?,
                    correlation_time_span_s = ?, receiver_count = ?, created_at = ?
                WHERE aircraft_id = ? AND timestamp = ?
            """, (
                latitude, longitude, altitude, uncertainty, num_receivers,
                receiver_ids_json, residual, quality_score, quality_bucket,
                solver_method, solver_residual_m, solver_iterations,
                correlation_time_span_s, receiver_count, created_at, aircraft_id, timestamp
            ))
            
            self.conn.commit()
            if existing_id is not None:
                self.publish_position_event(existing_id)
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
                quality_score=row['quality_score'],
                quality_bucket=row['quality_bucket'],
                solver_method=row['solver_method'],
                solver_residual_m=row['solver_residual_m'],
                solver_iterations=row['solver_iterations'],
                correlation_time_span_s=row['correlation_time_span_s'],
                receiver_count=row['receiver_count'],
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
                quality_score=row['quality_score'],
                quality_bucket=row['quality_bucket'],
                solver_method=row['solver_method'],
                solver_residual_m=row['solver_residual_m'],
                solver_iterations=row['solver_iterations'],
                correlation_time_span_s=row['correlation_time_span_s'],
                receiver_count=row['receiver_count'],
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
        avg_uncertainty: float,
        avg_quality_score: float = 0.0,
        avg_latency_ms: float = 0.0,
        max_latency_ms: float = 0.0,
        failed_solves: int = 0,
        rejected_groups: int = 0,
        successful_solves: int = 0,
        avg_ingest_latency_ms: float = 0.0,
        max_ingest_latency_ms: float = 0.0,
        avg_store_latency_ms: float = 0.0,
        max_store_latency_ms: float = 0.0,
        discovery_latency_ms: float = 0.0,
        registry_discovery_live: bool = False,
        process_rss_mb: float = 0.0,
        uptime_s: float = 0.0,
        last_signal_age_s: Optional[float] = None,
        last_store_age_s: Optional[float] = None,
        synthetic_feed_mode: bool = False,
    ):
        """Store system statistics snapshot"""
        cursor = self.conn.cursor()

        timestamp = datetime.now().timestamp()
        created_at = datetime.now().isoformat()

        columns = {row[1] for row in cursor.execute("PRAGMA table_info(statistics)")}
        migrations = {
            "avg_quality_score": "REAL NOT NULL DEFAULT 0.0",
            "avg_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "max_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "failed_solves": "INTEGER NOT NULL DEFAULT 0",
            "rejected_groups": "INTEGER NOT NULL DEFAULT 0",
            "successful_solves": "INTEGER NOT NULL DEFAULT 0",
            "avg_ingest_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "max_ingest_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "avg_store_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "max_store_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "discovery_latency_ms": "REAL NOT NULL DEFAULT 0.0",
            "registry_discovery_live": "INTEGER NOT NULL DEFAULT 0",
            "process_rss_mb": "REAL NOT NULL DEFAULT 0.0",
            "uptime_s": "REAL NOT NULL DEFAULT 0.0",
            "last_signal_age_s": "REAL",
            "last_store_age_s": "REAL",
            "synthetic_feed_mode": "INTEGER NOT NULL DEFAULT 0",
        }
        for column_name, definition in migrations.items():
            if column_name not in columns:
                cursor.execute(
                    f"ALTER TABLE statistics ADD COLUMN {column_name} {definition}"
                )

        payload = {
            "timestamp": timestamp,
            "total_signals": total_signals,
            "total_positions": total_positions,
            "successful_solves": successful_solves,
            "active_aircraft": active_aircraft,
            "active_receivers": active_receivers,
            "avg_uncertainty": avg_uncertainty,
            "avg_quality_score": avg_quality_score,
            "avg_latency_ms": avg_latency_ms,
            "max_latency_ms": max_latency_ms,
            "avg_ingest_latency_ms": avg_ingest_latency_ms,
            "max_ingest_latency_ms": max_ingest_latency_ms,
            "avg_store_latency_ms": avg_store_latency_ms,
            "max_store_latency_ms": max_store_latency_ms,
            "discovery_latency_ms": discovery_latency_ms,
            "registry_discovery_live": int(registry_discovery_live),
            "process_rss_mb": process_rss_mb,
            "uptime_s": uptime_s,
            "last_signal_age_s": last_signal_age_s,
            "last_store_age_s": last_store_age_s,
            "synthetic_feed_mode": int(synthetic_feed_mode),
            "failed_solves": failed_solves,
            "rejected_groups": rejected_groups,
            "created_at": created_at,
        }
        column_sql = ", ".join(payload)
        placeholder_sql = ", ".join("?" for _ in payload)
        cursor.execute(
            f"INSERT INTO statistics ({column_sql}) VALUES ({placeholder_sql})",
            tuple(payload.values()),
        )

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

    def touch_receiver(self, receiver_id: str, last_seen: float) -> bool:
        """Update receiver freshness after an observation is ingested."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE receivers
            SET last_seen = ?, status = 'online', updated_at = ?
            WHERE receiver_id = ?
            """,
            (last_seen, datetime.now().isoformat(), receiver_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def _row_to_stored_position(self, row: sqlite3.Row) -> StoredPosition:
        return StoredPosition(
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
            quality_score=row['quality_score'],
            quality_bucket=row['quality_bucket'],
            solver_method=row['solver_method'],
            solver_residual_m=row['solver_residual_m'],
            solver_iterations=row['solver_iterations'],
            correlation_time_span_s=row['correlation_time_span_s'],
            receiver_count=row['receiver_count'],
            created_at=row['created_at']
        )

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
        return [self._row_to_stored_position(row) for row in rows]

    def get_position_by_id(self, position_id: int) -> Optional[StoredPosition]:
        """Return a position by primary key."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
        row = cursor.fetchone()
        return self._row_to_stored_position(row) if row else None

    def get_latest_position(self) -> Optional[StoredPosition]:
        """Return the most recently stored position across all aircraft."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return self._row_to_stored_position(row) if row else None

    def get_or_create_position_queue(self) -> queue.Queue:
        """Return a process-local queue for immediate position events."""
        normalized_path = os.path.abspath(self.db_path)
        return _EVENT_QUEUES.setdefault(normalized_path, queue.Queue())

    def publish_position_event(self, position_id: int):
        """Publish a new or updated position id to the local event queue."""
        self.get_or_create_position_queue().put(position_id)

    def create_account(self, account_name: str, contact_email: str, status: str = "active") -> int:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO accounts (account_name, contact_email, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (account_name, contact_email, status, now, now),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_account_by_name(self, account_name: str) -> Optional[Account]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE account_name = ?", (account_name,))
        row = cursor.fetchone()
        if row is None:
            return None
        return Account(**dict(row))

    def get_plan_by_code(self, plan_code: str) -> Optional[Plan]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM plans WHERE plan_code = ?", (plan_code,))
        row = cursor.fetchone()
        if row is None:
            return None
        record = dict(row)
        record["can_access_premium"] = bool(record["can_access_premium"])
        record["can_stream_live"] = bool(record["can_stream_live"])
        return Plan(**record)

    def create_api_key(
        self,
        *,
        account_id: int,
        key_name: str,
        raw_key: str,
        plan_id: int,
        status: str = "active",
    ) -> int:
        cursor = self.conn.cursor()
        created_at = datetime.now().isoformat()
        key_prefix = raw_key[:8]
        key_hash = self._hash_api_key(raw_key)
        cursor.execute(
            """
            INSERT INTO api_keys (
                account_id, key_name, key_prefix, key_hash, status, plan_id, created_at, last_used_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (account_id, key_name, key_prefix, key_hash, status, plan_id, created_at, None),
        )
        self.conn.commit()
        return cursor.lastrowid

    def create_entitlement(
        self,
        *,
        account_id: int,
        entitlement_code: str,
        status: str = "active",
        starts_at: Optional[str] = None,
        ends_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        cursor = self.conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO entitlements (
                account_id, entitlement_code, status, starts_at, ends_at, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                entitlement_code,
                status,
                starts_at,
                ends_at,
                json.dumps(metadata or {}),
                created_at,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def authenticate_api_key(self, raw_key: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        key_hash = self._hash_api_key(raw_key)
        cursor.execute(
            """
            SELECT
                api_keys.id AS api_key_id,
                api_keys.key_name,
                api_keys.status AS api_key_status,
                api_keys.last_used_at,
                accounts.id AS account_id,
                accounts.account_name,
                accounts.contact_email,
                accounts.status AS account_status,
                plans.id AS plan_id,
                plans.plan_code,
                plans.display_name,
                plans.tier,
                plans.max_history_seconds,
                plans.can_access_premium,
                plans.can_stream_live
            FROM api_keys
            JOIN accounts ON accounts.id = api_keys.account_id
            JOIN plans ON plans.id = api_keys.plan_id
            WHERE api_keys.key_hash = ?
            """,
            (key_hash,),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        cursor.execute(
            """
            SELECT entitlement_code, status, starts_at, ends_at, metadata_json
            FROM entitlements
            WHERE account_id = ?
            """,
            (row["account_id"],),
        )
        entitlements = []
        for entitlement in cursor.fetchall():
            entitlements.append(
                {
                    "entitlement_code": entitlement["entitlement_code"],
                    "status": entitlement["status"],
                    "starts_at": entitlement["starts_at"],
                    "ends_at": entitlement["ends_at"],
                    "metadata": json.loads(entitlement["metadata_json"]),
                }
            )

        record = dict(row)
        record["can_access_premium"] = bool(record["can_access_premium"])
        record["can_stream_live"] = bool(record["can_stream_live"])
        record["entitlements"] = entitlements
        return record

    def touch_api_key(self, api_key_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
            (datetime.now().isoformat(), api_key_id),
        )
        self.conn.commit()

    def record_usage_event(
        self,
        *,
        account_id: Optional[int],
        api_key_id: Optional[int],
        event_type: str,
        resource: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO usage_events (
                account_id, api_key_id, event_type, resource, quantity, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                api_key_id,
                event_type,
                resource,
                quantity,
                json.dumps(metadata or {}),
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_usage_summary(self, account_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT event_type, resource, SUM(quantity) AS total_quantity
            FROM usage_events
            WHERE account_id = ?
            GROUP BY event_type, resource
            ORDER BY event_type, resource
            """,
            (account_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

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

    def get_latest_statistics(self) -> Optional[Dict[str, Any]]:
        """Return the newest processor statistics snapshot."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM statistics ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    
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

    def cleanup_simulation_data(self, position_hours: int = 24, statistics_days: int = 7):
        """
        Remove old simulated/demo-era data while preserving recent operational history.

        Args:
            position_hours: Keep position rows from the last N hours.
            statistics_days: Keep statistics rows from the last N days.
        """
        cursor = self.conn.cursor()

        position_cutoff = datetime.now().timestamp() - (position_hours * 3600)
        statistics_cutoff = datetime.now().timestamp() - (statistics_days * 86400)

        cursor.execute("DELETE FROM positions WHERE timestamp < ?", (position_cutoff,))
        positions_deleted = cursor.rowcount

        cursor.execute("DELETE FROM statistics WHERE timestamp < ?", (statistics_cutoff,))
        stats_deleted = cursor.rowcount

        self.conn.commit()

        if positions_deleted or stats_deleted:
            logger.info(
                "Pruned %d old positions and %d old statistics rows "
                "(retention: %dh positions, %dd statistics)",
                positions_deleted,
                stats_deleted,
                position_hours,
                statistics_days,
            )
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
        
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]

        return {
            'total_positions': total_positions,
            'unique_aircraft': unique_aircraft,
            'earliest_position': datetime.fromtimestamp(min_time).isoformat() if min_time else None,
            'latest_position': datetime.fromtimestamp(max_time).isoformat() if max_time else None,
            'database_size_bytes': db_size,
            'database_size_mb': db_size / (1024 * 1024),
            'journal_mode': journal_mode,
            'sqlite_single_node_only': True,
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("Database connection closed")


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
