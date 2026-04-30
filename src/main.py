"""
MLAT System Orchestrator

Main system that coordinates:
1. CKB-based peer discovery and data streaming
2. Signal correlation
3. Position calculation
4. Result output
"""

import asyncio
from typing import Dict, List
from datetime import datetime
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

from network.ckb_client import NetworkConfig
from correlation.correlator import RawSignal, CorrelatedSignalGroup
from mlat.solver import MLATSolver, ReceiverPosition, SignalObservation, AircraftPosition
from mlat_runtime import BaseMLATRuntime
from runtime_config import load_runtime_settings


class MLATSystem(BaseMLATRuntime[ReceiverPosition, SignalObservation]):
    """
    Complete MLAT system orchestrator.
    
    This is the main entry point that coordinates all subsystems.
    """
    
    def __init__(self, config: NetworkConfig):
        super().__init__(
            config,
            time_window=0.002,  # 2ms correlation window
            min_receivers=4,
        )
        self.mlat_solver = MLATSolver(min_receivers=4)

        # Tracking state
        self.tracked_aircraft: Dict[str, List[AircraftPosition]] = {}
        self.total_positions_calculated = 0
        self.total_signals_received = 0
    
    async def initialize(self) -> None:
        """Initialize the MLAT system"""
        print("=" * 60)
        print("🛩️  MLAT AIRCRAFT LOCALIZATION SYSTEM")
        print("=" * 60)
        print()
        
        await self.initialize_network()
        
        print()
        print("✅ System initialized successfully!")
        print()
    
    def build_receiver_position(self, receiver_id: str, info) -> ReceiverPosition:
        return ReceiverPosition(
            latitude=info.latitude,
            longitude=info.longitude,
            altitude=info.altitude,
            receiver_id=receiver_id,
        )

    def on_signal_received(self, signal: RawSignal):
        self.total_signals_received += 1

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
    
    async def start(self) -> None:
        """Start the MLAT system"""
        self.is_running = True
        
        print("🚀 Starting MLAT processing...")
        print(f"📡 Listening on {len(self.receiver_positions)} receivers")
        print()
        
        # Start receiving data
        await self.network_client.start_streaming(self.handle_incoming_signal)
        
        # Start correlation and solving loop
        asyncio.create_task(self._processing_loop())
        
        print("✅ System running - Press Ctrl+C to stop")
        print("-" * 60)
    
    async def _processing_loop(self) -> None:
        """
        Main processing loop.
        
        Periodically:
        1. Correlate signals to find groups
        2. Calculate positions using MLAT
        3. Output results
        """
        while self.is_running:
            # Run correlation
            correlated_groups = self.correlator.correlate()
            
            # Process each correlated group
            for group in correlated_groups:
                await self._process_signal_group(group)
            
            # Wait a bit before next cycle
            await asyncio.sleep(0.1)  # Process every 100ms
    
    async def _process_signal_group(self, group: CorrelatedSignalGroup) -> None:
        """
        Process a correlated signal group to calculate aircraft position.
        """
        observations = self.build_observations_from_group(group)
        
        # Solve position
        position = self.mlat_solver.solve_position(observations)
        
        if position:
            self.total_positions_calculated += 1
            await self._handle_position_result(group.message, position)
    
    async def _handle_position_result(
        self,
        aircraft_id: str,
        position: AircraftPosition
    ) -> None:
        """
        Handle a successfully calculated position.
        """
        # Store in tracking history
        if aircraft_id not in self.tracked_aircraft:
            self.tracked_aircraft[aircraft_id] = []
        
        self.tracked_aircraft[aircraft_id].append(position)
        
        # Keep only recent positions (last 100)
        if len(self.tracked_aircraft[aircraft_id]) > 100:
            self.tracked_aircraft[aircraft_id] = self.tracked_aircraft[aircraft_id][-100:]
        
        # Output result
        self._print_position(aircraft_id, position)
    
    def _print_position(self, aircraft_id: str, position: AircraftPosition) -> None:
        """Print position result in a nice format"""
        timestamp_str = datetime.fromtimestamp(position.timestamp).strftime('%H:%M:%S.%f')[:-3]
        
        print(f"✈️  Aircraft: {aircraft_id[:6]}...")
        print(f"   📍 Position: {position.latitude:.6f}°N, {position.longitude:.6f}°W")
        print(f"   ⬆️  Altitude: {position.altitude:.0f} m ({position.altitude*3.28084:.0f} ft)")
        print(f"   🎯 Uncertainty: ±{position.uncertainty:.1f} m")
        print(f"   📡 Receivers: {position.num_receivers} ({', '.join(position.receiver_ids)})")
        print(f"   ⏰ Time: {timestamp_str}")
        print("-" * 60)
    
    async def stop(self) -> None:
        """Stop the MLAT system"""
        print()
        print("🛑 Stopping MLAT system...")
        
        self.is_running = False
        await self.network_client.shutdown()
        
        # Print statistics
        self._print_statistics()
        
        print("✅ System stopped")
    
    def _print_statistics(self) -> None:
        """Print system statistics"""
        print()
        print("=" * 60)
        print("📊 SYSTEM STATISTICS")
        print("=" * 60)
        print(f"Total signals received: {self.total_signals_received}")
        print(f"Total positions calculated: {self.total_positions_calculated}")
        print(f"Unique aircraft tracked: {len(self.tracked_aircraft)}")
        print(f"Active receivers: {len(self.receiver_positions)}")
        
        # Correlator stats
        corr_stats = self.correlator.get_statistics()
        print(f"Signals in buffer: {corr_stats['buffer_size']}")
        print(f"Processed groups: {corr_stats['processed_groups']}")
        
        print("=" * 60)


async def main():
    """Main entry point"""
    settings = load_runtime_settings(max_receivers_default=5)
    
    # Create MLAT system
    system = MLATSystem(settings.network_config)
    
    try:
        # Initialize
        await system.initialize()
        
        # Start processing
        await system.start()
        
        # Run until interrupted
        # In a real system, this would run indefinitely
        # For demo, run for 30 seconds
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    finally:
        await system.stop()


def main_cli():
    """Console entry point for the demo system."""
    asyncio.run(main())


if __name__ == "__main__":
    main_cli()
