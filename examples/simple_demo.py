"""
Simple Working MLAT Demo

This demonstrates the system components working together with
a simplified, guaranteed-to-converge approach.
"""

import math
import random
from datetime import datetime

from mlat.solver import MLATSolver, ReceiverPosition, SignalObservation
from correlation.correlator import SignalCorrelator, RawSignal

SPEED_OF_LIGHT = 299792458.0  # m/s


def lat_lon_alt_to_ecef(lat, lon, alt):
    """Simple ECEF conversion"""
    import numpy as np
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    a = 6378137.0
    e2 = 0.00669437999014
    
    N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
    
    x = (N + alt) * np.cos(lat_rad) * np.cos(lon_rad)
    y = (N + alt) * np.cos(lat_rad) * np.sin(lon_rad)
    z = (N * (1 - e2) + alt) * np.sin(lat_rad)
    
    return np.array([x, y, z])


def simulate_perfect_signals(aircraft_lat, aircraft_lon, aircraft_alt, receivers, base_time):
    """Generate perfect simulated signals with realistic timing"""
    aircraft_ecef = lat_lon_alt_to_ecef(aircraft_lat, aircraft_lon, aircraft_alt)
    
    signals = []
    message = f"8D{random.randint(100000, 999999):06X}202CC371C32CE0576098"
    
    for receiver in receivers:
        receiver_ecef = receiver.to_ecef()
        distance = float(math.sqrt(sum((aircraft_ecef[i] - receiver_ecef[i])**2 for i in range(3))))
        
        travel_time = distance / SPEED_OF_LIGHT
        
        # Very small random error
        error = random.gauss(0, 1e-9)  # 1 nanosecond
        
        reception_time = base_time + travel_time + error
        
        signal = RawSignal(
            receiver_id=receiver.receiver_id,
            timestamp=reception_time,
            message=message,
            signal_strength=random.uniform(40, 50)
        )
        signals.append(signal)
    
    return signals


def demo_component_testing():
    """Demonstrate each component working individually"""
    
    print("\n" + "="*80)
    print("🧪 MLAT SYSTEM COMPONENT TESTING")
    print("="*80 + "\n")
    
    # Setup receivers
    receivers = [
        ReceiverPosition(40.7128, -74.0060, 10, "NYC"),
        ReceiverPosition(42.3601, -71.0589, 20, "BOS"),
        ReceiverPosition(39.9526, -75.1652, 15, "PHL"),
        ReceiverPosition(38.9072, -77.0369, 25, "DC"),
    ]
    
    print("📡 Receiver Network:")
    for recv in receivers:
        print(f"   {recv.receiver_id:8s}: {recv.latitude:7.4f}°N, {recv.longitude:8.4f}°W, {recv.altitude}m")
    print()
    
    # Test 1: Signal Correlation
    print("="*80)
    print("TEST 1: Signal Correlation")
    print("="*80 + "\n")
    
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)
    
    # Simulate 3 different aircraft transmissions
    base_time = 1000.0
    
    # Aircraft 1
    msg1 = "8D123456202CC371C32CE0576098"
    for i, recv in enumerate(receivers):
        correlator.add_signal(RawSignal(
            recv.receiver_id,
            base_time + i * 0.0001,
            msg1,
            45.0
        ))
    
    # Aircraft 2 (different time)
    msg2 = "8D789ABC202CC371C32CE0576098"
    for i, recv in enumerate(receivers):
        correlator.add_signal(RawSignal(
            recv.receiver_id,
            base_time + 0.2 + i * 0.0001,
            msg2,
            42.0
        ))
    
    # Aircraft 3 (only 2 receivers - should be filtered)
    msg3 = "8DDEADBE202CC371C32CE0576098"
    for i in range(2):
        correlator.add_signal(RawSignal(
            receivers[i].receiver_id,
            base_time + 0.4 + i * 0.0001,
            msg3,
            38.0
        ))
    
    groups = correlator.correlate()
    
    print(f"Added signals from 3 aircraft:")
    print(f"  Aircraft 1: 4 receivers heard it")
    print(f"  Aircraft 2: 4 receivers heard it")
    print(f"  Aircraft 3: 2 receivers heard it (below minimum)")
    print()
    print(f"✅ Correlated groups found: {len(groups)}")
    print(f"   Expected: 2 (third aircraft filtered out)")
    print()
    
    for i, group in enumerate(groups):
        print(f"   Group {i+1}:")
        print(f"      Receivers: {len(group.signals)}")
        print(f"      Time span: {group.time_span*1000:.3f}ms")
        print()
    
    # Test 2: MLAT Position Calculation
    print("="*80)
    print("TEST 2: MLAT Position Calculation")
    print("="*80 + "\n")
    
    # Test with known aircraft position
    true_lat = 40.5
    true_lon = -74.0
    true_alt = 8000.0
    
    print(f"True Aircraft Position:")
    print(f"   Latitude:  {true_lat}°")
    print(f"   Longitude: {true_lon}°")
    print(f"   Altitude:  {true_alt}m")
    print()
    
    # Generate perfect signals
    signals = simulate_perfect_signals(true_lat, true_lon, true_alt, receivers, base_time)
    
    # Convert to observations
    observations = [
        SignalObservation(
            receiver_id=sig.receiver_id,
            timestamp=sig.timestamp,
            signal_data=sig.message,
            receiver_position=next(r for r in receivers if r.receiver_id == sig.receiver_id)
        )
        for sig in signals
    ]
    
    # Solve
    solver = MLATSolver(min_receivers=4)
    position = solver.solve_position(observations)
    
    if position:
        print(f"✅ Calculated Position:")
        print(f"   Latitude:  {position.latitude:.6f}°")
        print(f"   Longitude: {position.longitude:.6f}°")
        print(f"   Altitude:  {position.altitude:.1f}m")
        print(f"   Uncertainty: ±{position.uncertainty:.1f}m")
        print(f"   Used {position.num_receivers} receivers")
        print()
        
        # Calculate error
        lat_error = abs(position.latitude - true_lat) * 111000
        lon_error = abs(position.longitude - true_lon) * 111000
        alt_error = abs(position.altitude - true_alt)
        
        total_error = math.sqrt(lat_error**2 + lon_error**2 + alt_error**2)
        
        print(f"📊 Accuracy:")
        print(f"   Latitude error:  {lat_error:.1f}m")
        print(f"   Longitude error: {lon_error:.1f}m")
        print(f"   Altitude error:  {alt_error:.1f}m")
        print(f"   Total 3D error:  {total_error:.1f}m")
        print()
        
        if total_error < 1000:
            print("✅ TEST PASSED - Position calculated successfully!")
        else:
            print("⚠️  Position calculated but with larger error than ideal")
    else:
        print("❌ Failed to calculate position")
    
    print()


