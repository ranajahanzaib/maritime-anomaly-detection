import uuid
import datetime
from typing import List, Dict, Any, Optional
from backend.detection.base import BaseDetector
from backend.features.movement import compute_movement_features
from backend.trajectories.kinematics import haversine_distance_nm


class HistoricalInconsistencyDetector(BaseDetector):
    def __init__(self, min_historical_observations: int = 30):
        self.min_history = min_historical_observations

    @property
    def detector_id(self) -> str:
        return "STAT_HISTORICAL_INCONSISTENCY"

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    def detect(
        self,
        mmsi: int,
        points: List[Dict[str, Any]],
        historical_profile: Optional[Dict[str, Any]] = None,
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        events = []
        if len(points) < 8 or not historical_profile:
            return events

        # Check if historical baseline had enough observations
        hist_count = historical_profile.get("observation_count", 0)
        if hist_count < self.min_history:
            return events

        mov = compute_movement_features(points)
        obs_mean_speed = mov["speed_mean"]
        hist_mean_speed = historical_profile.get("avg_speed_knots", obs_mean_speed)
        hist_max_speed = historical_profile.get("max_speed_knots", 25.0)

        # Check geographic operating region
        hist_center_lat = historical_profile.get("center_lat")
        hist_center_lon = historical_profile.get("center_lon")
        hist_max_radius_nm = historical_profile.get("operating_radius_nm", 50.0)

        curr_center_lat = float(points[len(points) // 2]["latitude"])
        curr_center_lon = float(points[len(points) // 2]["longitude"])

        dist_from_home_nm = 0.0
        if hist_center_lat is not None and hist_center_lon is not None:
            dist_from_home_nm = haversine_distance_nm(
                hist_center_lat, hist_center_lon, curr_center_lat, curr_center_lon
            )

        speed_diff = abs(obs_mean_speed - hist_mean_speed)
        is_speed_inconsistent = speed_diff > 8.0 and obs_mean_speed > (hist_mean_speed * 1.6)
        is_region_inconsistent = dist_from_home_nm > (hist_max_radius_nm * 2.5) and dist_from_home_nm > 40.0

        if is_speed_inconsistent or is_region_inconsistent:
            def to_dt(t):
                if isinstance(t, str):
                    return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
                return t

            t_start = to_dt(points[0]["timestamp"])
            t_end = to_dt(points[-1]["timestamp"])

            score = 0.75 if (is_speed_inconsistent and is_region_inconsistent) else 0.62
            severity = "HIGH" if (is_speed_inconsistent and is_region_inconsistent) else "MEDIUM"

            reasons = []
            if is_speed_inconsistent:
                reasons.append(
                    f"Speed regime shifted: observed {obs_mean_speed:.1f} kts vs historical baseline {hist_mean_speed:.1f} kts"
                )
            if is_region_inconsistent:
                reasons.append(
                    f"Geographic shift: vessel observed {dist_from_home_nm:.1f}nm from historical primary operating area"
                )

            explanation = (
                f"Trajectory is inconsistent with vessel MMSI {mmsi}'s historical baseline profile ({hist_count} previous observations). "
                + "; ".join(reasons) + "."
            )

            events.append({
                "id": f"evt_hist_{mmsi}_{uuid.uuid4().hex[:8]}",
                "category": "HISTORICAL_INCONSISTENCY",
                "primary_mmsi": mmsi,
                "secondary_mmsi": None,
                "detector_id": self.detector_id,
                "detector_version": self.detector_version,
                "deviation_score": round(score, 3),
                "severity": severity,
                "confidence": 0.84,
                "start_time": t_start,
                "end_time": t_end,
                "duration_seconds": (t_end - t_start).total_seconds(),
                "latitude": curr_center_lat,
                "longitude": curr_center_lon,
                "bbox_geojson": {
                    "type": "Point",
                    "coordinates": [curr_center_lon, curr_center_lat],
                },
                "contextual_state": "POTENTIALLY_RELEVANT",
                "contextual_explanation": "Behavioral deviation relative to vessel-specific historical baseline.",
                "explanation": explanation,
                "feature_attributions": {
                    "speed_difference_knots": round(speed_diff, 2),
                    "distance_from_home_nm": round(dist_from_home_nm, 2),
                    "historical_observation_count": hist_count,
                },
                "evidence": {
                    "historical_profile": historical_profile,
                    "current_segment_metrics": mov,
                },
                "is_synthetic": is_synthetic,
                "status": "NEW",
            })

        return events
