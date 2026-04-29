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
import logging
import signal
import sys
import os
from typing import Dict
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

from network.ckb_client import CKBNeuronNetworkClient, NetworkConfig
from correlation.correlator import SignalCorrelator, RawSignal
from mlat.robust_solver import RobustMLATSolver, ReceiverPosition, SignalObservation
from database.mlat_db import MLATDatabase

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_runtime_settings() -> tuple[NetworkConfig, str]:
    """Load CKB and storage configuration from environment."""
    fourdsky_endpoint = os.getenv("FOURDSKYENDPOINT") or os.getenv(
        "FOURDSKY_ENDPOINT",
        "wss://api.4dsky.com/stream",
    )
    fourdsky_api_key = os.getenv("FOURDSKYAPIKEY") or os.getenv("FOURDSKY_API_KEY")

    config = NetworkConfig(
        ckb_network=os.getenv("CKB_NETWORK", "testnet"),
        ckb_rpc_url=os.getenv("CKB_RPC_URL", "https://testnet.ckb.dev/rpc"),
        ckb_indexer_url=os.getenv("CKB_INDEXER_URL", "https://testnet.ckb.dev/indexer"),
        receiver_registry_type_hash=os.getenv("RECEIVER_REGISTRY_TYPE_HASH", ""),
        api_key=fourdsky_api_key,
        fourdskyendpoint=fourdsky_endpoint,
        max_receivers=int(os.getenv("MAX_RECEIVERS", "10")),
        simulate_if_unavailable=_env_bool("SIMULATE_IF_UNAVAILABLE", True),
    )
    db_path = os.getenv("DATABASE_PATH", "mlat_data.db")
    return config, db_path


class ProductionMLATSystem:
    """
    Production-ready MLAT system with all features integrated.
    """
    
    def __init__(self, config: NetworkConfig, db_path: str = "mlat_data.db"):
        self.config = config
        
        # Initialize components
        self.network_client = CKBNeuronNetworkClient(config)
        self.correlator = SignalCorrelator(
            time_window=0.005,  # 5ms
            min_receivers=4
        )
        self.solver = RobustMLATSolver(min_receivers=4)
        self.database = MLATDatabase(db_path)
        
        # State tracking
        self.receiver_positions: Dict[str, ReceiverPosition] = {}
        self.is_running = False
        
        # Statistics
        self.stats = {
            'start_time': time.time(),
            'total_signals': 0,
            'total_positions': 0,
            'successful_solves': 0,
            'failed_solves': 0,
            'last_position_time': 0
        }
        
    async def initialize(self):
        """Initialize the system"""
        logger.info("=" * 70)
        logger.info("🚀 PRODUCTION MLAT SYSTEM INITIALIZING")
        logger.info("=" * 70)
        
        # Connect to database
        self.database.connect()
        logger.info("✅ Database connected")
        
        # Initialize network
        await self.network_client.initialize()
        logger.info("✅ Network initialized")
        
        # Cache receiver positions
        self._cache_receiver_positions()
        logger.info(f"✅ Cached {len(self.receiver_positions)} receiver positions")
        
        logger.info("=" * 70)
        logger.info("✅ SYSTEM READY")
        logger.info("=" * 70)
    
    def _cache_receiver_positions(self):
        """Cache receiver positions for MLAT"""
        for receiver_id, info in self.network_client.active_receivers.items():
            self.receiver_positions[receiver_id] = ReceiverPosition(
                latitude=info.latitude,
                longitude=info.longitude,
                altitude=info.altitude,
                receiver_id=receiver_id
            )
    
    async def start(self):
        """Start the MLAT system"""
        self.is_running = True
        
        logger.info("📡 Starting data stream processing...")
        
        # Start network data streaming
        await self.network_client.start_streaming(self._handle_incoming_signal)
        
        # Start processing loops
        processing_task = asyncio.create_task(self._processing_loop())
        stats_task = asyncio.create_task(self._statistics_loop())
        
        logger.info("✅ System running")
        
        # Wait for tasks
        await asyncio.gather(processing_task, stats_task)
    
    async def _handle_incoming_signal(
        self,
        receiver_id: str,
        timestamp: float,
        message: str
    ):
        """Handle each incoming Mode-S signal"""
        self.stats['total_signals'] += 1
        
        # Create signal object
        signal = RawSignal(
            receiver_id=receiver_id,
            timestamp=timestamp,
            message=message,
            signal_strength=0.0
        )
        
        # Add to correlator
        self.correlator.add_signal(signal)
    
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
        # Convert to observations
        observations = []
        
        for signal in group.signals:
            recv_pos = self.receiver_positions.get(signal.receiver_id)
            if not recv_pos:
                continue
            
            obs = SignalObservation(
                receiver_id=signal.receiver_id,
                timestamp=signal.timestamp,
                signal_data=signal.message,
                receiver_position=recv_pos
            )
            observations.append(obs)
        
        if len(observations) < 4:
            return
        
        # Solve position
        self.stats['total_positions'] += 1
        position = self.solver.solve_position(observations)
        
        if position:
            self.stats['successful_solves'] += 1
            self.stats['last_position_time'] = time.time()
            
            # Store in database
            await self._store_position(group.message, position)
            
            # Log success
            logger.info(
                f"✈️  Aircraft {group.message[:8]}: "
                f"{position.latitude:.4f}°, {position.longitude:.4f}°, "
                f"{position.altitude:.0f}m "
                f"(±{position.uncertainty:.0f}m, {position.num_receivers} rcv)"
            )
        else:
            self.stats['failed_solves'] += 1
    
    async def _store_position(self, message: str, position):
        """Store position in database"""
        # Extract aircraft ID from message
        aircraft_id = message[2:8] if len(message) >= 8 else message
        
        try:
            self.database.store_position(
                aircraft_id=aircraft_id,
                timestamp=position.timestamp,
                latitude=position.latitude,
                longitude=position.longitude,
                altitude=position.altitude,
                uncertainty=position.uncertainty,
                num_receivers=position.num_receivers,
                receiver_ids=position.receiver_ids,
                residual=position.residual
            )
        except Exception as e:
            logger.error(f"Failed to store position: {e}")
    
    async def _statistics_loop(self):
        """Periodic statistics reporting and storage"""
        logger.info("📊 Statistics loop started")
        
        while self.is_running:
            await asyncio.sleep(60)  # Every minute
            
            # Calculate statistics
            runtime = time.time() - self.stats['start_time']
            active_aircraft = self.database.get_active_aircraft(seconds=300)
            
            # Get recent positions for uncertainty calculation
            recent_positions = self.database.get_recent_positions(seconds=300)
            avg_uncertainty = (
                sum(p.uncertainty for p in recent_positions) / len(recent_positions)
                if recent_positions else 0
            )
            
            # Store statistics
            self.database.store_statistics(
                total_signals=self.stats['total_signals'],
                total_positions=self.stats['total_positions'],
                active_aircraft=len(active_aircraft),
                active_receivers=len(self.receiver_positions),
                avg_uncertainty=avg_uncertainty
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
    config, db_path = load_runtime_settings()
    
    # Create system
    system = ProductionMLATSystem(config, db_path=db_path)
    
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


if __name__ == "__main__":
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MLAT AIRCRAFT LOCALIZATION SYSTEM - PRODUCTION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")
    
    asyncio.run(main())
