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

from network.ckb_client import CKBNeuronNetworkClient, NetworkConfig
from correlation.correlator import SignalCorrelator, RawSignal, CorrelatedSignalGroup
from mlat.solver import MLATSolver, ReceiverPosition, SignalObservation, AircraftPosition


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_runtime_config() -> NetworkConfig:
    """Load CKB demo configuration from environment."""
    return NetworkConfig(
        ckb_network=os.getenv("CKB_NETWORK", "testnet"),
        ckb_rpc_url=os.getenv("CKB_RPC_URL", "https://testnet.ckb.dev/rpc"),
        ckb_indexer_url=os.getenv("CKB_INDEXER_URL", "https://testnet.ckb.dev/indexer"),
        receiver_registry_type_hash=os.getenv("RECEIVER_REGISTRY_TYPE_HASH", ""),
        api_key=os.getenv("FOURDSKYAPIKEY") or os.getenv("FOURDSKY_API_KEY"),
        fourdskyendpoint=os.getenv("FOURDSKYENDPOINT") or os.getenv(
            "FOURDSKY_ENDPOINT",
            "",
        ),
        fourdsky_transport=os.getenv("FOURDSKY_TRANSPORT", "auto"),
        fourdsky_auth_header=os.getenv("FOURDSKY_AUTH_HEADER", "X-API-Key"),
        fourdsky_auth_scheme=os.getenv("FOURDSKY_AUTH_SCHEME") or None,
        fourdsky_auth_token=os.getenv("FOURDSKY_AUTH_TOKEN") or None,
        fourdsky_subscribe_message=os.getenv("FOURDSKY_SUBSCRIBE_MESSAGE") or None,
        fourdsky_bridge_command=os.getenv("FOURDSKY_BRIDGE_COMMAND") or None,
        max_receivers=int(os.getenv("MAX_RECEIVERS", "5")),
        simulate_if_unavailable=_env_bool("SIMULATE_IF_UNAVAILABLE", True),
    )


class MLATSystem:
    """
    Complete MLAT system orchestrator.
    
    This is the main entry point that coordinates all subsystems.
    """
    
    def __init__(self, config: NetworkConfig):
        self.config = config
        
        # Initialize subsystems
        self.network_client = CKBNeuronNetworkClient(config)
        self.correlator = SignalCorrelator(
            time_window=0.002,  # 2ms correlation window
            min_receivers=4
        )
        self.mlat_solver = MLATSolver(min_receivers=4)
        
        # Tracking state
        self.tracked_aircraft: Dict[str, List[AircraftPosition]] = {}
        self.receiver_positions: Dict[str, ReceiverPosition] = {}
        self.total_positions_calculated = 0
        self.total_signals_received = 0
        
        # Running flag
        self.is_running = False
    
    async def initialize(self) -> None:
        """Initialize the MLAT system"""
        print("=" * 60)
        print("🛩️  MLAT AIRCRAFT LOCALIZATION SYSTEM")
        print("=" * 60)
        print()
        
        # Initialize network connection
        await self.network_client.initialize()
        
        # Store receiver positions for MLAT
        self._cache_receiver_positions()
        
        print()
        print("✅ System initialized successfully!")
        print()
    
    def _cache_receiver_positions(self) -> None:
        """Cache receiver positions for quick lookup during MLAT"""
        for receiver_id, info in self.network_client.active_receivers.items():
            self.receiver_positions[receiver_id] = ReceiverPosition(
                latitude=info.latitude,
                longitude=info.longitude,
                altitude=info.altitude,
                receiver_id=receiver_id
            )
    
    async def start(self) -> None:
        """Start the MLAT system"""
        self.is_running = True
        
        print("🚀 Starting MLAT processing...")
        print(f"📡 Listening on {len(self.receiver_positions)} receivers")
        print()
        
        # Start receiving data
        await self.network_client.start_streaming(self._handle_incoming_signal)
        
        # Start correlation and solving loop
        asyncio.create_task(self._processing_loop())
        
        print("✅ System running - Press Ctrl+C to stop")
        print("-" * 60)
    
    async def _handle_incoming_signal(
        self,
        receiver_id: str,
        timestamp: float,
        message: str
    ) -> None:
        """
        Handle each incoming Mode-S signal.
        
        This is called by the network client for every message received.
        """
        self.total_signals_received += 1
        
        # Create raw signal object
        signal = RawSignal(
            receiver_id=receiver_id,
            timestamp=timestamp,
            message=message,
            signal_strength=0.0
        )
        
        # Add to correlator
        self.correlator.add_signal(signal)
    
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
        # Convert to SignalObservations
        observations = []
        
        for signal in group.signals:
            # Get receiver position
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
    config = load_runtime_config()
    
    # Create MLAT system
    system = MLATSystem(config)
    
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
