import torch
from backend.ml.models.tcn_autoencoder import TemporalConvAutoencoder
from backend.ml.models.trajectory_transformer import TrajectoryTransformer


def test_tcn_autoencoder_forward():
    model = TemporalConvAutoencoder(in_features=7, hidden_dim=16, latent_dim=8)
    batch_size = 4
    seq_len = 16
    x = torch.randn(batch_size, seq_len, 7)
    recon, latent = model(x)

    assert recon.shape == (batch_size, seq_len, 7)
    assert latent.shape == (batch_size, seq_len, 8)

    errors = model.compute_reconstruction_error(x)
    assert errors.shape == (batch_size,)
    assert (errors >= 0).all()


def test_trajectory_transformer_forward():
    model = TrajectoryTransformer(in_features=7, d_model=16, nhead=2, num_layers=1)
    batch_size = 2
    seq_len = 12
    x = torch.randn(batch_size, seq_len, 7)
    recon, latent = model(x)

    assert recon.shape == (batch_size, seq_len, 7)
    assert latent.shape == (batch_size, seq_len, 16)
