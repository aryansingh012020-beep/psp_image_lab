"""Statistical analysis service — first/second-order statistics of random fields."""
from __future__ import annotations
import numpy as np
from scipy.stats import skew, kurtosis
from scipy.signal import correlate2d
from utils.image_io import get_luminance


def _safe_snr(mean: float, variance: float) -> tuple[float, float]:
    """Return (snr_linear, snr_db). Handles zero variance safely."""
    if variance <= 1e-12:
        return float("inf"), float("inf")
    snr_lin = (mean ** 2) / variance
    snr_db = 10.0 * np.log10(snr_lin) if snr_lin > 0 else float("-inf")
    return float(snr_lin), float(snr_db)


def _channel_stats(channel: np.ndarray) -> dict:
    """Compute all statistics for a single 2D float32 channel."""
    flat = channel.ravel().astype(np.float64)
    mu = float(flat.mean())
    var = float(flat.var())
    std = float(flat.std())
    skewness = float(skew(flat))
    kurt = float(kurtosis(flat, fisher=True))  # excess kurtosis

    # Entropy from histogram
    hist, _ = np.histogram(flat, bins=256, range=(0.0, 1.0))
    hist_prob = hist / hist.sum()
    hist_prob = hist_prob[hist_prob > 0]
    entropy = float(-np.sum(hist_prob * np.log2(hist_prob)))

    snr_lin, snr_db = _safe_snr(mu, var)

    # Autocorrelation at lags (1,0), (0,1), (1,1)
    zm = channel - mu  # zero-mean
    N = zm.size

    def _autocorr(dy: int, dx: int) -> float:
        if dy == 0 and dx == 0:
            return 1.0
        h, w = channel.shape
        if dy > 0:
            a, b = zm[:-dy, :], zm[dy:, :]
        else:
            a, b = zm, zm
        if dx > 0:
            a, b = a[:, :-dx], b[:, dx:]
        return float(np.sum(a * b) / N) / (var + 1e-12)

    ac10 = _autocorr(1, 0)
    ac01 = _autocorr(0, 1)
    ac11 = _autocorr(1, 1)

    return {
        "mean": mu,
        "variance": var,
        "std": std,
        "skewness": skewness,
        "kurtosis": kurt,
        "entropy": entropy,
        "snr_linear": snr_lin if np.isfinite(snr_lin) else 0.0,
        "snr_db": snr_db if np.isfinite(snr_db) else 0.0,
        "autocorr_lag10": ac10,
        "autocorr_lag01": ac01,
        "autocorr_lag11": ac11,
    }


def analyze(image: np.ndarray) -> dict:
    """
    Full statistical analysis of a float32 image (H, W, C).
    Returns a dict matching StatReport schema.
    """
    lum = get_luminance(image)
    overall = _channel_stats(lum)

    per_channel = []
    for c in range(image.shape[2]):
        per_channel.append(_channel_stats(image[:, :, c]))

    # 256-bin histogram on luminance
    hist, _ = np.histogram(lum.ravel(), bins=256, range=(0.0, 1.0))

    return {
        "overall": overall,
        "per_channel": per_channel,
        "histogram_data": hist.tolist(),
    }
