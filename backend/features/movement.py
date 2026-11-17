import math
from typing import List, Dict, Any
import numpy as np
from backend.trajectories.kinematics import haversine_distance_nm, derive_point_kinematics


def compute_movement_features(points: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Computes movement kinematics features over a sequence of points.
    """
    if len(points) < 2:
        sog = float(points[0].get("sog", 0.0)) if points else 0.0
        return {
            "speed_mean": sog,
            "speed_std": 0.0,
            "speed_max": sog,
            "speed_p95": sog,
            "acceleration_mean": 0.0,
            "acceleration_std": 0.0,
            "turn_rate_mean": 0.0,
            "turn_rate_max": 0.0,
            "straightness_ratio": 1.0,
            "stop_ratio": 1.0 if sog < 1.0 else 0.0,
            "total_distance_nm": 0.0,
        }

    sogs = [float(p.get("sog", 0.0)) for p in points]
    speeds = []
    accels = []
    turns = []
    total_dist = 0.0

    for i in range(1, len(points)):
        k = derive_point_kinematics(points[i - 1], points[i])
        speeds.append(k["derived_speed_knots"])
        accels.append(abs(k["acceleration_ms2"]))
        turns.append(k["turn_rate_deg_per_min"])
        total_dist += k["dist_nm"]

    # Straightness ratio: straight line distance from start to end / total distance
    net_dist = haversine_distance_nm(
        points[0]["latitude"], points[0]["longitude"],
        points[-1]["latitude"], points[-1]["longitude"]
    )
    straightness = (net_dist / total_dist) if total_dist > 0.001 else 1.0
    straightness = min(1.0, max(0.0, straightness))

    stop_points = sum(1 for s in sogs if s < 1.0)
    stop_ratio = stop_points / len(sogs) if sogs else 0.0

    return {
        "speed_mean": round(float(np.mean(sogs)), 2),
        "speed_std": round(float(np.std(sogs)), 2),
        "speed_max": round(float(np.max(sogs)), 2),
        "speed_p95": round(float(np.percentile(sogs, 95)), 2),
        "acceleration_mean": round(float(np.mean(accels)), 4) if accels else 0.0,
        "acceleration_std": round(float(np.std(accels)), 4) if accels else 0.0,
        "turn_rate_mean": round(float(np.mean(turns)), 2) if turns else 0.0,
        "turn_rate_max": round(float(np.max(turns)), 2) if turns else 0.0,
        "straightness_ratio": round(straightness, 3),
        "stop_ratio": round(stop_ratio, 3),
        "total_distance_nm": round(total_dist, 2),
    }
