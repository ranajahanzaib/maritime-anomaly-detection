import uuid
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from backend.detection.base import BaseDetector
from backend.features.extractor import TrajectoryFeatureExtractor


class TrajectoryIsolationForestDetector(BaseDetector):
    def __init__(self, contamination: float = 0.05, n_estimators: int = 100):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.extractor = TrajectoryFeatureExtractor()
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42,
        )
        self.is_fitted = False

    @property
    def detector_id(self) -> str:
        return "ML_ISOLATION_FOREST"

    @property
    def detector_version(self) -> str:
        return "1.0.0"

    def fit(self, list_of_points: List[List[Dict[str, Any]]]):
        """Fits Isolation Forest on a corpus of trajectory windows."""
        vectors = []
        for pts in list_of_points:
            if len(pts) >= 5:
                vectors.append(self.extractor.extract_feature_vector(pts))
        if len(vectors) >= 10:
            X = np.array(vectors)
            self.model.fit(X)
            self.is_fitted = True

    def detect(
        self,
        mmsi: int,
        points: List[Dict[str, Any]],
        vessel_type: str = "Cargo",
        is_synthetic: bool = False,
    ) -> List[Dict[str, Any]]:
        events = []
        if len(points) < 5 or not self.is_fitted:
            return events

        vec = self.extractor.extract_feature_vector(points).reshape(1, -1)
        # IsolationForest: negative scores are outliers
        raw_score = float(self.model.decision_function(vec)[0])
        pred = int(self.model.predict(vec)[0])  # -1 for anomaly, 1 for inlier

        if pred == -1 or raw_score < -0.05:
            # Normalize anomaly score to [0, 1] range
            norm_score = min(1.0, max(0.0, 0.5 - raw_score * 2.5))
            severity = "HIGH" if norm_score > 0.8 else "MEDIUM"

            def to_dt(t):
                if isinstance(t, str):
                    return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
                return t

            t_start = to_dt(points[0]["timestamp"])
            t_end = to_dt(points[-1]["timestamp"])
            center_lat = float(points[len(points) // 2]["latitude"])
            center_lon = float(points[len(points) // 2]["longitude"])

            feats = self.extractor.extract_features(points)

            explanation = (
                f"Multi-dimensional trajectory anomaly detected by Isolation Forest (score: {norm_score:.2f}). "
                f"Trajectory features (speed={feats['speed_mean']:.1f} kts, turn_rate={feats['turn_rate_mean']:.1f} dpm, "
                f"straightness={feats['straightness_ratio']:.2f}) lie in low-density isolation space."
            )

            events.append({
                "id": f"evt_if_{mmsi}_{uuid.uuid4().hex[:8]}",
                "category": "PEER_GROUP_DEVIATION",
                "primary_mmsi": mmsi,
                "secondary_mmsi": None,
                "detector_id": self.detector_id,
                "detector_version": self.detector_version,
                "deviation_score": round(norm_score, 3),
                "severity": severity,
                "confidence": 0.78,
                "start_time": t_start,
                "end_time": t_end,
                "duration_seconds": (t_end - t_start).total_seconds(),
                "latitude": center_lat,
                "longitude": center_lon,
                "bbox_geojson": {
                    "type": "Point",
                    "coordinates": [center_lon, center_lat],
                },
                "contextual_state": "POTENTIALLY_RELEVANT",
                "contextual_explanation": "Unsupervised feature space anomaly identified via Isolation Forest.",
                "explanation": explanation,
                "feature_attributions": {
                    "raw_decision_score": round(raw_score, 4),
                    "speed_mean": feats["speed_mean"],
                    "turn_rate_mean": feats["turn_rate_mean"],
                    "straightness_ratio": feats["straightness_ratio"],
                },
                "evidence": {
                    "feature_vector_summary": feats,
                },
                "is_synthetic": is_synthetic,
                "status": "NEW",
            })

        return events
