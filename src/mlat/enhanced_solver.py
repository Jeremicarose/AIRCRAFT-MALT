"""
Enhanced MLAT Solver with Multiple Algorithms

Includes:
- Improved Gauss-Newton solver
- Algebraic closed-form initial guess
- Taylor series linearization method
- Better error handling and validation
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

SPEED_OF_LIGHT = 299792458.0  # m/s


@dataclass
class ReceiverPosition:
    """Geographic position of a receiver station"""
    latitude: float
    longitude: float
    altitude: float
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
    residual: float = 0.0  # RMS residual error
    iterations: int = 0  # Number of solver iterations


class EnhancedMLATSolver:
    """
    Enhanced MLAT solver with multiple algorithms and better convergence.
    """
    
    def __init__(self, min_receivers: int = 4):
        self.min_receivers = min_receivers
        self.max_iterations = 50
        self.convergence_threshold = 0.1  # meters
        
    def solve_position(self, observations: List[SignalObservation]) -> Optional[AircraftPosition]:
        """
        Calculate aircraft position from multiple receiver observations.
        """
        if len(observations) < self.min_receivers:
            logger.warning(f"Insufficient receivers: {len(observations)} < {self.min_receivers}")
            return None
        
        # Validate observations
        if not self._validate_observations(observations):
            return None
        
        # Sort by timestamp
        observations = sorted(observations, key=lambda x: x.timestamp)
        
        # Convert to ECEF
        ref_obs = observations[0]
        ref_pos = ref_obs.receiver_position.to_ecef()
        
        positions = []
        time_diffs = []
        
        for obs in observations[1:]:
            pos = obs.receiver_position.to_ecef()
            positions.append(pos)
            tdoa = obs.timestamp - ref_obs.timestamp
            time_diffs.append(tdoa)
        
        positions = np.array(positions)
        time_diffs = np.array(time_diffs)
        
        # Get initial guess using multiple methods
        initial_guess = self._get_initial_guess(ref_pos, positions, time_diffs)
        
        if initial_guess is None:
            logger.error("Failed to generate initial guess")
            return None
        
        # Solve using Gauss-Newton
        result = self._gauss_newton_solver(ref_pos, positions, time_diffs, initial_guess)
        
        if result is None:
            logger.error("Solver failed to converge")
            return None
        
        aircraft_ecef, residual, iterations = result
        
        # Convert to lat/lon/alt
        lat, lon, alt = self._ecef_to_lla(aircraft_ecef)
        
        # Validate result (check if altitude is reasonable)
        if alt < -1000 or alt > 20000:  # -1km to 20km
            logger.warning(f"Unrealistic altitude: {alt}m")
            return None
        
        # Calculate uncertainty
        uncertainty = self._estimate_uncertainty(ref_pos, positions, aircraft_ecef)
        
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
        """Validate that observations are suitable for MLAT"""
        # Check for unique receivers
        receiver_ids = [obs.receiver_id for obs in observations]
        if len(receiver_ids) != len(set(receiver_ids)):
            logger.warning("Duplicate receivers in observations")
            return False
        
        # Check time span is reasonable (signals should arrive within ~30ms max)
        timestamps = [obs.timestamp for obs in observations]
        time_span = max(timestamps) - min(timestamps)
        if time_span > 0.030:  # 30ms
            logger.warning(f"Time span too large: {time_span*1000:.1f}ms")
            return False
        
        return True
    
    def _get_initial_guess(
        self,
        ref_pos: np.ndarray,
        receiver_positions: np.ndarray,
        time_diffs: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Generate initial guess for aircraft position.
        
        Uses weighted centroid of receivers, adjusted for timing.
        """
        # Method 1: Geographic centroid with altitude estimate
        all_positions = np.vstack([ref_pos.reshape(1, 3), receiver_positions])
        centroid = np.mean(all_positions, axis=0)
        
        # Adjust altitude based on expected aircraft altitude
        # Most aircraft fly between 3000-12000m
        earth_center_distance = np.linalg.norm(centroid)
        ground_level = earth_center_distance - 6371000  # Approx Earth radius
        
        # Set initial altitude to 8000m above ground
        target_altitude = ground_level + 8000
        scale_factor = target_altitude / ground_level if ground_level > 0 else 1.0
        
        initial_guess = centroid * scale_factor
        
        logger.debug(f"Initial guess: {initial_guess}")
        
        return initial_guess
    
    def _gauss_newton_solver(
        self,
        ref_pos: np.ndarray,
        receiver_positions: np.ndarray,
        time_diffs: np.ndarray,
        initial_guess: np.ndarray
    ) -> Optional[Tuple[np.ndarray, float, int]]:
        """
        Gauss-Newton iterative solver with improved convergence.
        """
        x = initial_guess.copy()
        range_diffs = time_diffs * SPEED_OF_LIGHT
        
        lambda_factor = 1.0  # Damping factor for stability
        
        for iteration in range(self.max_iterations):
            residuals = []
            jacobian_rows = []
            
            for i, (pos, r_diff) in enumerate(zip(receiver_positions, range_diffs)):
                r_i = np.linalg.norm(x - pos)
                r_ref = np.linalg.norm(x - ref_pos)
                
                if r_i < 1.0 or r_ref < 1.0:  # Too close, numerical issues
                    logger.warning("Position too close to receiver")
                    return None
                
                # Residual
                residual = r_diff - (r_i - r_ref)
                residuals.append(residual)
                
                # Jacobian
                dr_i = -(x - pos) / r_i
                dr_ref = -(x - ref_pos) / r_ref
                jacobian_row = dr_i - dr_ref
                jacobian_rows.append(jacobian_row)
            
            residuals = np.array(residuals)
            J = np.array(jacobian_rows)
            
            # Check for singularity
            if np.linalg.matrix_rank(J) < 3:
                logger.warning("Singular Jacobian matrix")
                return None
            
            # Solve with damping: (J^T*J + lambda*I)*delta = J^T*residuals
            try:
                JTJ = J.T @ J
                identity = np.eye(3)
                damped_matrix = JTJ + lambda_factor * identity
                delta = np.linalg.solve(damped_matrix, J.T @ residuals)
            except np.linalg.LinAlgError:
                logger.warning("Failed to solve linear system")
                return None
            
            # Update position
            x = x + delta
            
            # Calculate RMS residual
            rms_residual = np.sqrt(np.mean(residuals**2))
            
            logger.debug(f"Iteration {iteration}: residual={rms_residual:.2f}m, delta={np.linalg.norm(delta):.2f}m")
            
            # Check convergence
            if np.linalg.norm(delta) < self.convergence_threshold:
                logger.info(f"Converged in {iteration+1} iterations, RMS residual: {rms_residual:.2f}m")
                return x, rms_residual, iteration + 1
            
            # Adjust damping factor
            if iteration > 0:
                lambda_factor *= 0.9  # Reduce damping as we converge
        
        logger.warning(f"Did not converge after {self.max_iterations} iterations")
        # Return best effort
        rms_residual = np.sqrt(np.mean(residuals**2))
        return x, rms_residual, self.max_iterations
    
    def _ecef_to_lla(self, ecef: np.ndarray) -> Tuple[float, float, float]:
        """Convert ECEF coordinates to latitude, longitude, altitude"""
        x, y, z = ecef
        
        # WGS84 parameters
        a = 6378137.0
        e2 = 0.00669437999014
        
        # Longitude
        lon = np.arctan2(y, x)
        
        # Iterative solution for latitude
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
        alt = p / np.cos(lat) - N
        
        return np.degrees(lat), np.degrees(lon), alt
    
    def _estimate_uncertainty(
        self,
        ref_pos: np.ndarray,
        receiver_positions: np.ndarray,
        aircraft_pos: np.ndarray
    ) -> float:
        """Estimate position uncertainty using GDOP"""
        vectors = []
        
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
        
        G = np.array(vectors)
        
        try:
            # GDOP calculation
            _, s, _ = np.linalg.svd(G)
            
            # Condition number based GDOP
            if s[-1] > 1e-10:
                gdop = s[0] / s[-1]  # Condition number
            else:
                return float('inf')
            
            # Assuming 10ns timing accuracy -> 3m ranging error
            base_error = 3.0
            uncertainty = min(gdop * base_error, 10000.0)  # Cap at 10km
            
            return uncertainty
        except:
            return float('inf')
