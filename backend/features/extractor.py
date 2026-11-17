from typing import List, Dict, Any
import numpy as np
from backend.features.movement import compute_movement_features
from backend.features.spatial import compute_spatial_features
from backend.features.temporal import compute_temporal_features


class TrajectoryFeatureExtractor:
    FEATURE_NAMES = [
        "speed_mean",
        "speed_std",
        "speed_max",
        "speed_p95",
        "acceleration_mean",
        "acceleration_std",
        "turn_rate_mean",
        "turn_rate_max",
        "straightness_ratio",
        "stop_ratio",
        "total_distance_nm",
        "centroid_lat",
        "centroid_lon",
        "bbox_area_deg2",
        "radius_of_gyration_nm",
        "duration_hours",
        "sampling_interval_mean_sec",
        "sampling_interval_std_sec",
        "start_hour",
        "day_of_week",
    ]

    def extract_features(self, points: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extracts complete named dictionary of spatial-temporal trajectory features."""
        mov = compute_movement_features(points)
        spat = compute_spatial_features(points)
        temp = compute_temporal_features(points)

        features = {}
        features.update(mov)
        features.update(spat)
        features.update(temp)
        return features

    def extract_feature_vector(self, points: List[Dict[str, Any]]) -> np.ndarray:
        """Extracts fixed-length 1D numpy array aligned with FEATURE_NAMES."""
        feats = self.extract_features(points)
        return np.array([float(feats.get(name, 0.0)) for name in self.FEATURE_NAMES], dtype=np.float32)
