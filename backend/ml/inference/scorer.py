from typing import List, Dict, Any, Optional
import numpy as np
import torch

from backend.ml.models.tcn_autoencoder import TemporalConvAutoencoder
from backend.ml.models.trajectory_transformer import TrajectoryTransformer
from backend.ml.training.dataset import TrajectoryWindowDataset
from backend.ml.registry.model_store import ModelArtifactStore


class TrajectorySequenceScorer:
    def __init__(self, model_id: str, device: str = "cpu"):
        self.model_id = model_id
        self.device = torch.device(device)
        self.store = ModelArtifactStore()
        self.metadata = self.store.load_metadata(model_id)
        if not self.metadata:
            raise ValueError(f"Model metadata not found for model_id {model_id}")

        self.model_type = self.metadata.get("model_type", "TCN_AUTOENCODER")
        self.seq_len = self.metadata.get("seq_len", 16)
        self.threshold = self.metadata.get("validation_metrics", {}).get("anomaly_threshold", 0.05)

        if self.model_type == "TRAJECTORY_TRANSFORMER":
            self.model = TrajectoryTransformer(in_features=7, d_model=32, nhead=4, num_layers=2)
        else:
            self.model = TemporalConvAutoencoder(in_features=7, hidden_dim=32, latent_dim=16)

        self.model.to(self.device)
        loaded = self.store.load_weights(model_id, self.model)
        if not loaded:
            raise ValueError(f"Model weights not found for model_id {model_id}")

    def score_trajectory(self, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs sliding-window inference across the trajectory.
        Returns overall anomaly score, window errors, and detected anomalous segments.
        """
        if len(points) < self.seq_len:
            return {
                "max_reconstruction_error": 0.0,
                "mean_reconstruction_error": 0.0,
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "window_errors": [],
            }

        dataset = TrajectoryWindowDataset([points], seq_len=self.seq_len, stride=1)
        if len(dataset) == 0:
            return {
                "max_reconstruction_error": 0.0,
                "mean_reconstruction_error": 0.0,
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "window_errors": [],
            }

        windows_tensor = torch.stack([dataset[i] for i in range(len(dataset))]).to(self.device)

        self.model.eval()
        with torch.no_grad():
            recon, _ = self.model(windows_tensor)
            mse_per_window = torch.mean((windows_tensor - recon) ** 2, dim=(1, 2)).cpu().numpy()

        max_err = float(np.max(mse_per_window))
        mean_err = float(np.mean(mse_per_window))

        # Normalized anomaly score relative to learned threshold
        norm_score = min(1.0, max(0.0, (max_err / (self.threshold * 2.5 + 1e-6))))
        is_anomalous = bool(max_err > self.threshold)

        return {
            "max_reconstruction_error": round(max_err, 6),
            "mean_reconstruction_error": round(mean_err, 6),
            "threshold": round(self.threshold, 6),
            "anomaly_score": round(norm_score, 3),
            "is_anomalous": is_anomalous,
            "window_count": len(mse_per_window),
            "window_errors": [round(float(e), 5) for e in mse_per_window[:50]],  # sample for UI
        }
