"""Matplotlib-based visualization generators — returns base64 PNG strings."""
from __future__ import annotations
import base64
import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import correlate2d
from utils.image_io import get_luminance

_DARK_BG = "#12151f"
_TEXT_COLOR = "#e8eaf6"
_MUTED_COLOR = "#8892a4"
_ACCENT = "#4f8ef7"
_GREEN = "#3ecf8e"
_RED = "#f45b5b"

plt.rcParams.update({
    "figure.facecolor": _DARK_BG,
    "axes.facecolor": _DARK_BG,
    "axes.edgecolor": "#2a2d3e",
    "axes.labelcolor": _TEXT_COLOR,
    "xtick.color": _MUTED_COLOR,
    "ytick.color": _MUTED_COLOR,
    "text.color": _TEXT_COLOR,
    "grid.color": "#2a2d3e",
    "grid.alpha": 0.5,
})


def _fig_to_b64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=96, bbox_inches="tight", facecolor=_DARK_BG)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_histogram(image: np.ndarray, title: str = "Pixel Intensity Histogram") -> str:
    """256-bin histogram with mean/sigma vertical lines."""
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=96)
    ax.set_facecolor(_DARK_BG)
    bins = np.linspace(0, 1, 257)

    if image.shape[2] == 1:
        data = image[:, :, 0].ravel()
        hist, _ = np.histogram(data, bins=bins)
        ax.fill_between(bins[:-1], hist, alpha=0.7, color=_ACCENT, step="post", label="Gray")
        mu, sigma = data.mean(), data.std()
    else:
        colors = [_RED, _GREEN, _ACCENT]
        names = ["Red", "Green", "Blue"]
        for c, (col, name) in enumerate(zip(colors, names)):
            data_c = image[:, :, c].ravel()
            hist, _ = np.histogram(data_c, bins=bins)
            ax.fill_between(bins[:-1], hist, alpha=0.5, color=col, step="post", label=name)
        lum = get_luminance(image).ravel()
        mu, sigma = lum.mean(), lum.std()

    ymax = ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1
    ax.axvline(mu, color="white", linewidth=1.2, linestyle="--", label=f"μ={mu:.3f}")
    ax.axvline(mu - sigma, color=_MUTED_COLOR, linewidth=0.8, linestyle=":", label=f"μ±σ")
    ax.axvline(mu + sigma, color=_MUTED_COLOR, linewidth=0.8, linestyle=":")
    ax.set_xlabel("Pixel Intensity", fontsize=9)
    ax.set_ylabel("Frequency", fontsize=9)
    ax.set_title(title, fontsize=10, pad=8)
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _fig_to_b64(fig)


def generate_correlation_map(image: np.ndarray) -> str:
    """2D normalized autocorrelation heatmap of luminance, cropped to center 64×64."""
    lum = get_luminance(image)
    zm = lum - lum.mean()
    corr = correlate2d(zm, zm, mode="same")
    # Normalize
    corr /= (corr.max() + 1e-12)

    h, w = corr.shape
    ch, cw = h // 2, w // 2
    half = 32
    crop = corr[
        max(0, ch - half): ch + half,
        max(0, cw - half): cw + half,
    ]

    fig, ax = plt.subplots(figsize=(5, 4.5), dpi=96)
    im = ax.imshow(crop, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Normalized Correlation")
    ax.set_title("2D Autocorrelation (center 64×64 crop)", fontsize=9)
    ax.set_xlabel("Δx lag", fontsize=8)
    ax.set_ylabel("Δy lag", fontsize=8)
    fig.tight_layout()
    return _fig_to_b64(fig)


def generate_snr_bar(snr_before: float, snr_after: float) -> str:
    """Horizontal bar chart comparing SNR before/after."""
    fig, ax = plt.subplots(figsize=(6, 2.5), dpi=96)
    labels = ["Before Enhancement", "After Enhancement"]
    values = [snr_before, snr_after]
    colors = [_MUTED_COLOR, _GREEN if snr_after >= snr_before else _RED]
    bars = ax.barh(labels, values, color=colors, height=0.4, edgecolor="#2a2d3e")
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val:.2f} dB", va="center", ha="left", fontsize=9, color=_TEXT_COLOR
        )
    ax.set_xlabel("SNR (dB)", fontsize=9)
    ax.set_title("Signal-to-Noise Ratio Comparison", fontsize=10)
    ax.set_xlim(0, max(snr_before, snr_after) * 1.25 + 1)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    return _fig_to_b64(fig)


def generate_convergence_plot(curve: list[float]) -> str:
    """MRF ICM convergence energy vs iteration."""
    fig, ax = plt.subplots(figsize=(6, 3), dpi=96)
    ax.plot(range(1, len(curve) + 1), curve, color=_ACCENT, linewidth=1.5, marker="o",
            markersize=3)
    ax.set_xlabel("Iteration", fontsize=9)
    ax.set_ylabel("Sum Squared Update", fontsize=9)
    ax.set_title("MRF ICM Convergence Curve", fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _fig_to_b64(fig)


def generate_wiener_gain_heatmap(gain_map: np.ndarray) -> str:
    """Per-pixel Wiener gain heatmap — values near 0 = noise-dominated, near 1 = signal."""
    fig, ax = plt.subplots(figsize=(5, 4), dpi=96)
    im = ax.imshow(gain_map, cmap="hot", vmin=0.0, vmax=1.0, aspect="auto")
    plt.colorbar(im, ax=ax, label="K (Wiener Gain)")
    ax.set_title("Wiener Gain Map  K = σ²_x / (σ²_x + σ²_n)", fontsize=9)
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.tight_layout()
    return _fig_to_b64(fig)


def get_histogram_data(image: np.ndarray, bins: int = 128) -> list[dict]:
    """Returns raw JSON data for the histogram (downsampled to 128 bins for frontend)."""
    edges = np.linspace(0, 1, bins + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    data_list = []
    
    if image.shape[2] == 1:
        hist, _ = np.histogram(image[:, :, 0].ravel(), bins=edges)
        for i in range(bins):
            data_list.append({
                "intensity": round(float(centers[i]), 3),
                "Gray": int(hist[i]),
            })
    else:
        hist_r, _ = np.histogram(image[:, :, 0].ravel(), bins=edges)
        hist_g, _ = np.histogram(image[:, :, 1].ravel(), bins=edges)
        hist_b, _ = np.histogram(image[:, :, 2].ravel(), bins=edges)
        for i in range(bins):
            data_list.append({
                "intensity": round(float(centers[i]), 3),
                "Red": int(hist_r[i]),
                "Green": int(hist_g[i]),
                "Blue": int(hist_b[i]),
            })
    return data_list


def get_snr_data(snr_before: float, snr_after: float) -> list[dict]:
    """Returns raw JSON data for the SNR comparison bar chart."""
    return [
        {"name": "Original", "snr": round(snr_before, 2)},
        {"name": "Enhanced", "snr": round(snr_after, 2)}
    ]


def get_convergence_data(curve: list[float]) -> list[dict]:
    """Returns raw JSON data for the convergence plot."""
    return [{"iteration": i + 1, "energy": round(val, 4)} for i, val in enumerate(curve)]
