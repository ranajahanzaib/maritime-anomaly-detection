import math
from typing import List, Dict, Any, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset
from backend.trajectories.kinematics import derive_point_kinematics


class TrajectoryWindowDataset(Dataset):
    """
    Slices vessel trajectory observations into sliding sequence windows
    of length `seq_len` for temporal model training and inference.
    """
    def __init__(
        self,
        list_of_tracks: List[List[Dict[str, Any]]],
        seq_len: int = 16,
        stride: int = 4,
    ):
        self.seq_len = seq_len
        self.windows = []

        for track in list_of_tracks:
            if len(track) < seq_len:
                continue

            # Compute normalized kinematic steps
            features = []
            for i in range(len(track)):
                pt = track[i]
                lat = float(pt["latitude"])
                lon = float(pt["longitude"])
                sog = float(pt.get("sog", 0.0))
                cog = float(pt.get("cog", 0.0))

                cog_rad = math.radians(cog)
                sin_cog = math.sin(cog_rad)
                cos_cog = math.cos(cog_rad)

                turn_rate = 0.0
                accel = 0.0
                if i > 0:
                    k = derive_point_kinematics(track[i - 1], pt)
                    turn_rate = k["turn_rate_deg_per_min"] / 100.0  # scaled
                    accel = k["acceleration_ms2"]

                feat_vec = [
                    lat,
                    lon,
                    sog / 25.0,  # normalized by typical 25 kts
                    sin_cog,
                    cos_cog,
                    turn_rate,
                    accel,
                ]
                features.append(feat_vec)

            # Slide window
            feat_arr = np.array(features, dtype=np.float32)
            for start in range(0, len(feat_arr) - seq_len + 1, stride):
                window = feat_arr[start : start + seq_len]
                # Center coordinates relative to window start for translation invariance
                window_centered = window.copy()
                window_centered[:, 0] = (window_centered[:, 0] - window_centered[0, 0]) * 60.0  # degrees to approx NM
                window_centered[:, 1] = (window_centered[:, 1] - window_centered[0, 1]) * 60.0 * math.cos(math.radians(lat))
                self.windows.append(window_centered)

        if not self.windows:
            # Fallback dummy window if no trajectories were long enough
            self.windows = [np.zeros((seq_len, 7), dtype=np.float32)]

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return torch.tensor(self.windows[idx], dtype=torch.float32)
