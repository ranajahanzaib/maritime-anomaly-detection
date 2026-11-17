import uuid
import datetime
from typing import List, Dict, Any, Tuple
from backend.detection.base import BaseDetector
from backend.detection.context.maritime_zones import MARITIME_SHIPPING_CORRIDORS
from backend.detection.context.interpreter import MaritimeContextInterpreter
from backend.trajectories.kinematics import haversine_distance_nm


class RouteDeviationDetector(BaseDetector):
    def __init__(self, deviation_threshold_nm: float = 3.5):
        self.threshold_nm = deviation_threshold_nm
        self.interpreter = MaritimeContextInterpreter()

    @property
    def detector_id(self) -> str:
        return "RULE_ROUTE_DEVIATION"

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    def detect(
        self,
        mmsi: int,
        points: List[Dict[str, Any]],
        vessel_type: str = "Cargo",
        corridors: List[Dict[str, Any]] | None = None,
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        events = []
        if len(points) < 8:
            return events

        active_corridors = corridors or MARITIME_SHIPPING_CORRIDORS
        if not active_corridors:
            return events

        def to_dt(t):
            if isinstance(t, str):
                return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            return t

        # Find closest corridor to the start of this trajectory
        start_pt = points[0]
        best_corridor = None
        min_start_dist = float("inf")

        for corr in active_corridors:
            for wp in corr["waypoints"]:
                d = haversine_distance_nm(start_pt["latitude"], start_pt["longitude"], wp[0], wp[1])
                if d < min_start_dist:
                    min_start_dist = d
                    best_corridor = corr

        # If trajectory is within proximity of a recognized corridor, track deviations
        if best_corridor and min_start_dist <= 15.0:
            max_dev_nm = 0.0
            worst_pt = None
            deviating_points = []

            for pt in points:
                # Find min distance to any segment of corridor
                min_pt_corr_dist = min(
                    haversine_distance_nm(pt["latitude"], pt["longitude"], wp[0], wp[1])
                    for wp in best_corridor["waypoints"]
                )
                if min_pt_corr_dist > (best_corridor.get("width_nm", 3.0) + self.threshold_nm):
                    deviating_points.append(pt)
                    if min_pt_corr_dist > max_dev_nm:
                        max_dev_nm = min_pt_corr_dist
                        worst_pt = pt

            if len(deviating_points) >= 4 and worst_pt:
                t_start = to_dt(deviating_points[0]["timestamp"])
                t_end = to_dt(deviating_points[-1]["timestamp"])
                duration_hrs = (t_end - t_start).total_seconds() / 3600.0

                context = self.interpreter.interpret_route_deviation(
                    max_dev_nm, best_corridor["name"]
                )

                score = min(1.0, 0.4 + (max_dev_nm / 15.0) * 0.5)
                severity = "HIGH" if max_dev_nm > 8.0 else "MEDIUM"

                explanation = (
                    f"Vessel substantially deviated from established shipping corridor '{best_corridor['name']}'. "
                    f"Maximum observed lateral deviation was {max_dev_nm:.1f}nm from fairway centerline. "
                    f"Context: {context['contextual_explanation']}"
                )

                events.append({
                    "id": f"evt_dev_{mmsi}_{uuid.uuid4().hex[:8]}",
                    "category": "UNUSUAL_ROUTE_DEVIATION",
                    "primary_mmsi": mmsi,
                    "secondary_mmsi": None,
                    "detector_id": self.detector_id,
                    "detector_version": self.detector_version,
                    "deviation_score": round(score, 3),
                    "severity": severity,
                    "confidence": 0.85,
                    "start_time": t_start,
                    "end_time": t_end,
                    "duration_seconds": (t_end - t_start).total_seconds(),
                    "latitude": worst_pt["latitude"],
                    "longitude": worst_pt["longitude"],
                    "bbox_geojson": {
                        "type": "LineString",
                        "coordinates": [[p["longitude"], p["latitude"]] for p in deviating_points[::max(1, len(deviating_points) // 20)]],
                    },
                    "contextual_state": context["contextual_state"],
                    "contextual_explanation": context["contextual_explanation"],
                    "explanation": explanation,
                    "feature_attributions": {
                        "corridor_name": best_corridor["name"],
                        "max_deviation_nm": round(max_dev_nm, 2),
                        "corridor_width_nm": best_corridor.get("width_nm", 3.0),
                        "deviating_points_count": len(deviating_points),
                    },
                    "evidence": {
                        "expected_corridor_waypoints": [
                            {"lat": wp[0], "lon": wp[1]} for wp in best_corridor["waypoints"]
                        ],
                        "actual_peak_deviation_coords": [worst_pt["latitude"], worst_pt["longitude"]],
                    },
                    "is_synthetic": is_synthetic,
                    "status": "NEW",
                })

        return events
