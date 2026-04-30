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
import os
from typing import Dict
import time

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

from network.ckb_client import CKBNeuronNetworkClient, NetworkConfig
from correlation.correlator import RawSignal
from mlat.robust_solver import RobustMLATSolver, ReceiverPosition, SignalObservation
from database.mlat_db import MLATDatabase
from mlat_runtime import BaseMLATRuntime
from runtime_config import load_runtime_settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMLATSystem(BaseMLATRuntime[ReceiverPosition, SignalObservation]):
    """
    Production-ready MLAT system with all features integrated.
    """
    
    def __init__(self, config: NetworkConfig, db_path: str = "mlat_data.db"):
        super().__init__(
            config,
            time_window=0.005,  # 5ms
            min_receivers=4,
        )
        self.solver = RobustMLATSolver(min_receivers=4)
        self.database = MLATDatabase(db_path)

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
    settings = load_runtime_settings(max_receivers_default=10)
    
    # Create system
    system = ProductionMLATSystem(settings.network_config, db_path=settings.db_path)
    
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
