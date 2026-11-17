import torch
import torch.nn as nn
from typing import Tuple


class ChausalConv1d(nn.Module):
    """1D Dilated Causal Convolution with left-padding to avoid future-data leakage."""
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3, dilation: int = 1):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(
            in_channels, out_channels, kernel_size=kernel_size, dilation=dilation, padding=self.padding
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv(x)
        if self.padding != 0:
            out = out[:, :, :-self.padding]
        return out


class ResidualTCNBlock(nn.Module):
    def __init__(self, channels: int, kernel_size: int = 3, dilation: int = 1, dropout: float = 0.1):
        super().__init__()
        self.conv1 = ChausalConv1d(channels, channels, kernel_size=kernel_size, dilation=dilation)
        self.relu1 = nn.ReLU()
        self.drop1 = nn.Dropout(dropout)
        
        self.conv2 = ChausalConv1d(channels, channels, kernel_size=kernel_size, dilation=dilation)
        self.relu2 = nn.ReLU()
        self.drop2 = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x
        out = self.drop1(self.relu1(self.conv1(x)))
        out = self.drop2(self.relu2(self.conv2(out)))
        return torch.relu(out + res)


class TemporalConvAutoencoder(nn.Module):
    """
    Temporal Convolutional Autoencoder for sequence reconstruction and anomaly scoring.
    Learns normal movement representations across trajectory windows.
    Reconstruction error (MSE) serves as an interpretable sequence anomaly score.
    """
    def __init__(
        self,
        in_features: int = 7,
        hidden_dim: int = 32,
        latent_dim: int = 16,
        kernel_size: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        # Encoder: in_features -> hidden_dim -> latent_dim with dilations
        self.enc_in = nn.Conv1d(in_features, hidden_dim, kernel_size=1)
        self.enc_block1 = ResidualTCNBlock(hidden_dim, kernel_size=kernel_size, dilation=1, dropout=dropout)
        self.enc_block2 = ResidualTCNBlock(hidden_dim, kernel_size=kernel_size, dilation=2, dropout=dropout)
        self.enc_bottleneck = nn.Conv1d(hidden_dim, latent_dim, kernel_size=1)

        # Decoder: latent_dim -> hidden_dim -> in_features
        self.dec_in = nn.Conv1d(latent_dim, hidden_dim, kernel_size=1)
        self.dec_block1 = ResidualTCNBlock(hidden_dim, kernel_size=kernel_size, dilation=2, dropout=dropout)
        self.dec_block2 = ResidualTCNBlock(hidden_dim, kernel_size=kernel_size, dilation=1, dropout=dropout)
        self.dec_out = nn.Conv1d(hidden_dim, in_features, kernel_size=1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        x: (batch_size, seq_len, in_features)
        Returns:
            reconstructed: (batch_size, seq_len, in_features)
            latent: (batch_size, seq_len, latent_dim)
        """
        # Transpose to (batch_size, in_features, seq_len)
        x_trans = x.transpose(1, 2)
        
        # Encoder
        h = torch.relu(self.enc_in(x_trans))
        h = self.enc_block1(h)
        h = self.enc_block2(h)
        latent = self.enc_bottleneck(h)

        # Decoder
        h_dec = torch.relu(self.dec_in(latent))
        h_dec = self.dec_block1(h_dec)
        h_dec = self.dec_block2(h_dec)
        recon = self.dec_out(h_dec)

        recon = recon.transpose(1, 2)
        latent_out = latent.transpose(1, 2)
        return recon, latent_out

    def compute_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Computes mean squared error per sequence window: (batch_size,)."""
        recon, _ = self.forward(x)
        mse = torch.mean((x - recon) ** 2, dim=(1, 2))
        return mse
