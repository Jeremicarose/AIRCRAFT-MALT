"""
Production MLAT System - Main Application

Integrates all components:
- Network connectivity (CKB/4DSky)
- Signal correlation
- MLAT position solving
- Database storage
- REST API
- Live statistics
"""

import asyncio
from collections import deque
import logging
import signal
import os
import time

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    env_file = os.getenv("MLAT_ENV_FILE", os.path.join(os.getcwd(), ".env"))
    load_dotenv(dotenv_path=env_file)

from network.ckb_client import CKBReceiverNetworkClient, NetworkConfig
from correlation.correlator import RawSignal
from mlat.robust_solver import RobustMLATSolver, ReceiverPosition, SignalObservation
from database.mlat_db import MLATDatabase
from demo_scenarios import get_demo_scenario, scenario_aircraft_states
from mlat_runtime import BaseMLATRuntime
from runtime_config import DemoSettings, load_runtime_settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CURRENT_RUNTIME = None


class ProductionMLATSystem(BaseMLATRuntime[ReceiverPosition, SignalObservation]):
    """
    Production-ready MLAT system with all features integrated.
    """

    def __init__(
        self,
        config: NetworkConfig,
        db_path: str = "mlat_data.db",
        simulation_retention_hours: int = 24,
        statistics_retention_days: int = 7,
        health_stale_signal_seconds: int = 120,
        stats_interval_seconds: int = 60,
        require_live_benchmarkable_output: bool = False,
        demo_settings: DemoSettings | None = None,
    ):
        super().__init__(
            config,
            time_window=0.005,  # 5ms
            min_receivers=4,
        )
        self.solver = RobustMLATSolver(min_receivers=4)
        self.database = MLATDatabase(db_path)
        self.health_stale_signal_seconds = max(1, health_stale_signal_seconds)
        self.stats_interval_seconds = max(5, stats_interval_seconds)
        self.require_live_benchmarkable_output = require_live_benchmarkable_output
        self.solve_latencies_ms = deque(maxlen=1000)
        self.store_latencies_ms = deque(maxlen=1000)
        self.api_latencies_ms = deque(maxlen=1000)
        self.rejected_groups = 0
        self.last_successful_solve_at = 0.0
        self.last_store_at = 0.0

        # Statistics
        self.stats = {
            'start_time': time.time(),
            'total_signals': 0,
            'total_positions': 0,
            'successful_solves': 0,
            'failed_solves': 0,
            'last_position_time': 0
        }
        self.demo_settings = demo_settings or DemoSettings(
            enabled=False,
            scenario="default",
            read_only=False,
            label="",
            auto_connect=False,
            scenario_metadata={},
        )
        self.demo_scenario = get_demo_scenario(self.demo_settings.scenario)
        self.simulation_mode = config.simulate_if_unavailable and not config.receiver_registry_type_hash
        self.synthetic_feed_mode = config.fourdsky_transport == "simulation"
        self.simulation_retention_hours = max(1, simulation_retention_hours)
        self.statistics_retention_days = max(1, statistics_retention_days)

    def get_runtime_state(self) -> dict:
        """Expose current runtime health and performance state."""
        now = time.time()
        instrumentation = self.get_runtime_instrumentation()
        return {
            "is_running": self.is_running,
            "synthetic_feed_mode": self.synthetic_feed_mode,
            "require_live_benchmarkable_output": self.require_live_benchmarkable_output,
            "start_time": self.stats['start_time'],
            "uptime_s": max(0.0, now - self.stats['start_time']),
            "last_signal_at": instrumentation.get("last_signal_at", 0.0),
            "last_signal_age_s": instrumentation.get("last_signal_age_s"),
            "last_successful_solve_at": self.last_successful_solve_at,
            "last_successful_solve_age_s": (max(0.0, now - self.last_successful_solve_at) if self.last_successful_solve_at else None),
            "last_store_at": self.last_store_at,
            "last_store_age_s": (max(0.0, now - self.last_store_at) if self.last_store_at else None),
            "avg_ingest_latency_ms": instrumentation.get("avg_ingest_latency_ms", 0.0),
            "max_ingest_latency_ms": instrumentation.get("max_ingest_latency_ms", 0.0),
            "avg_solve_latency_ms": (sum(self.solve_latencies_ms) / len(self.solve_latencies_ms) if self.solve_latencies_ms else 0.0),
            "max_solve_latency_ms": (max(self.solve_latencies_ms) if self.solve_latencies_ms else 0.0),
            "avg_store_latency_ms": (sum(self.store_latencies_ms) / len(self.store_latencies_ms) if self.store_latencies_ms else 0.0),
            "max_store_latency_ms": (max(self.store_latencies_ms) if self.store_latencies_ms else 0.0),
            "avg_api_latency_ms": (sum(self.api_latencies_ms) / len(self.api_latencies_ms) if self.api_latencies_ms else 0.0),
            "max_api_latency_ms": (max(self.api_latencies_ms) if self.api_latencies_ms else 0.0),
            "failed_solves": self.stats['failed_solves'],
            "rejected_groups": self.rejected_groups,
            "active_receivers": len(self.receiver_positions),
            "buffer_size": len(self.correlator.signal_buffer),
            "stale_signal_threshold_s": self.health_stale_signal_seconds,
            "signal_fresh": (
                instrumentation.get("last_signal_age_s") is not None
                and instrumentation.get("last_signal_age_s") <= self.health_stale_signal_seconds
            ),
        }
        
    async def initialize(self):
        """Initialize the system"""
        logger.info("=" * 70)
        logger.info("🚀 PRODUCTION MLAT SYSTEM INITIALIZING")
        logger.info("=" * 70)
        
        global CURRENT_RUNTIME

        # Connect to database
        self.database.connect()
        CURRENT_RUNTIME = self
        logger.info("✅ Database connected")
        if self.synthetic_feed_mode:
            logger.info(
                "🧹 Simulation retention active: positions=%dh, statistics=%dd",
                self.simulation_retention_hours,
                self.statistics_retention_days,
            )
            if self.require_live_benchmarkable_output:
                logger.warning(
                    "⚠️ REQUIRE_LIVE_BENCHMARKABLE_OUTPUT=true but FOURDSKY_TRANSPORT=simulation. "
                    "Current output is not suitable for real external benchmarking."
                )
        if self.demo_settings.enabled:
            logger.info(
                "🎛️ Demo mode enabled: scenario=%s label=%s read_only=%s",
                self.demo_scenario.slug,
                self.demo_settings.label,
                self.demo_settings.read_only,
            )

        # Initialize network
        await self.initialize_network()
        logger.info("✅ Network initialized")
        logger.info(f"✅ Cached {len(self.receiver_positions)} receiver positions")
        
        logger.info("=" * 70)
        logger.info("✅ SYSTEM READY")
        logger.info("=" * 70)
    
    def build_receiver_position(self, receiver_id: str, info) -> ReceiverPosition:
        return ReceiverPosition(
            latitude=info.latitude,
            longitude=info.longitude,
            altitude=info.altitude,
            receiver_id=receiver_id,
        )

    def on_receiver_cached(self, receiver_id: str, info):
        self.database.store_receiver(
            receiver_id=receiver_id,
            latitude=info.latitude,
            longitude=info.longitude,
            altitude=info.altitude,
            status=info.status,
            last_seen=info.last_seen,
            capabilities=info.capabilities,
        )

    def on_signal_received(self, signal: RawSignal):
        self.stats['total_signals'] += 1

    def build_observation(
        self,
        signal: RawSignal,
        receiver_position: ReceiverPosition,
    ) -> SignalObservation:
        return SignalObservation(
            receiver_id=signal.receiver_id,
            timestamp=signal.timestamp,
            signal_data=signal.message,
            receiver_position=receiver_position,
        )
    
    async def start(self):
        """Start the MLAT system"""
        self.is_running = True
        
        logger.info("📡 Starting data stream processing...")
        
        # Start network data streaming
        await self.network_client.start_streaming(self.handle_incoming_signal)
        
        # Start processing loops
        processing_task = asyncio.create_task(self._processing_loop())
        stats_task = asyncio.create_task(self._statistics_loop())
        logger.info("✅ System running")
        
        # Wait for tasks
        await asyncio.gather(processing_task, stats_task)
    
    async def _processing_loop(self):
        """Main processing loop - correlate and solve"""
        logger.info("🔄 Processing loop started")
        
        while self.is_running:
            try:
                # Run correlation
                correlated_groups = self.correlator.correlate()
                
                # Process each group
                for group in correlated_groups:
                    await self._process_signal_group(group)
                
                # Sleep briefly
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_signal_group(self, group):
        """Process a correlated signal group"""
        observations = self.build_observations_from_group(group)

        if len(observations) < 4:
            self.rejected_groups += 1
            return

        if self.synthetic_feed_mode:
            await self._store_simulated_position(group, observations)
            return

        # Solve position
        self.stats['total_positions'] += 1
        solve_started_at = time.time()
        position = self.solver.solve_position(observations)
        self.solve_latencies_ms.append((time.time() - solve_started_at) * 1000)
        
        if position:
            self.stats['successful_solves'] += 1
            self.stats['last_position_time'] = time.time()
            self.last_successful_solve_at = self.stats['last_position_time']
            
            # Store in database
            await self._store_position(group.message, position, group=group)
            
            # Log success
            logger.info(
                f"✈️  Aircraft {group.message[:8]}: "
                f"{position.latitude:.4f}°, {position.longitude:.4f}°, "
                f"{position.altitude:.0f}m "
                f"(±{position.uncertainty:.0f}m, {position.num_receivers} rcv)"
            )
        else:
            self.stats['failed_solves'] += 1
    
    async def _store_position(self, message: str, position, group=None):
        """Store position in database"""
        # Extract aircraft ID from message
        aircraft_id = message[2:8] if len(message) >= 8 else message
        correlation_time_span_s = getattr(position, "correlation_time_span_s", 0.0)
        if group is not None:
            correlation_time_span_s = group.time_span

        try:
            store_started_at = time.time()
            self.database.store_position(
                aircraft_id=aircraft_id,
                timestamp=position.timestamp,
                latitude=position.latitude,
                longitude=position.longitude,
                altitude=position.altitude,
                uncertainty=position.uncertainty,
                num_receivers=position.num_receivers,
                receiver_ids=position.receiver_ids,
                residual=position.residual,
                quality_score=getattr(position, "quality_score", 0.0),
                quality_bucket=getattr(position, "quality_bucket", "poor"),
                solver_method=getattr(position, "solver_method", getattr(position, "method", "unknown")),
                solver_residual_m=getattr(position, "solver_residual_m", getattr(position, "residual", 0.0)),
                solver_iterations=getattr(position, "solver_iterations", getattr(position, "iterations", 0)),
                correlation_time_span_s=correlation_time_span_s,
                receiver_count=getattr(position, "receiver_count", position.num_receivers),
            )
            self.store_latencies_ms.append((time.time() - store_started_at) * 1000)
            self.last_store_at = time.time()
        except Exception as e:
            logger.error(f"Failed to store position: {e}")

    async def _store_simulated_position(self, group, observations):
        """
        In simulation mode, persist a deterministic synthetic position so the
        end-to-end API/dashboard path produces live data even though the MLAT
        solver is not yet numerically validated for the synthetic feed.
        """
        self.stats['total_positions'] += 1
        self.stats['successful_solves'] += 1
        self.stats['last_position_time'] = time.time()

        centroid_lat = sum(obs.receiver_position.latitude for obs in observations) / len(observations)
        centroid_lon = sum(obs.receiver_position.longitude for obs in observations) / len(observations)

        aircraft_id = group.message[2:8] if len(group.message) >= 8 else group.message
        replay_positions = {
            state["icao"]: state
            for state in scenario_aircraft_states(observations[0].timestamp, self.demo_scenario.slug)
        }
        synthetic_position = replay_positions.get(
            aircraft_id,
            {
                "latitude": centroid_lat,
                "longitude": centroid_lon,
                "altitude": 8000.0,
            },
        )

        try:
            receiver_count = len(observations)
            correlation_time_span_s = group.time_span if group is not None else 0.0
            quality_score = 0.72 if receiver_count >= 4 else 0.35
            quality_bucket = "good" if quality_score >= 0.65 else "fair"
            store_started_at = time.time()
            self.database.store_position(
                aircraft_id=aircraft_id,
                timestamp=observations[0].timestamp,
                latitude=synthetic_position["latitude"],
                longitude=synthetic_position["longitude"],
                altitude=synthetic_position["altitude"],
                uncertainty=150.0,
                num_receivers=receiver_count,
                receiver_ids=[obs.receiver_id for obs in observations],
                residual=0.0,
                quality_score=quality_score,
                quality_bucket=quality_bucket,
                solver_method="simulated_replay",
                solver_residual_m=0.0,
                solver_iterations=0,
                correlation_time_span_s=correlation_time_span_s,
                receiver_count=receiver_count,
            )
            self.store_latencies_ms.append((time.time() - store_started_at) * 1000)
            self.last_store_at = time.time()
            logger.info(
                "✈️  Simulated aircraft %s: %.4f°, %.4f°, %.0fm (%d rcv)",
                aircraft_id,
                synthetic_position["latitude"],
                synthetic_position["longitude"],
                synthetic_position["altitude"],
                len(observations),
            )
        except Exception as exc:
            logger.error("Failed to store simulated position: %s", exc)
    
    async def _statistics_loop(self):
        """Periodic statistics reporting and storage"""
        logger.info("📊 Statistics loop started")
        
        while self.is_running:
            await asyncio.sleep(self.stats_interval_seconds)
            
            # Calculate statistics
            runtime = time.time() - self.stats['start_time']
            active_aircraft = self.database.get_active_aircraft(seconds=300)

            # Get recent positions for uncertainty calculation
            recent_positions = self.database.get_recent_positions(seconds=300)
            avg_uncertainty = (
                sum(p.uncertainty for p in recent_positions) / len(recent_positions)
                if recent_positions else 0
            )
            avg_quality_score = (
                sum(p.quality_score for p in recent_positions) / len(recent_positions)
                if recent_positions else 0
            )
            avg_latency_ms = (
                sum(self.solve_latencies_ms) / len(self.solve_latencies_ms)
                if self.solve_latencies_ms else 0
            )
            max_latency_ms = max(self.solve_latencies_ms) if self.solve_latencies_ms else 0

            # Store statistics
            self.database.store_statistics(
                total_signals=self.stats['total_signals'],
                total_positions=self.stats['total_positions'],
                active_aircraft=len(active_aircraft),
                active_receivers=len(self.receiver_positions),
                avg_uncertainty=avg_uncertainty,
                avg_quality_score=avg_quality_score,
                avg_latency_ms=avg_latency_ms,
                max_latency_ms=max_latency_ms,
                failed_solves=self.stats['failed_solves'],
                rejected_groups=self.rejected_groups,
            )

            if self.synthetic_feed_mode:
                self.database.cleanup_simulation_data(
                    position_hours=self.simulation_retention_hours,
                    statistics_days=self.statistics_retention_days,
                )
            
            # Log statistics
            logger.info("=" * 70)
            logger.info("📊 SYSTEM STATISTICS")
            logger.info(f"  Runtime: {runtime/60:.1f} minutes")
            logger.info(f"  Signals received: {self.stats['total_signals']}")
            logger.info(f"  Positions attempted: {self.stats['total_positions']}")
            logger.info(f"  Successful: {self.stats['successful_solves']}")
            logger.info(f"  Failed: {self.stats['failed_solves']}")
            if self.stats['total_positions'] > 0:
                success_rate = 100 * self.stats['successful_solves'] / self.stats['total_positions']
                logger.info(f"  Success rate: {success_rate:.1f}%")
            logger.info(f"  Active aircraft: {len(active_aircraft)}")
            logger.info(f"  Active receivers: {len(self.receiver_positions)}")
            logger.info(f"  Avg uncertainty: {avg_uncertainty:.1f}m")
            logger.info(f"  Avg quality score: {avg_quality_score:.2f}")
            logger.info(f"  Avg solve latency: {avg_latency_ms:.1f}ms")
            logger.info(f"  Max solve latency: {max_latency_ms:.1f}ms")
            logger.info(f"  Rejected groups: {self.rejected_groups}")
            logger.info("=" * 70)

    async def stop(self):
        """Stop the system gracefully"""
        logger.info("🛑 Stopping MLAT system...")
        
        self.is_running = False
        
        # Stop network
        await self.network_client.shutdown()
        
        # Final statistics
        logger.info("=" * 70)
        logger.info("📊 FINAL STATISTICS")
        runtime = time.time() - self.stats['start_time']
        logger.info(f"  Total runtime: {runtime/60:.1f} minutes")
        logger.info(f"  Total signals: {self.stats['total_signals']}")
        logger.info(f"  Total positions: {self.stats['total_positions']}")
        logger.info(f"  Successful solves: {self.stats['successful_solves']}")
        logger.info(f"  Failed solves: {self.stats['failed_solves']}")
        
        if runtime > 0:
            logger.info(f"  Signals/second: {self.stats['total_signals']/runtime:.2f}")
            logger.info(f"  Positions/second: {self.stats['total_positions']/runtime:.2f}")
        
        logger.info("=" * 70)
        
        # Close database
        self.database.close()
        
        logger.info("✅ System stopped cleanly")


async def main():
    """Main entry point"""
    settings = load_runtime_settings(max_receivers_default=10)

    # Create system
    system = ProductionMLATSystem(
        settings.network_config,
        db_path=settings.db_path,
        simulation_retention_hours=settings.simulation_retention_hours,
        statistics_retention_days=settings.statistics_retention_days,
        health_stale_signal_seconds=settings.health_stale_signal_seconds,
        stats_interval_seconds=settings.stats_interval_seconds,
        require_live_benchmarkable_output=settings.require_live_benchmarkable_output,
        demo_settings=settings.demo,
    )
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler(sig, frame):
        logger.info(f"\n⚠️  Received signal {sig}")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize
        await system.initialize()
        
        # Start running
        await system.start()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        await system.stop()


def main_cli():
    """Console entry point for the production processor."""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MLAT AIRCRAFT LOCALIZATION SYSTEM - PRODUCTION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")

    asyncio.run(main())


if __name__ == "__main__":
    main_cli()
