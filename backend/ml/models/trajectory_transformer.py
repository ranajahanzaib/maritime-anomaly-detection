import math
import torch
import torch.nn as nn
from typing import Tuple


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 500):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch_size, seq_len, d_model)
        seq_len = x.size(1)
        return x + self.pe[:, :seq_len]


class TrajectoryTransformer(nn.Module):
    """
    Compact Transformer Encoder model for trajectory representation and reconstruction.
    Uses multi-head self-attention over sequence timesteps.
    """
    def __init__(
        self,
        in_features: int = 7,
        d_model: int = 32,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 64,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.in_proj = nn.Linear(in_features, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.out_proj = nn.Linear(d_model, in_features)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # x: (batch_size, seq_len, in_features)
        h = self.in_proj(x)
        h = self.pos_encoder(h)
        latent = self.transformer_encoder(h)
        recon = self.out_proj(latent)
        return recon, latent

    def compute_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        recon, _ = self.forward(x)
        return torch.mean((x - recon) ** 2, dim=(1, 2))
