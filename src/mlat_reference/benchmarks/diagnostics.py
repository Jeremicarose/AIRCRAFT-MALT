"""Observe solver decisions without changing its numerical algorithm."""

import math
from statistics import median

import numpy as np

from mlat_reference.solver.robust import RobustMLATSolver


class DiagnosticSolver(RobustMLATSolver):
    def solve_position(self, observations):
        self.diagnostics = {"failure_category": "insufficient_receivers"}
        result = super().solve_position(observations)
        if result is not None:
            self.diagnostics["failure_category"] = None
        return result

    def _validate_observations(self, observations):
        valid = super()._validate_observations(observations)
        self.diagnostics["failure_category"] = (
            "timestamp_validation" if valid else "observation_validation"
        )
        return valid

    def _get_smart_initial_guess(self, *args):
        self.diagnostics["failure_category"] = "initial_guess"
        return super()._get_smart_initial_guess(*args)

    def _levenberg_marquardt(self, *args):
        self.diagnostics["failure_category"] = "optimizer_rejected"
        result = super()._levenberg_marquardt(*args)
        if result is not None:
            self.diagnostics.update(residual_m=float(result[1]), iterations=int(result[2]))
        return result

    def _validate_result(self, latitude, longitude, altitude, residual):
        valid = super()._validate_result(latitude, longitude, altitude, residual)
        self.diagnostics.update(
            candidate_altitude_m=float(altitude),
            failure_category=(
                None
                if valid
                else (
                    "altitude_out_of_bounds"
                    if not -500 <= altitude <= 15000
                    else "residual_out_of_bounds" if residual > 5000 else "coordinate_out_of_bounds"
                )
            ),
        )
        return valid


def summarize(values):
    values = [float(value) for value in values if value is not None and math.isfinite(value)]
    if not values:
        return None
    return {
        "count": len(values),
        "median": median(values),
        "p95": float(np.percentile(values, 95)),
        "minimum": min(values),
        "maximum": max(values),
    }


def receiver_geometry(observations, truth):
    ordered = sorted(observations, key=lambda item: item.timestamp_ns)
    points = [observation.receiver_position.to_ecef() for observation in ordered]
    target = truth.to_ecef()
    vectors = [(target - point) / np.linalg.norm(target - point) for point in points]
    singular = np.linalg.svd(
        np.array([vector - vectors[0] for vector in vectors[1:]]), compute_uv=False
    )
    baselines = [
        float(np.linalg.norm(first - second))
        for i, first in enumerate(points)
        for second in points[i + 1 :]
    ]
    altitudes = [observation.receiver_position.altitude for observation in ordered]
    return {
        "receiver_count": len(points),
        "minimum_baseline_m": min(baselines),
        "maximum_baseline_m": max(baselines),
        "vertical_aperture_m": max(altitudes) - min(altitudes),
        "tdoa_condition_number_at_reference": (
            float(singular[0] / singular[-1]) if singular[-1] > 1e-12 else None
        ),
        "definition": "Singular-value ratio of the TDOA Jacobian at the aircraft-reported reference position; not calibrated GDOP or confidence.",
    }
