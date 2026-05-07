"""Bayesian MAP estimation for image denoising (Wiener filter derivation)."""
from __future__ import annotations
import base64
import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter


def _wiener_gain_to_base64(gain_map: np.ndarray) -> str:
    """Render Wiener gain map as a heatmap and return base64 PNG."""
    fig, ax = plt.subplots(figsize=(5, 4), dpi=96)
    im = ax.imshow(gain_map, cmap="hot", vmin=0.0, vmax=1.0, aspect="auto")
    plt.colorbar(im, ax=ax, label="Wiener Gain K")
    ax.set_title("Wiener Gain Map (K = σ²_x / (σ²_x + σ²_n))", fontsize=9)
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=96, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def apply_bayesian_map(
    image: np.ndarray,
    noise_variance: float,
) -> tuple[np.ndarray, dict]:
    """
    Bayesian MAP denoising via pixelwise Wiener filter.

    Model:  y = x + n,  n ~ N(0, σ_n²)
    Prior:  p(x) = N(μ_x, σ_x²)  (estimated locally from 5×5 window)
    MAP:    x̂ = μ_x + K*(y - μ_x),  K = σ_x² / (σ_x² + σ_n²)

    Args:
        image: float32 ndarray (H, W, C) in [0, 1]
        noise_variance: σ_n²

    Returns:
        (denoised_image, stats_dict)
    """
    sigma_n2 = float(noise_variance)
    if sigma_n2 <= 0:
        sigma_n2 = 1e-6

    result = np.zeros_like(image)
    gain_maps = []

    for c in range(image.shape[2]):
        y = image[:, :, c].astype(np.float64)

        # Local mean and variance in 5×5 window
        mu_x = uniform_filter(y, size=5, mode="reflect")
        y2_local = uniform_filter(y ** 2, size=5, mode="reflect")
        sigma_x2 = np.maximum(y2_local - mu_x ** 2, 0.0)  # clamp negative (numerical)

        # Wiener gain
        K = sigma_x2 / (sigma_x2 + sigma_n2)
        gain_maps.append(K.astype(np.float32))

        # MAP estimate
        x_hat = mu_x + K * (y - mu_x)
        result[:, :, c] = np.clip(x_hat, 0.0, 1.0).astype(np.float32)

    # Average gain map across channels for visualization
    mean_gain_map = np.mean(np.stack(gain_maps, axis=0), axis=0)
    mean_posterior_var = float(
        np.mean(np.stack([uniform_filter(image[:, :, c].astype(np.float64) ** 2, size=5) -
                          uniform_filter(image[:, :, c].astype(np.float64), size=5) ** 2
                          for c in range(image.shape[2])]))
    )

    wiener_gain_b64 = _wiener_gain_to_base64(mean_gain_map)

    stats = {
        "noise_variance_used": sigma_n2,
        "mean_posterior_variance": mean_posterior_var,
        "wiener_gain_map_base64": wiener_gain_b64,
    }

    return result, stats
