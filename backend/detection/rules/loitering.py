import uuid
import datetime
from typing import List, Dict, Any
from backend.detection.base import BaseDetector
from backend.detection.context.interpreter import MaritimeContextInterpreter
from backend.trajectories.kinematics import haversine_distance_nm


class LoiteringDetector(BaseDetector):
    def __init__(
        self,
        max_loitering_speed_knots: float = 1.5,
        max_loitering_radius_nm: float = 1.2,
        min_loitering_duration_hours: float = 2.0,
    ):
        self.max_speed = max_loitering_speed_knots
        self.max_radius = max_loitering_radius_nm
        self.min_duration = min_loitering_duration_hours
        self.interpreter = MaritimeContextInterpreter()

    @property
    def detector_id(self) -> str:
        return "RULE_LOITERING_DWELL"

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
        if len(points) < 5:
            return events

        def to_dt(t):
            if isinstance(t, str):
                return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            return t

        # Find continuous sequences where speed is low and spatial spread is small
        i = 0
        n = len(points)

        while i < n:
            if float(points[i].get("sog", 0.0)) <= self.max_speed:
                cluster_start = i
                center_lat = float(points[i]["latitude"])
                center_lon = float(points[i]["longitude"])
                j = i + 1

                while j < n:
                    sog_j = float(points[j].get("sog", 0.0))
                    d = haversine_distance_nm(
                        center_lat, center_lon,
                        float(points[j]["latitude"]), float(points[j]["longitude"])
                    )
                    if sog_j <= self.max_speed and d <= self.max_radius:
                        j += 1
                    else:
                        break

                t_start = to_dt(points[cluster_start]["timestamp"])
                t_end = to_dt(points[j - 1]["timestamp"])
                duration_hrs = (t_end - t_start).total_seconds() / 3600.0

                if duration_hrs >= self.min_duration:
                    context = self.interpreter.interpret_loitering(
                        center_lat, center_lon, duration_hrs, vessel_type
                    )

                    score = min(1.0, 0.4 + (duration_hrs / 12.0) * 0.5)
                    if context["is_benign_explanation"]:
                        severity = "LOW"
                    elif duration_hrs > 8.0:
                        severity = "HIGH"
                    else:
                        severity = "MEDIUM"

                    explanation = (
                        f"Vessel maintained low speed (avg < {self.max_speed} kts) within "
                        f"{self.max_radius:.1f}nm radius for {duration_hrs:.1f} hours. "
                        f"Context: {context['contextual_explanation']}"
                    )

                    events.append({
                        "id": f"evt_loiter_{mmsi}_{uuid.uuid4().hex[:8]}",
                        "category": "LOITERING",
                        "primary_mmsi": mmsi,
                        "secondary_mmsi": None,
                        "detector_id": self.detector_id,
                        "detector_version": self.detector_version,
                        "deviation_score": round(score, 3),
                        "severity": severity,
                        "confidence": 0.88,
                        "start_time": t_start,
                        "end_time": t_end,
                        "duration_seconds": (t_end - t_start).total_seconds(),
                        "latitude": center_lat,
                        "longitude": center_lon,
                        "bbox_geojson": {
                            "type": "Point",
                            "coordinates": [center_lon, center_lat],
                        },
                        "contextual_state": context["contextual_state"],
                        "contextual_explanation": context["contextual_explanation"],
                        "explanation": explanation,
                        "feature_attributions": {
                            "dwell_duration_hours": round(duration_hrs, 2),
                            "max_radius_nm": round(self.max_radius, 2),
                            "avg_sog": round(float(points[cluster_start].get("sog", 0.0)), 2),
                            "inside_anchorage_or_port": context["is_benign_explanation"],
                        },
                        "evidence": {
                            "cluster_point_count": j - cluster_start,
                            "center_coordinates": [center_lat, center_lon],
                            "radius_meters": round(self.max_radius * 1852.0, 1),
                        },
                        "is_synthetic": is_synthetic,
                        "status": "NEW",
                    })

                i = j
            else:
                i += 1

        return events
