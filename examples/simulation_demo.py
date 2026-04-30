"""
Complete MLAT Simulation Demo

This demonstrates the full system working with simulated aircraft:
- Multiple aircraft flying realistic paths
- Receivers detecting signals
- Signal correlation
- MLAT position calculation
- Real-time output

Run this to see the system in action!
"""

import asyncio
import random
import math
import time
from typing import List, Dict
from datetime import datetime

from mlat.enhanced_solver import EnhancedMLATSolver, ReceiverPosition, SignalObservation, AircraftPosition
from correlation.correlator import SignalCorrelator, RawSignal


class SimulatedAircraft:
    """Simulates a single aircraft flying"""
    
    def __init__(self, aircraft_id: str, lat: float, lon: float, alt: float):
        self.aircraft_id = aircraft_id
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.heading = random.uniform(0, 360)
        self.speed = random.uniform(400, 600)  # km/h
        self.icao = f"AC{random.randint(1000, 9999):04X}"
        
    def update_position(self, dt: float):
        """Update aircraft position based on time step dt (seconds)"""
        # Convert speed to m/s
        speed_ms = self.speed * 1000 / 3600
        
        # Calculate distance traveled
        distance = speed_ms * dt
        
        # Convert to degrees (rough approximation)
        dlat = (distance * math.cos(math.radians(self.heading))) / 111000
        dlon = (distance * math.sin(math.radians(self.heading))) / (111000 * math.cos(math.radians(self.lat)))
        
        self.lat += dlat
        self.lon += dlon
        
        # Random heading changes
        if random.random() < 0.05:
            self.heading += random.uniform(-15, 15)
            self.heading = self.heading % 360
        
        # Random altitude changes
        if random.random() < 0.1:
            self.alt += random.uniform(-200, 200)
            self.alt = max(3000, min(12000, self.alt))
    
    def to_ecef(self) -> tuple:
        """Convert current position to ECEF"""
        lat_rad = math.radians(self.lat)
        lon_rad = math.radians(self.lon)
        
        a = 6378137.0
        e2 = 0.00669437999014
        
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
        
        x = (N + self.alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + self.alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e2) + self.alt) * math.sin(lat_rad)
        
        return (x, y, z)


