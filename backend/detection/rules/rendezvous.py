import uuid
import datetime
from typing import List, Dict, Any
from backend.detection.base import BaseDetector
from backend.detection.context.interpreter import MaritimeContextInterpreter
from backend.features.interactions import compute_pairwise_interaction_timeline


class RendezvousDetector(BaseDetector):
    def __init__(
        self,
        proximity_distance_meters: float = 600.0,
        min_rendezvous_minutes: float = 15.0,
        max_relative_speed_knots: float = 4.0,
    ):
        self.max_distance_meters = proximity_distance_meters
        self.min_duration_minutes = min_rendezvous_minutes
        self.max_rel_speed = max_relative_speed_knots
        self.interpreter = MaritimeContextInterpreter()

    @property
    def detector_id(self) -> str:
        return "RULE_RENDEZVOUS"

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    def detect_pair(
        self,
        mmsi_a: int,
        points_a: List[Dict[str, Any]],
        mmsi_b: int,
        points_b: List[Dict[str, Any]],
        vessel_a_type: str = "Cargo",
        vessel_b_type: str = "Tug",
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        events = []
        if not points_a or not points_b:
            return events

        timeline = compute_pairwise_interaction_timeline(points_a, points_b)
        if not timeline:
            return events

        # Find continuous sequences where distance <= max_distance_meters and relative speed is low
        rendezvous_segments = []
        current_seq = []

        for item in timeline:
            if item["distance_meters"] <= self.max_distance_meters and item["relative_speed_knots"] <= self.max_rel_speed:
                current_seq.append(item)
            else:
                if current_seq:
                    rendezvous_segments.append(current_seq)
                    current_seq = []

        if current_seq:
            rendezvous_segments.append(current_seq)

        for seq in rendezvous_segments:
            t_start = seq[0]["timestamp"]
            t_end = seq[-1]["timestamp"]
            duration_mins = (t_end - t_start).total_seconds() / 60.0

            if duration_mins >= self.min_duration_minutes:
                center_lat = (seq[0]["lat_a"] + seq[0]["lat_b"]) / 2.0
                center_lon = (seq[0]["lon_a"] + seq[0]["lon_b"]) / 2.0
                min_dist_m = min(s["distance_meters"] for s in seq)
                avg_dist_m = sum(s["distance_meters"] for s in seq) / len(seq)
                avg_rel_speed = sum(s["relative_speed_knots"] for s in seq) / len(seq)

                context = self.interpreter.interpret_rendezvous(
                    center_lat, center_lon, duration_mins, vessel_a_type, vessel_b_type
                )

                score = min(1.0, 0.5 + (duration_mins / 60.0) * 0.4)
                severity = "LOW" if context["is_benign_explanation"] else ("HIGH" if duration_mins > 45 else "MEDIUM")

                explanation = (
                    f"Rendezvous observed between MMSI {mmsi_a} ({vessel_a_type}) and MMSI {mmsi_b} ({vessel_b_type}). "
                    f"Maintained close proximity (min {min_dist_m:.0f}m, avg {avg_dist_m:.0f}m) for {duration_mins:.0f} min "
                    f"with low relative speed ({avg_rel_speed:.1f} kts). Context: {context['contextual_explanation']}"
                )

                events.append({
                    "id": f"evt_rdz_{mmsi_a}_{mmsi_b}_{uuid.uuid4().hex[:8]}",
                    "category": "RENDEZVOUS",
                    "primary_mmsi": mmsi_a,
                    "secondary_mmsi": mmsi_b,
                    "detector_id": self.detector_id,
                    "detector_version": self.detector_version,
                    "deviation_score": round(score, 3),
                    "severity": severity,
                    "confidence": 0.92,
                    "start_time": t_start,
                    "end_time": t_end,
                    "duration_seconds": (t_end - t_start).total_seconds(),
                    "latitude": center_lat,
                    "longitude": center_lon,
                    "bbox_geojson": {
                        "type": "LineString",
                        "coordinates": [
                            [seq[0]["lon_a"], seq[0]["lat_a"]],
                            [seq[0]["lon_b"], seq[0]["lat_b"]],
                        ],
                    },
                    "contextual_state": context["contextual_state"],
                    "contextual_explanation": context["contextual_explanation"],
                    "explanation": explanation,
                    "feature_attributions": {
                        "duration_minutes": round(duration_mins, 1),
                        "min_distance_meters": round(min_dist_m, 1),
                        "avg_relative_speed_knots": round(avg_rel_speed, 2),
                        "pairwise_observations": len(seq),
                    },
                    "evidence": {
                        "interaction_timeline": [
                            {
                                "timestamp": s["timestamp"].isoformat() if isinstance(s["timestamp"], datetime.datetime) else str(s["timestamp"]),
                                "distance_meters": s["distance_meters"],
                                "vessel_a_sog": s["vessel_a_sog"],
                                "vessel_b_sog": s["vessel_b_sog"],
                                "relative_speed": s["relative_speed_knots"],
                                "course_diff_deg": s["course_diff_deg"],
                            }
                            for s in seq[::max(1, len(seq) // 25)]  # sample up to 25 steps for visualization
                        ],
                    },
                    "is_synthetic": is_synthetic,
                    "status": "NEW",
                })

        return events

    def detect(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return self.detect_pair(*args, **kwargs)
