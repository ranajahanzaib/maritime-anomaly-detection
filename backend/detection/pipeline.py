import uuid
from typing import List, Dict, Any, Optional

from backend.detection.rules.loitering import LoiteringDetector
from backend.detection.rules.rendezvous import RendezvousDetector
from backend.detection.rules.route_deviation import RouteDeviationDetector
from backend.detection.rules.speed_violation import SpeedViolationDetector
from backend.detection.rules.ais_gap import AISTransmissionGapDetector
from backend.detection.statistical.peer_deviation import PeerGroupDeviationDetector
from backend.detection.statistical.historical_inconsistency import HistoricalInconsistencyDetector
from backend.detection.statistical.isolation_forest import TrajectoryIsolationForestDetector
from backend.ml.inference.scorer import TrajectorySequenceScorer


class MaritimeAnomalyDetectionPipeline:
    def __init__(self):
        self.loitering_detector = LoiteringDetector()
        self.rendezvous_detector = RendezvousDetector()
        self.route_detector = RouteDeviationDetector()
        self.speed_detector = SpeedViolationDetector()
        self.ais_gap_detector = AISTransmissionGapDetector()
        self.peer_detector = PeerGroupDeviationDetector()
        self.hist_detector = HistoricalInconsistencyDetector()
        self.iso_forest_detector = TrajectoryIsolationForestDetector()

    def run_trajectory_detection(
        self,
        mmsi: int,
        points: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None,
        vessel_type: str = "Cargo",
        historical_profile: Optional[Dict[str, Any]] = None,
        trained_model_id: Optional[str] = None,
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Executes complete multi-detector pipeline on a single vessel track.
        Returns list of explainable BehavioralEvent dictionaries.
        """
        all_events = []

        # 1. Kinematic / Speed jump checks
        speed_events = self.speed_detector.detect(mmsi, points, vessel_type=vessel_type, is_synthetic=is_synthetic)
        all_events.extend(speed_events)

        # 2. AIS Transmission Gaps
        if gaps:
            gap_events = self.ais_gap_detector.detect_from_gaps(mmsi, gaps, vessel_type=vessel_type, is_synthetic=is_synthetic)
            all_events.extend(gap_events)

        # 3. Loitering and unusual dwell
        loiter_events = self.loitering_detector.detect(mmsi, points, vessel_type=vessel_type, is_synthetic=is_synthetic)
        all_events.extend(loiter_events)

        # 4. Route corridor deviation
        route_events = self.route_detector.detect(mmsi, points, vessel_type=vessel_type, is_synthetic=is_synthetic)
        all_events.extend(route_events)

        # 5. Peer group statistical deviation
        peer_events = self.peer_detector.detect(mmsi, points, vessel_type=vessel_type, is_synthetic=is_synthetic)
        all_events.extend(peer_events)

        # 6. Historical profile inconsistency
        if historical_profile:
            hist_events = self.hist_detector.detect(mmsi, points, historical_profile=historical_profile, is_synthetic=is_synthetic)
            all_events.extend(hist_events)

        # 7. Isolation forest (if fitted)
        if self.iso_forest_detector.is_fitted:
            iso_events = self.iso_forest_detector.detect(mmsi, points, vessel_type=vessel_type, is_synthetic=is_synthetic)
            all_events.extend(iso_events)

        # 8. Temporal Deep Learning Model (TCN or Transformer)
        if trained_model_id:
            try:
                scorer = TrajectorySequenceScorer(trained_model_id)
                res = scorer.score_trajectory(points)
                if res["is_anomalous"]:
                    t_start = points[0]["timestamp"]
                    t_end = points[-1]["timestamp"]
                    center_lat = float(points[len(points) // 2]["latitude"])
                    center_lon = float(points[len(points) // 2]["longitude"])

                    all_events.append({
                        "id": f"evt_dl_{mmsi}_{uuid.uuid4().hex[:8]}",
                        "category": "PEER_GROUP_DEVIATION",
                        "primary_mmsi": mmsi,
                        "secondary_mmsi": None,
                        "detector_id": f"DL_{scorer.model_type}",
                        "detector_version": "1.0.0",
                        "deviation_score": res["anomaly_score"],
                        "severity": "HIGH" if res["anomaly_score"] > 0.8 else "MEDIUM",
                        "confidence": 0.86,
                        "start_time": t_start,
                        "end_time": t_end,
                        "duration_seconds": (t_end - t_start).total_seconds() if hasattr(t_end, "__sub__") else 0.0,
                        "latitude": center_lat,
                        "longitude": center_lon,
                        "bbox_geojson": {"type": "Point", "coordinates": [center_lon, center_lat]},
                        "contextual_state": "POTENTIALLY_RELEVANT",
                        "contextual_explanation": f"Deep sequence reconstruction error exceeded learned baseline threshold ({res['threshold']}).",
                        "explanation": (
                            f"Temporal deep learning model ({scorer.model_type}) detected sequence pattern deviation. "
                            f"Peak sequence reconstruction error: {res['max_reconstruction_error']:.5f} (baseline threshold: {res['threshold']:.5f})."
                        ),
                        "feature_attributions": {
                            "reconstruction_error": res["max_reconstruction_error"],
                            "threshold": res["threshold"],
                            "model_type": scorer.model_type,
                        },
                        "evidence": {
                            "window_errors": res["window_errors"],
                            "window_count": res["window_count"],
                        },
                        "is_synthetic": is_synthetic,
                        "status": "NEW",
                    })
            except Exception:
                pass

        return all_events
