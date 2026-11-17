import time
from typing import Dict, Any, List, Optional
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

from backend.ml.models.tcn_autoencoder import TemporalConvAutoencoder
from backend.ml.models.trajectory_transformer import TrajectoryTransformer
from backend.ml.training.dataset import TrajectoryWindowDataset
from backend.ml.registry.model_store import ModelArtifactStore


class TrajectoryModelTrainer:
    def __init__(
        self,
        model_type: str = "TCN_AUTOENCODER",
        seq_len: int = 16,
        batch_size: int = 32,
        epochs: int = 10,
        learning_rate: float = 1e-3,
        device: str = "cpu",
    ):
        self.model_type = model_type.upper()
        self.seq_len = seq_len
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = learning_rate
        self.device = torch.device(device)
        self.store = ModelArtifactStore()

    def build_model(self) -> nn.Module:
        if self.model_type == "TRAJECTORY_TRANSFORMER":
            return TrajectoryTransformer(in_features=7, d_model=32, nhead=4, num_layers=2)
        else:
            return TemporalConvAutoencoder(in_features=7, hidden_dim=32, latent_dim=16)

    def train(
        self,
        model_id: str,
        tracks: List[List[Dict[str, Any]]],
        dataset_id: Optional[str] = None,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes actual training loop on trajectory windows, recording epoch losses and metrics.
        """
        full_ds = TrajectoryWindowDataset(tracks, seq_len=self.seq_len, stride=2)
        total_samples = len(full_ds)

        if total_samples < 4:
            raise ValueError(f"Insufficient trajectory data for training (only {total_samples} windows).")

        val_size = max(1, int(total_samples * 0.2))
        train_size = total_samples - val_size
        train_ds, val_ds = random_split(full_ds, [train_size, val_size])

        train_loader = DataLoader(train_ds, batch_size=min(self.batch_size, train_size), shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=min(self.batch_size, val_size), shuffle=False)

        model = self.build_model().to(self.device)
        optimizer = torch.optim.Adam(model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        history = []
        best_val_loss = float("inf")

        for epoch in range(1, self.epochs + 1):
            model.train()
            train_loss = 0.0
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                recon, _ = model(batch)
                loss = criterion(recon, batch)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * batch.size(0)

            train_loss /= train_size

            # Validation
            model.eval()
            val_loss = 0.0
            val_errors = []
            with torch.no_grad():
                for batch in val_loader:
                    batch = batch.to(self.device)
                    recon, _ = model(batch)
                    loss = criterion(recon, batch)
                    val_loss += loss.item() * batch.size(0)
                    mse_per_sample = torch.mean((batch - recon) ** 2, dim=(1, 2))
                    val_errors.extend(mse_per_sample.cpu().numpy().tolist())

            val_loss /= val_size
            history.append({
                "epoch": epoch,
                "train_loss": round(train_loss, 6),
                "val_loss": round(val_loss, 6),
            })

            if progress_callback:
                progress_callback(epoch, self.epochs, train_loss, val_loss)

        # Compute empirical threshold (e.g. 95th percentile on validation)
        threshold = float(np.percentile(val_errors, 95)) if val_errors else 0.05

        validation_metrics = {
            "final_train_loss": round(train_loss, 6),
            "final_val_loss": round(val_loss, 6),
            "reconstruction_error_mean": round(float(np.mean(val_errors)), 6) if val_errors else 0.0,
            "reconstruction_error_p95": round(threshold, 6),
            "anomaly_threshold": round(threshold, 6),
            "total_windows": total_samples,
            "train_samples": train_size,
            "val_samples": val_size,
        }

        metadata = {
            "model_id": model_id,
            "model_type": self.model_type,
            "dataset_id": dataset_id,
            "seq_len": self.seq_len,
            "in_features": 7,
            "validation_metrics": validation_metrics,
            "training_history": history,
            "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        artifact_path = self.store.save_model(model_id, model, metadata)
        return {
            "model_id": model_id,
            "artifact_path": artifact_path,
            "validation_metrics": validation_metrics,
            "history": history,
        }