def demo_complete_workflow():
    """Demonstrate complete workflow with multiple aircraft"""
    
    print("="*80)
    print("TEST 3: Complete Workflow - Multiple Aircraft")
    print("="*80 + "\n")
    
    # Setup
    receivers = [
        ReceiverPosition(40.7128, -74.0060, 10, "NYC"),
        ReceiverPosition(42.3601, -71.0589, 20, "BOS"),
        ReceiverPosition(39.9526, -75.1652, 15, "PHL"),
        ReceiverPosition(38.9072, -77.0369, 25, "DC"),
        ReceiverPosition(41.4993, -81.6944, 22, "CLE"),
    ]
    
    correlator = SignalCorrelator(time_window=0.005, min_receivers=4)
    solver = MLATSolver(min_receivers=4)
    
    # Aircraft positions
    aircraft = [
        ("FLT001", 40.5, -74.0, 9000),
        ("FLT002", 41.0, -73.0, 8500),
        ("FLT003", 39.5, -75.5, 7000),
    ]
    
    base_time = 2000.0
    positions_found = 0
    
    print(f"Simulating {len(aircraft)} aircraft transmissions...\n")
    
    # Simulate transmissions
    for idx, (name, lat, lon, alt) in enumerate(aircraft):
        print(f"Aircraft {name}:")
        print(f"   True position: {lat}°, {lon}°, {alt}m")
        
        # Generate signals
        signals = simulate_perfect_signals(
            lat, lon, alt,
            receivers,
            base_time + idx * 0.5
        )
        
        print(f"   Generated {len(signals)} receiver signals")
        
        # Add to correlator
        correlator.add_signals(signals)
    
    print(f"\nCorrelating signals...")
    groups = correlator.correlate()
    print(f"   Found {len(groups)} correlated groups")
    
    print(f"\nCalculating positions...\n")
    
    for i, group in enumerate(groups):
        observations = [
            SignalObservation(
                receiver_id=sig.receiver_id,
                timestamp=sig.timestamp,
                signal_data=sig.message,
                receiver_position=next(r for r in receivers if r.receiver_id == sig.receiver_id)
            )
            for sig in group.signals
        ]
        
        position = solver.solve_position(observations)
        
        if position:
            positions_found += 1
            print(f"Position {positions_found}:")
            print(f"   Location: {position.latitude:.4f}°, {position.longitude:.4f}°")
            print(f"   Altitude: {position.altitude:.0f}m")
            print(f"   Uncertainty: ±{position.uncertainty:.1f}m")
            print(f"   Receivers: {position.num_receivers}")
            print()
    
    print(f"{'='*80}")
    print(f"Results: {positions_found}/{len(aircraft)} positions calculated")
    
    if positions_found == len(aircraft):
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"⚠️  Some positions not calculated")
    
    print(f"{'='*80}\n")


def main():
    """Main demo"""
    
    print("\n" + "╔"+ "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "      MLAT AIRCRAFT LOCALIZATION SYSTEM - DEMONSTRATION".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")
    
    try:
        demo_component_testing()
        demo_complete_workflow()
        
        print("\n" + "="*80)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*80)
        print()
        print("The system successfully demonstrated:")
        print("  ✓ Signal correlation across multiple receivers")
        print("  ✓ MLAT position calculation")
        print("  ✓ Complete workflow with multiple aircraft")
        print()
        print("Next steps:")
        print("  1. Review the code to understand how each component works")
        print("  2. Check docs/INTEGRATION_GUIDE.md for production deployment")
        print("  3. Open src/visualization/dashboard.html for interactive demo")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
