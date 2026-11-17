# Model Training & Sequence Learning

The platform implements PyTorch deep sequence models to learn normal vessel trajectory representations and flag sequence anomalies based on reconstruction error.

---

## 1. Temporal Convolutional Autoencoder (TCN Autoencoder)

- **Architecture:** 1D Causal Dilated Convolutions with residual blocks.
- **Why Causal & Dilated?** Left-padded causal convolutions strictly prevent future-data leakage in temporal sequence modeling. Exponential dilations ($d=1, 2$) expand the receptive field to capture long-range route patterns without pooling or losing temporal resolution.
- **Bottleneck:** Encodes 7 kinematic input features ($\text{lat}_{\text{norm}}, \text{lon}_{\text{norm}}, \text{sog}_{\text{norm}}, \sin(\text{cog}), \cos(\text{cog}), \text{rot}, a$) into a compressed latent representation ($d_{\text{latent}}=16$).
- **Reconstruction Loss:**
  $$\mathcal{L}_{\text{MSE}} = \frac{1}{T \cdot F} \sum_{t=1}^{T} \sum_{f=1}^{F} (x_{t,f} - \hat{x}_{t,f})^2$$
- **Anomaly Scoring:** An empirical threshold is calibrated from the 95th percentile reconstruction error on validation sequences. Sequences with high reconstruction loss represent unlearned, abnormal movement dynamics.

---

## 2. Comparative Trajectory Transformer

- **Architecture:** Multi-head self-attention encoder with sinusoidal positional encodings.
- **Purpose:** Comparative benchmark against the TCN architecture on trajectory window reconstruction.
- **Hyperparameters:** $d_{\text{model}}=32$, 4 attention heads, 2 encoder layers, feed-forward dimension 64.

---

## 3. Training Script & Model Registry

```bash
# Train the TCN Autoencoder
python scripts/train_model.py TCN_AUTOENCODER

# Train the comparative Transformer
python scripts/train_model.py TRAJECTORY_TRANSFORMER
```

All trained checkpoints, hyperparameters, and loss histories are persisted to `data/models/{model_id}/` and registered in the database for reproducible inference.
