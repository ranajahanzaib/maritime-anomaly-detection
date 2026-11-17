import uuid
import datetime
from typing import List, Dict, Any
from backend.detection.base import BaseDetector
from backend.trajectories.kinematics import derive_point_kinematics


class SpeedViolationDetector(BaseDetector):
    def __init__(self, max_realistic_speed_knots: float = 45.0):
        self.max_speed = max_realistic_speed_knots

    @property
    def detector_id(self) -> str:
        return "RULE_IMPLAUSIBLE_MOVEMENT"

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
        if len(points) < 2:
            return events

        def to_dt(t):
            if isinstance(t, str):
                return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            return t

        for i in range(1, len(points)):
            k = derive_point_kinematics(points[i - 1], points[i])
            if k["derived_speed_knots"] > self.max_speed:
                t1 = to_dt(points[i - 1]["timestamp"])
                t2 = to_dt(points[i]["timestamp"])
                explanation = (
                    f"Physically implausible position displacement between consecutive AIS reports: "
                    f"implied speed {k['derived_speed_knots']:.1f} kts exceeds physical limit ({self.max_speed} kts). "
                    "Likely GPS jump, spoofing, or corrupted coordinate transmission."
                )
                events.append({
                    "id": f"evt_jump_{mmsi}_{uuid.uuid4().hex[:8]}",
                    "category": "IMPLAUSIBLE_MOVEMENT",
                    "primary_mmsi": mmsi,
                    "secondary_mmsi": None,
                    "detector_id": self.detector_id,
                    "detector_version": self.detector_version,
                    "deviation_score": 0.95,
                    "severity": "CRITICAL",
                    "confidence": 0.95,
                    "start_time": t1,
                    "end_time": t2,
                    "duration_seconds": (t2 - t1).total_seconds(),
                    "latitude": points[i]["latitude"],
                    "longitude": points[i]["longitude"],
                    "bbox_geojson": {
                        "type": "LineString",
                        "coordinates": [
                            [points[i - 1]["longitude"], points[i - 1]["latitude"]],
                            [points[i]["longitude"], points[i]["latitude"]],
                        ],
                    },
                    "contextual_state": "CONTEXT_UNAVAILABLE",
                    "contextual_explanation": "Sensor / telemetry anomaly independent of maritime context.",
                    "explanation": explanation,
                    "feature_attributions": {
                        "derived_speed_knots": k["derived_speed_knots"],
                        "displacement_nm": k["dist_nm"],
                        "dt_seconds": k["dt_seconds"],
                    },
                    "evidence": {
                        "p1": [points[i - 1]["latitude"], points[i - 1]["longitude"]],
                        "p2": [points[i]["latitude"], points[i]["longitude"]],
                    },
                    "is_synthetic": is_synthetic,
                    "status": "NEW",
                })
        return events