class MLATSimulation:
    """Complete MLAT system simulation"""
    
    def __init__(self):
        # Setup receivers
        self.receivers = [
            ReceiverPosition(40.7128, -74.0060, 10, "RECV_NYC"),
            ReceiverPosition(42.3601, -71.0589, 20, "RECV_BOS"),
            ReceiverPosition(39.9526, -75.1652, 15, "RECV_PHL"),
            ReceiverPosition(38.9072, -77.0369, 25, "RECV_DC"),
            ReceiverPosition(42.8864, -78.8784, 18, "RECV_BUF"),
            ReceiverPosition(41.4993, -81.6944, 22, "RECV_CLE"),
        ]
        
        # Setup components
        self.correlator = SignalCorrelator(
            time_window=0.005,  # 5ms correlation window
            min_receivers=4
        )
        self.solver = EnhancedMLATSolver(min_receivers=4)
        
        # Aircraft being simulated
        self.aircraft: Dict[str, SimulatedAircraft] = {}
        
        # Statistics
        self.total_signals = 0
        self.total_positions = 0
        self.position_errors = []
        self.start_time = time.time()
        
    def add_aircraft(self, aircraft_id: str, lat: float, lon: float, alt: float):
        """Add an aircraft to the simulation"""
        self.aircraft[aircraft_id] = SimulatedAircraft(aircraft_id, lat, lon, alt)
        print(f"✈️  Added aircraft {aircraft_id} at {lat:.4f}°, {lon:.4f}°, {alt}m")
    
    def simulate_signal_reception(self, aircraft: SimulatedAircraft, current_time: float) -> List[RawSignal]:
        """Simulate receivers detecting an aircraft transmission"""
        SPEED_OF_LIGHT = 299792458.0
        
        # Aircraft position in ECEF
        aircraft_ecef = aircraft.to_ecef()
        
        signals = []
        message = f"8D{aircraft.icao}202CC371C32CE0576098"
        
        for receiver in self.receivers:
            # Calculate distance from aircraft to receiver
            receiver_ecef = receiver.to_ecef()
            distance = math.sqrt(
                sum((aircraft_ecef[i] - receiver_ecef[i])**2 for i in range(3))
            )
            
            # Calculate time for signal to travel
            travel_time = distance / SPEED_OF_LIGHT
            
            # Add small random error (simulates clock drift, noise)
            error = random.gauss(0, 10e-9)  # 10 nanosecond standard deviation
            
            # Reception time
            reception_time = current_time + travel_time + error
            
            # Not all receivers hear every signal (simulate coverage gaps)
            if random.random() > 0.9:  # 10% chance of missing signal
                continue
            
            signal = RawSignal(
                receiver_id=receiver.receiver_id,
                timestamp=reception_time,
                message=message,
                signal_strength=random.uniform(30, 50)
            )
            signals.append(signal)
            self.total_signals += 1
        
        return signals
    
    def calculate_position_error(
        self,
        true_aircraft: SimulatedAircraft,
        calculated: AircraftPosition
    ) -> float:
        """Calculate 3D error between true and calculated position"""
        lat_error = (calculated.latitude - true_aircraft.lat) * 111000
        lon_error = (calculated.longitude - true_aircraft.lon) * 111000 * math.cos(math.radians(true_aircraft.lat))
        alt_error = calculated.altitude - true_aircraft.alt
        
        error_3d = math.sqrt(lat_error**2 + lon_error**2 + alt_error**2)
        return error_3d
    
    async def run(self, duration: int = 60, update_interval: float = 1.0):
        """
        Run the simulation
        
        Args:
            duration: How long to run (seconds)
            update_interval: How often to update aircraft positions (seconds)
        """
        print("=" * 80)
        print("🚀 MLAT SIMULATION STARTING")
        print("=" * 80)
        print(f"\nConfiguration:")
        print(f"  Receivers: {len(self.receivers)}")
        print(f"  Duration: {duration} seconds")
        print(f"  Update interval: {update_interval}s")
        print()
        
        # Add some aircraft
        self.add_aircraft("FLT001", 40.5, -74.5, 8000)
        self.add_aircraft("FLT002", 41.0, -73.0, 9500)
        self.add_aircraft("FLT003", 39.5, -76.0, 7500)
        
        print(f"\n{'='*80}")
        print("📡 SIMULATION RUNNING - REAL-TIME OUTPUT")
        print(f"{'='*80}\n")
        
        elapsed = 0
        iteration = 0
        
        while elapsed < duration:
            iteration += 1
            current_time = self.start_time + elapsed
            
            # Update aircraft positions
            for aircraft in self.aircraft.values():
                aircraft.update_position(update_interval)
            
            # Simulate signal transmissions
            for aircraft_id, aircraft in self.aircraft.items():
                # Aircraft transmit every ~1 second
                if random.random() < 0.8:
                    signals = self.simulate_signal_reception(aircraft, current_time)
                    
                    if signals:
                        # Add signals to correlator
                        self.correlator.add_signals(signals)
            
            # Process correlations and calculate positions
            correlated_groups = self.correlator.correlate()
            
            for group in correlated_groups:
                # Convert to observations
                observations = []
                for signal in group.signals:
                    recv = next((r for r in self.receivers if r.receiver_id == signal.receiver_id), None)
                    if recv:
                        obs = SignalObservation(
                            receiver_id=signal.receiver_id,
                            timestamp=signal.timestamp,
                            signal_data=signal.message,
                            receiver_position=recv
                        )
                        observations.append(obs)
                
                # Solve position
                if len(observations) >= 4:
                    position = self.solver.solve_position(observations)
                    
                    if position:
                        self.total_positions += 1
                        
                        # Find which aircraft this is (by ICAO in message)
                        icao = group.message[2:8]
                        true_aircraft = next(
                            (ac for ac in self.aircraft.values() if ac.icao == icao),
                            None
                        )
                        
                        if true_aircraft:
                            error = self.calculate_position_error(true_aircraft, position)
                            self.position_errors.append(error)
                            
                            # Print result
                            self._print_position_result(
                                iteration,
                                true_aircraft,
                                position,
                                error
                            )
            
            await asyncio.sleep(update_interval)
            elapsed += update_interval
        
        # Print final statistics
        self._print_statistics()
    
    def _print_position_result(
        self,
        iteration: int,
        true_aircraft: SimulatedAircraft,
        calculated: AircraftPosition,
        error: float
    ):
        """Print a single position result"""
        timestamp_str = datetime.now().strftime('%H:%M:%S')
        
        # Color code based on error
        if error < 100:
            error_color = "🟢"
        elif error < 300:
            error_color = "🟡"
        else:
            error_color = "🔴"
        
        print(f"[{timestamp_str}] #{iteration:03d} {error_color} Aircraft {true_aircraft.aircraft_id}")
        print(f"  TRUE:  {true_aircraft.lat:8.4f}°, {true_aircraft.lon:8.4f}°, {true_aircraft.alt:6.0f}m")
        print(f"  MLAT:  {calculated.latitude:8.4f}°, {calculated.longitude:8.4f}°, {calculated.altitude:6.0f}m")
        print(f"  ERROR: {error:6.1f}m (±{calculated.uncertainty:.0f}m uncertainty) | {calculated.num_receivers} receivers | {calculated.iterations} iterations")
        print(f"  {'-'*76}")
    
    def _print_statistics(self):
        """Print final simulation statistics"""
        runtime = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 SIMULATION STATISTICS")
        print("=" * 80)
        print(f"\nRuntime: {runtime:.1f} seconds")
        print(f"Aircraft simulated: {len(self.aircraft)}")
        print(f"Total signals generated: {self.total_signals}")
        print(f"Total positions calculated: {self.total_positions}")
        print(f"Signals per second: {self.total_signals/runtime:.1f}")
        print(f"Positions per second: {self.total_positions/runtime:.1f}")
        
        if self.position_errors:
            print(f"\nPosition Accuracy:")
            print(f"  Mean error: {sum(self.position_errors)/len(self.position_errors):.1f}m")
            print(f"  Min error: {min(self.position_errors):.1f}m")
            print(f"  Max error: {max(self.position_errors):.1f}m")
            
            # Error distribution
            under_100 = sum(1 for e in self.position_errors if e < 100)
            under_300 = sum(1 for e in self.position_errors if e < 300)
            under_500 = sum(1 for e in self.position_errors if e < 500)
            
            print(f"\nError Distribution:")
            print(f"  < 100m:  {under_100:3d} ({100*under_100/len(self.position_errors):.1f}%)")
            print(f"  < 300m:  {under_300:3d} ({100*under_300/len(self.position_errors):.1f}%)")
            print(f"  < 500m:  {under_500:3d} ({100*under_500/len(self.position_errors):.1f}%)")
        
        print("\n" + "=" * 80)
        print("✅ SIMULATION COMPLETE")
        print("=" * 80)


async def main():
    """Main entry point"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║                    MLAT AIRCRAFT LOCALIZATION SYSTEM                       ║")
    print("║                         Simulation Demonstration                           ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    sim = MLATSimulation()
    
    try:
        # Run for 30 seconds with 1 second updates
        await sim.run(duration=30, update_interval=1.0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
        sim._print_statistics()


if __name__ == "__main__":
    asyncio.run(main())
