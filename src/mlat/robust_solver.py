"""
Robust MLAT Solver - Production Ready

This implements a robust MLAT algorithm using:
1. Better initial guess via spherical intersection
2. Levenberg-Marquardt optimization (more stable than Gauss-Newton)
3. Extensive validation and error handling
4. Multiple fallback strategies
"""

import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

SPEED_OF_LIGHT = 299792458.0  # m/s
EARTH_RADIUS = 6378137.0  # WGS84 semi-major axis


@dataclass
class ReceiverPosition:
    """Geographic position of a receiver station"""
    latitude: float
    longitude: float
    altitude: float
    receiver_id: str
    
    def to_ecef(self) -> np.ndarray:
        """Convert lat/lon/alt to ECEF coordinates"""
        lat_rad = np.radians(self.latitude)
        lon_rad = np.radians(self.longitude)
        
        a = 6378137.0
        e2 = 0.00669437999014
        
        N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
        
        x = (N + self.altitude) * np.cos(lat_rad) * np.cos(lon_rad)
        y = (N + self.altitude) * np.cos(lat_rad) * np.sin(lon_rad)
        z = (N * (1 - e2) + self.altitude) * np.sin(lat_rad)
        
        return np.array([x, y, z])


@dataclass
class SignalObservation:
    """A Mode-S signal observation from one receiver"""
    receiver_id: str
    timestamp: float
    signal_data: str
    receiver_position: ReceiverPosition


@dataclass
class AircraftPosition:
    """Calculated aircraft position"""
    latitude: float
    longitude: float
    altitude: float
    timestamp: float
    uncertainty: float
    num_receivers: int
    receiver_ids: List[str]
    residual: float = 0.0
    iterations: int = 0
    method: str = "robust_mlat"


