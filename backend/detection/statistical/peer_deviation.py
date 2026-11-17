import uuid
import datetime
from typing import List, Dict, Any
import numpy as np
from backend.detection.base import BaseDetector
from backend.features.movement import compute_movement_features

# Default baseline speed profiles by vessel type (mean knots, std knots)
FLEET_PEER_BASELINES: Dict[str, Dict[str, float]] = {
    "Cargo": {"speed_mean": 13.5, "speed_std": 2.8, "speed_p95_max": 20.0},
    "Tanker": {"speed_mean": 12.0, "speed_std": 2.5, "speed_p95_max": 18.0},
    "Fishing": {"speed_mean": 4.5, "speed_std": 3.0, "speed_p95_max": 12.0},
    "Passenger": {"speed_mean": 18.0, "speed_std": 4.5, "speed_p95_max": 26.0},
    "Tug": {"speed_mean": 8.0, "speed_std": 3.0, "speed_p95_max": 14.0},
    "Other": {"speed_mean": 10.0, "speed_std": 4.0, "speed_p95_max": 22.0},
}


class PeerGroupDeviationDetector(BaseDetector):
    def __init__(self, z_score_threshold: float = 2.5):
        self.threshold = z_score_threshold

    @property
    def detector_id(self) -> str:
        return "STAT_PEER_GROUP_DEVIATION"

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    def detect(
        self,
        mmsi: int,
        points: List[Dict[str, Any]],
        vessel_type: str = "Cargo",
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        events = []
        if len(points) < 8:
            return events

        baseline = FLEET_PEER_BASELINES.get(vessel_type, FLEET_PEER_BASELINES["Other"])
        mov = compute_movement_features(points)
        obs_speed_mean = mov["speed_mean"]
        obs_speed_p95 = mov["speed_p95"]

        peer_mean = baseline["speed_mean"]
        peer_std = baseline["speed_std"]
        z_score = abs(obs_speed_mean - peer_mean) / peer_std

        if z_score >= self.threshold or obs_speed_p95 > baseline["speed_p95_max"]:
            def to_dt(t):
                if isinstance(t, str):
                    return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
                return t

            t_start = to_dt(points[0]["timestamp"])
            t_end = to_dt(points[-1]["timestamp"])
            center_lat = float(points[len(points) // 2]["latitude"])
            center_lon = float(points[len(points) // 2]["longitude"])

            score = min(1.0, 0.5 + (z_score / 6.0) * 0.4)
            severity = "HIGH" if z_score > 3.5 else "MEDIUM"

            explanation = (
                f"Vessel speed characteristics significantly deviate from its peer group ({vessel_type}). "
                f"Observed average speed was {obs_speed_mean:.1f} kts (z-score: {z_score:.1f}), compared with "
                f"peer baseline of {peer_mean:.1f} ± {peer_std:.1f} kts."
            )

            events.append({
                "id": f"evt_peer_{mmsi}_{uuid.uuid4().hex[:8]}",
                "category": "PEER_GROUP_DEVIATION",
                "primary_mmsi": mmsi,
                "secondary_mmsi": None,
                "detector_id": self.detector_id,
                "detector_version": self.detector_version,
                "deviation_score": round(score, 3),
                "severity": severity,
                "confidence": 0.82,
                "start_time": t_start,
                "end_time": t_end,
                "duration_seconds": (t_end - t_start).total_seconds(),
                "latitude": center_lat,
                "longitude": center_lon,
                "bbox_geojson": {
                    "type": "Point",
                    "coordinates": [center_lon, center_lat],
                },
                "contextual_state": "EXPECTED_CONTEXT" if vessel_type == "Special Craft" else "POTENTIALLY_RELEVANT",
                "contextual_explanation": f"Statistical speed distribution evaluated against {vessel_type} peer group.",
                "explanation": explanation,
                "feature_attributions": {
                    "observed_speed_mean": obs_speed_mean,
                    "peer_speed_mean": peer_mean,
                    "peer_speed_std": peer_std,
                    "z_score": round(z_score, 2),
                    "vessel_type": vessel_type,
                },
                "evidence": {
                    "observed_distribution": {
                        "mean": obs_speed_mean,
                        "p95": obs_speed_p95,
                        "max": mov["speed_max"],
                    },
                    "peer_baseline": baseline,
                },
                "is_synthetic": is_synthetic,
                "status": "NEW",
            })

        return events
