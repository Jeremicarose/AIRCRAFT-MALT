"""
MLAT (Multilateration) Position Solver

This module implements the Time Difference of Arrival (TDOA) method
to calculate aircraft position from multiple receiver timestamps.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


# Speed of light in meters per second
SPEED_OF_LIGHT = 299792458.0  # m/s


@dataclass
class ReceiverPosition:
    """Geographic position of a receiver station"""
    latitude: float   # degrees
    longitude: float  # degrees
    altitude: float   # meters above sea level
    receiver_id: str
    
    def to_ecef(self) -> np.ndarray:
        """Convert lat/lon/alt to ECEF (Earth-Centered Earth-Fixed) coordinates"""
        lat_rad = np.radians(self.latitude)
        lon_rad = np.radians(self.longitude)
        
        # WGS84 parameters
        a = 6378137.0  # Semi-major axis
        e2 = 0.00669437999014  # First eccentricity squared
        
        N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
        
        x = (N + self.altitude) * np.cos(lat_rad) * np.cos(lon_rad)
        y = (N + self.altitude) * np.cos(lat_rad) * np.sin(lon_rad)
        z = (N * (1 - e2) + self.altitude) * np.sin(lat_rad)
        
        return np.array([x, y, z])


@dataclass
class SignalObservation:
    """A Mode-S signal observation from one receiver"""
    receiver_id: str
    timestamp: float  # GPS time in seconds (high precision)
    signal_data: str  # The Mode-S message content
    receiver_position: ReceiverPosition


@dataclass
class AircraftPosition:
    """Calculated aircraft position"""
    latitude: float
    longitude: float
    altitude: float
    timestamp: float
    uncertainty: float  # meters (geometric dilution of precision)
    num_receivers: int
    receiver_ids: List[str]


class MLATSolver:
    """
    Solves aircraft position using multilateration from TDOA measurements.
    
    The algorithm:
    1. Convert receiver positions to ECEF coordinates
    2. Calculate time differences relative to a reference receiver
    3. Set up and solve the least-squares problem
    4. Convert solution back to lat/lon/alt
    """
    
    def __init__(self, min_receivers: int = 4):
        """
        Initialize MLAT solver.
        
        Args:
            min_receivers: Minimum number of receivers needed (4 for 3D position)
        """
        self.min_receivers = min_receivers
    
    def solve_position(self, observations: List[SignalObservation]) -> Optional[AircraftPosition]:
        """
        Calculate aircraft position from multiple receiver observations.
        
        Args:
            observations: List of signal observations from different receivers
                         All observations should be from the SAME aircraft transmission
        
        Returns:
            AircraftPosition if successful, None if insufficient data
        """
        if len(observations) < self.min_receivers:
            print(f"Not enough receivers: {len(observations)} < {self.min_receivers}")
            return None
        
        # Sort by timestamp to use earliest as reference
        observations = sorted(observations, key=lambda x: x.timestamp)
        
        # Reference receiver (first to receive signal)
        ref_obs = observations[0]
        ref_pos = ref_obs.receiver_position.to_ecef()
        
        # Build system of equations
        positions = []
        time_diffs = []
        
        for obs in observations[1:]:
            pos = obs.receiver_position.to_ecef()
            positions.append(pos)
            
            # Time difference in seconds
            tdoa = obs.timestamp - ref_obs.timestamp
            time_diffs.append(tdoa)
        
        positions = np.array(positions)
        time_diffs = np.array(time_diffs)
        
        # Solve using iterative least squares (Gauss-Newton method)
        aircraft_ecef = self._gauss_newton_solver(
            ref_pos, positions, time_diffs
        )
        
        if aircraft_ecef is None:
            return None
        
        # Convert back to lat/lon/alt
        lat, lon, alt = self._ecef_to_lla(aircraft_ecef)
        
        # Calculate uncertainty (simplified GDOP estimation)
        uncertainty = self._estimate_uncertainty(ref_pos, positions, aircraft_ecef)
        
        return AircraftPosition(
            latitude=lat,
            longitude=lon,
            altitude=alt,
            timestamp=ref_obs.timestamp,
            uncertainty=uncertainty,
            num_receivers=len(observations),
            receiver_ids=[obs.receiver_id for obs in observations]
        )
    
    def _gauss_newton_solver(
        self, 
        ref_pos: np.ndarray,
        receiver_positions: np.ndarray,
        time_diffs: np.ndarray,
        max_iterations: int = 20,
        tolerance: float = 1.0  # meters
    ) -> Optional[np.ndarray]:
        """
        Iterative solver for MLAT using Gauss-Newton method.
        
        We're solving: ||aircraft - receiver_i|| - ||aircraft - ref|| = c * tdoa_i
        where c is speed of light
        """
        # Initial guess: average of all receiver positions
        all_positions = np.vstack([ref_pos.reshape(1, 3), receiver_positions])
        x = np.mean(all_positions, axis=0)
        
        # Convert time differences to range differences
        range_diffs = time_diffs * SPEED_OF_LIGHT
        
        for iteration in range(max_iterations):
            # Calculate residuals and Jacobian
            residuals = []
            jacobian_rows = []
            
            for i, (pos, r_diff) in enumerate(zip(receiver_positions, range_diffs)):
                # Distance from aircraft to receiver i
                r_i = np.linalg.norm(x - pos)
                # Distance from aircraft to reference
                r_ref = np.linalg.norm(x - ref_pos)
                
                # Residual: measured - predicted
                residual = r_diff - (r_i - r_ref)
                residuals.append(residual)
                
                # Jacobian row: partial derivatives
                if r_i > 0 and r_ref > 0:
                    dr_i = -(x - pos) / r_i
                    dr_ref = -(x - ref_pos) / r_ref
                    jacobian_row = dr_i - dr_ref
                else:
                    jacobian_row = np.zeros(3)
                
                jacobian_rows.append(jacobian_row)
            
            residuals = np.array(residuals)
            J = np.array(jacobian_rows)
            
            # Solve: J^T * J * delta = J^T * residuals
            try:
                delta = np.linalg.lstsq(J, residuals, rcond=None)[0]
            except np.linalg.LinAlgError:
                return None
            
            # Update position
            x = x + delta
            
            # Check convergence
            if np.linalg.norm(delta) < tolerance:
                return x
        
        # Return even if didn't fully converge
        return x
    
    def _ecef_to_lla(self, ecef: np.ndarray) -> Tuple[float, float, float]:
        """Convert ECEF coordinates to latitude, longitude, altitude"""
        x, y, z = ecef
        
        # WGS84 parameters
        a = 6378137.0
        e2 = 0.00669437999014
        
        # Longitude is straightforward
        lon = np.arctan2(y, x)
        
        # Iterative solution for latitude
        p = np.sqrt(x**2 + y**2)
        lat = np.arctan2(z, p * (1 - e2))
        
        for _ in range(5):  # Usually converges in 2-3 iterations
            N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
            lat = np.arctan2(z + e2 * N * np.sin(lat), p)
        
        # Altitude
        N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
        alt = p / np.cos(lat) - N
        
        return np.degrees(lat), np.degrees(lon), alt
    
    def _estimate_uncertainty(
        self,
        ref_pos: np.ndarray,
        receiver_positions: np.ndarray,
        aircraft_pos: np.ndarray
    ) -> float:
        """
        Estimate position uncertainty using simplified GDOP calculation.
        
        Lower GDOP = better geometry = more accurate position
        """
        # Build geometry matrix
        vectors = []
        
        # Vector from aircraft to reference
        r_ref = np.linalg.norm(aircraft_pos - ref_pos)
        if r_ref > 0:
            unit_ref = (aircraft_pos - ref_pos) / r_ref
        else:
            return float('inf')
        
        for pos in receiver_positions:
            r = np.linalg.norm(aircraft_pos - pos)
            if r > 0:
                unit_vector = (aircraft_pos - pos) / r
                vectors.append(unit_vector - unit_ref)
        
        if len(vectors) < 3:
            return float('inf')
        
        # GDOP is related to condition number of geometry matrix
        G = np.array(vectors)
        try:
            # Simplified: use smallest singular value as proxy
            _, s, _ = np.linalg.svd(G)
            gdop = 1.0 / s[-1] if s[-1] > 0 else float('inf')
            
            # Convert to approximate position error in meters
            # Assuming ~10ns timing accuracy -> ~3m ranging error
            base_error = 3.0  # meters
            uncertainty = gdop * base_error
            
            return uncertainty
        except:
            return float('inf')


# Example usage
if __name__ == "__main__":
    # Simulate 4 receivers around an aircraft
    receivers = [
        ReceiverPosition(40.7128, -74.0060, 10, "NYC"),      # New York
        ReceiverPosition(42.3601, -71.0589, 20, "BOS"),      # Boston
        ReceiverPosition(39.9526, -75.1652, 15, "PHL"),      # Philadelphia
        ReceiverPosition(38.9072, -77.0369, 25, "DC"),       # Washington DC
    ]
    
    # Simulate an aircraft at 41.0° N, 74.0° W, 10000m altitude
    # The aircraft transmits a signal at exactly t=0
    
    # Each receiver hears it at different times based on distance
    observations = []
    for i, recv in enumerate(receivers):
        # In reality, these timestamps come from actual signal reception
        # Here we simulate with small random delays
        timestamp = i * 0.000001  # Microsecond differences
        
        obs = SignalObservation(
            receiver_id=recv.receiver_id,
            timestamp=timestamp,
            signal_data="8D4840D6202CC371C32CE0576098",  # Example Mode-S
            receiver_position=recv
        )
        observations.append(obs)
    
    # Solve position
    solver = MLATSolver()
    position = solver.solve_position(observations)
    
    if position:
        print("Aircraft Position Found!")
        print(f"  Latitude:  {position.latitude:.6f}°")
        print(f"  Longitude: {position.longitude:.6f}°")
        print(f"  Altitude:  {position.altitude:.1f} m")
        print(f"  Uncertainty: {position.uncertainty:.1f} m")
        print(f"  Using {position.num_receivers} receivers")
    else:
        print("Could not solve position")