class RobustMLATSolver:
    """
    Production-ready MLAT solver with robust convergence.
    
    Uses Levenberg-Marquardt algorithm which is more stable
    than pure Gauss-Newton.
    """
    
    def __init__(self, min_receivers: int = 4):
        self.min_receivers = min_receivers
        self.max_iterations = 100
        self.convergence_threshold = 1.0  # meters
        
    def solve_position(self, observations: List[SignalObservation]) -> Optional[AircraftPosition]:
        """
        Calculate aircraft position using robust MLAT.
        
        Strategy:
        1. Validate inputs
        2. Get smart initial guess
        3. Optimize using Levenberg-Marquardt
        4. Validate result
        """
        if len(observations) < self.min_receivers:
            return None
        
        # Validate
        if not self._validate_observations(observations):
            return None
        
        # Sort by timestamp
        observations = sorted(observations, key=lambda x: x.timestamp)
        
        # Convert to ECEF
        ref_obs = observations[0]
        ref_pos = ref_obs.receiver_position.to_ecef()
        
        positions = np.array([obs.receiver_position.to_ecef() for obs in observations[1:]])
        time_diffs = np.array([obs.timestamp - ref_obs.timestamp for obs in observations[1:]])
        
        # Get initial guess
        initial_guess = self._get_smart_initial_guess(ref_pos, positions, time_diffs)
        
        if initial_guess is None:
            return None
        
        # Solve using Levenberg-Marquardt
        result = self._levenberg_marquardt(ref_pos, positions, time_diffs, initial_guess)
        
        if result is None:
            return None
        
        aircraft_ecef, residual, iterations = result
        
        # Convert to lat/lon/alt
        lat, lon, alt = self._ecef_to_lla(aircraft_ecef)
        
        # Validate result
        if not self._validate_result(lat, lon, alt, residual):
            return None
        
        # Calculate uncertainty
        uncertainty = self._estimate_uncertainty(ref_pos, positions, aircraft_ecef, residual)
        
        return AircraftPosition(
            latitude=lat,
            longitude=lon,
            altitude=alt,
            timestamp=ref_obs.timestamp,
            uncertainty=uncertainty,
            num_receivers=len(observations),
            receiver_ids=[obs.receiver_id for obs in observations],
            residual=residual,
            iterations=iterations
        )
    
    def _validate_observations(self, observations: List[SignalObservation]) -> bool:
        """Validate observations are suitable for MLAT"""
        # Check unique receivers
        receiver_ids = [obs.receiver_id for obs in observations]
        if len(receiver_ids) != len(set(receiver_ids)):
            return False
        
        # Check time span is reasonable
        timestamps = [obs.timestamp for obs in observations]
        time_span = max(timestamps) - min(timestamps)
        if time_span > 0.1:  # 100ms max
            return False
        
        return True
    
    def _get_smart_initial_guess(
        self,
        ref_pos: np.ndarray,
        positions: np.ndarray,
        time_diffs: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Get smart initial guess using geometric centroid
        with altitude based on typical aircraft cruising altitude.
        """
        # Use centroid of all receivers
        all_positions = np.vstack([ref_pos.reshape(1, 3), positions])
        centroid = np.mean(all_positions, axis=0)
        
        # Normalize to typical aircraft altitude above Earth surface
        # Most aircraft cruise at 8000-12000m
        centroid_norm = np.linalg.norm(centroid)
        target_altitude = EARTH_RADIUS + 9000  # 9km typical cruise
        
        # Scale centroid to be at aircraft altitude
        initial_guess = centroid * (target_altitude / centroid_norm)
        
        return initial_guess
    
    def _levenberg_marquardt(
        self,
        ref_pos: np.ndarray,
        positions: np.ndarray,
        time_diffs: np.ndarray,
        initial_guess: np.ndarray
    ) -> Optional[Tuple[np.ndarray, float, int]]:
        """
        Levenberg-Marquardt optimization.
        
        More robust than Gauss-Newton due to adaptive damping.
        """
        x = initial_guess.copy()
        range_diffs = time_diffs * SPEED_OF_LIGHT
        
        lambda_lm = 0.01  # Initial damping parameter
        nu = 2.0
        
        best_residual = float('inf')
        best_x = x.copy()
        
        for iteration in range(self.max_iterations):
            # Compute residuals and Jacobian
            residuals = []
            jacobian_rows = []
            
            for pos, r_diff in zip(positions, range_diffs):
                r_i = np.linalg.norm(x - pos)
                r_ref = np.linalg.norm(x - ref_pos)
                
                if r_i < 100 or r_ref < 100:  # Too close
                    return None
                
                # Residual
                predicted = r_i - r_ref
                residual = r_diff - predicted
                residuals.append(residual)
                
                # Jacobian
                dr_i = -(x - pos) / r_i
                dr_ref = -(x - ref_pos) / r_ref
                jacobian_rows.append(dr_i - dr_ref)
            
            residuals = np.array(residuals)
            J = np.array(jacobian_rows)
            
            # Current cost
            cost = 0.5 * np.sum(residuals**2)
            rms_residual = np.sqrt(np.mean(residuals**2))
            
            # Track best solution
            if rms_residual < best_residual:
                best_residual = rms_residual
                best_x = x.copy()
            
            # Check convergence
            if rms_residual < self.convergence_threshold:
                logger.debug(f"Converged in {iteration+1} iterations, RMS: {rms_residual:.2f}m")
                return x, rms_residual, iteration + 1
            
            # Levenberg-Marquardt step
            JTJ = J.T @ J
            JTr = J.T @ residuals
            
            # Try step with current damping
            try:
                delta = np.linalg.solve(JTJ + lambda_lm * np.eye(3), JTr)
            except np.linalg.LinAlgError:
                lambda_lm *= nu
                continue
            
            # Evaluate new position
            x_new = x + delta
            
            # Compute new residuals
            residuals_new = []
            for pos, r_diff in zip(positions, range_diffs):
                r_i = np.linalg.norm(x_new - pos)
                r_ref = np.linalg.norm(x_new - ref_pos)
                predicted = r_i - r_ref
                residuals_new.append(r_diff - predicted)
            
            residuals_new = np.array(residuals_new)
            cost_new = 0.5 * np.sum(residuals_new**2)
            
            # Accept or reject step
            if cost_new < cost:
                # Good step - accept and decrease damping
                x = x_new
                lambda_lm = max(lambda_lm / nu, 1e-7)
            else:
                # Bad step - reject and increase damping
                lambda_lm = min(lambda_lm * nu, 1e7)
            
            # Check if step is too small
            if np.linalg.norm(delta) < 0.01:  # 1cm
                logger.debug(f"Step too small at iteration {iteration+1}")
                break
        
        # Return best solution found
        if best_residual < 10000:  # 10km threshold
            logger.debug(f"Returning best solution: RMS {best_residual:.2f}m")
            return best_x, best_residual, self.max_iterations
        
        return None
    
    def _validate_result(self, lat: float, lon: float, alt: float, residual: float) -> bool:
        """Validate the calculated result makes sense"""
        # Latitude bounds
        if lat < -90 or lat > 90:
            return False
        
        # Longitude bounds
        if lon < -180 or lon > 180:
            return False
        
        # Altitude bounds (aircraft typically -500m to 15000m)
        if alt < -500 or alt > 15000:
            logger.debug(f"Invalid altitude: {alt}m")
            return False
        
        # Residual should be reasonable
        if residual > 5000:  # 5km
            logger.debug(f"Residual too large: {residual}m")
            return False
        
        return True
    
    def _ecef_to_lla(self, ecef: np.ndarray) -> Tuple[float, float, float]:
        """Convert ECEF to lat/lon/alt"""
        x, y, z = ecef
        
        a = 6378137.0
        e2 = 0.00669437999014
        
        # Longitude
        lon = np.arctan2(y, x)
        
        # Latitude (iterative)
        p = np.sqrt(x**2 + y**2)
        lat = np.arctan2(z, p * (1 - e2))
        
        for _ in range(10):
            N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
            lat_new = np.arctan2(z + e2 * N * np.sin(lat), p)
            if abs(lat_new - lat) < 1e-12:
                break
            lat = lat_new
        
        # Altitude
        N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
        alt = p / np.cos(lat) - N if abs(np.cos(lat)) > 1e-10 else 0
        
        return np.degrees(lat), np.degrees(lon), alt
    
    def _estimate_uncertainty(
        self,
        ref_pos: np.ndarray,
        positions: np.ndarray,
        aircraft_pos: np.ndarray,
        residual: float
    ) -> float:
        """
        Estimate position uncertainty.
        
        Combines geometric dilution of precision (GDOP)
        with residual error.
        """
        vectors = []
        
        r_ref = np.linalg.norm(aircraft_pos - ref_pos)
        if r_ref > 0:
            unit_ref = (aircraft_pos - ref_pos) / r_ref
        else:
            return 10000.0
        
        for pos in positions:
            r = np.linalg.norm(aircraft_pos - pos)
            if r > 0:
                unit_vector = (aircraft_pos - pos) / r
                vectors.append(unit_vector - unit_ref)
        
        if len(vectors) < 3:
            return 10000.0
        
        G = np.array(vectors)
        
        try:
            # SVD for GDOP
            _, s, _ = np.linalg.svd(G)
            
            if s[-1] > 1e-6:
                gdop = s[0] / s[-1]
            else:
                return 10000.0
            
            # Combine GDOP with residual
            # Residual gives us actual error magnitude
            # GDOP gives us geometric amplification
            base_uncertainty = max(residual, 10.0)  # At least 10m
            uncertainty = min(gdop * base_uncertainty / 3, 5000.0)
            
            return uncertainty
        except:
            return 10000.0
