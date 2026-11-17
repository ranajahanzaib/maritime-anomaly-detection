import uuid
import datetime
from typing import List, Dict, Any
from backend.detection.base import BaseDetector


class AISTransmissionGapDetector(BaseDetector):
    def __init__(self, min_gap_hours: float = 2.0):
        self.min_gap_hours = min_gap_hours

    @property
    def detector_id(self) -> str:
        return "RULE_AIS_TRANSMISSION_GAP"

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    def detect_from_gaps(
        self,
        mmsi: int,
        gaps: List[Dict[str, Any]],
        vessel_type: str = "Cargo",
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        events = []
        for g in gaps:
            duration_hrs = g["duration_hours"]
            if duration_hrs >= self.min_gap_hours:
                # Explicit data quality observability explanation
                explanation = (
                    f"AIS transmission gap of {duration_hrs:.1f} hours detected (from {g['start_time']} to {g['end_time']}). "
                    f"Displacement during gap: {g['displacement_nm']}nm (implied drift/transit speed: {g['implied_speed_knots']} kts). "
                    "Note: Transmission gaps reflect VHF line-of-sight coverage loss, satellite receiver pass intervals, "
                    "or transponder powering; they are telemetry observability events, not proof of illicit intent."
                )

                score = min(0.9, 0.3 + (duration_hrs / 12.0) * 0.4)
                severity = "MEDIUM" if duration_hrs > 6.0 else "LOW"

                events.append({
                    "id": f"evt_gap_{mmsi}_{uuid.uuid4().hex[:8]}",
                    "category": "AIS_TRANSMISSION_GAP",
                    "primary_mmsi": mmsi,
                    "secondary_mmsi": None,
                    "detector_id": self.detector_id,
                    "detector_version": self.detector_version,
                    "deviation_score": round(score, 3),
                    "severity": severity,
                    "confidence": 0.99,
                    "start_time": g["start_time"],
                    "end_time": g["end_time"],
                    "duration_seconds": g["duration_seconds"],
                    "latitude": g["start_lat"],
                    "longitude": g["start_lon"],
                    "bbox_geojson": {
                        "type": "LineString",
                        "coordinates": [
                            [g["start_lon"], g["start_lat"]],
                            [g["end_lon"], g["end_lat"]],
                        ],
                    },
                    "contextual_state": "CONTEXT_UNAVAILABLE",
                    "contextual_explanation": "Observability / RF coverage gap. Original observations preserved without interpolation.",
                    "explanation": explanation,
                    "feature_attributions": {
                        "gap_duration_hours": duration_hrs,
                        "displacement_nm": g["displacement_nm"],
                        "implied_speed_knots": g["implied_speed_knots"],
                    },
                    "evidence": {
                        "last_reported_position": [g["start_lat"], g["start_lon"]],
                        "reappearance_position": [g["end_lat"], g["end_lon"]],
                        "gap_duration_seconds": g["duration_seconds"],
                    },
                    "data_quality_warnings": [
                        "AIS signal loss: observations missing for > 2 hours.",
                        "True trajectory during interval is unknown.",
                    ],
                    "is_synthetic": is_synthetic,
                    "status": "NEW",
                })
        return events

    def detect(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return self.detect_from_gaps(*args, **kwargs)
