"""Noise detection and classification service using PSP-grounded estimators."""
from __future__ import annotations
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
from utils.image_io import get_luminance


class NoiseReport:
    def __init__(self, noise_types: list[str], estimated_sigma: float,
                 sp_density: float, laplacian_variance: float, recommendation: str):
        self.noise_types = noise_types
        self.estimated_sigma = estimated_sigma
        self.sp_density = sp_density
        self.laplacian_variance = laplacian_variance
        self.recommendation = recommendation

    def to_dict(self) -> dict:
        return {
            "noise_types": self.noise_types,
            "estimated_sigma": float(self.estimated_sigma),
            "sp_density": float(self.sp_density),
            "laplacian_variance": float(self.laplacian_variance),
            "recommendation": self.recommendation,
        }


def classify_noise(image: np.ndarray) -> NoiseReport:
    """
    Classify the noise in a float32 image array in [0, 1].
    Returns a NoiseReport with type flags, sigma estimate, and recommendation.
    """
    lum = get_luminance(image)  # (H, W) float32

    # Convert to uint8 for Laplacian
    lum_uint8 = (lum * 255).astype(np.uint8)
    laplacian = cv2.Laplacian(lum_uint8, cv2.CV_64F)
    lap_var = float(laplacian.var())

    # Gaussian noise estimation via MAD estimator on HF residual
    blurred = gaussian_filter(lum, sigma=1.5)
    hf_residual = lum - blurred
    sigma_hat = float(np.median(np.abs(hf_residual)) / 0.6745)

    # Salt-and-pepper detection
    total_pixels = lum.size
    sp_count = int(np.sum((lum < 0.02) | (lum > 0.98)))
    sp_density = sp_count / total_pixels

    noise_types: list[str] = []

    # Gaussian noise flag
    if sigma_hat > 0.05:
        noise_types.append("Gaussian")

    # Salt-and-pepper flag
    if sp_density > 0.005:
        noise_types.append("Salt & Pepper")

    # Blur flag (Laplacian variance in uint8 scale)
    if lap_var < 50.0:
        noise_types.append("Blur")

    # Build recommendation
    parts: list[str] = []
    if "Salt & Pepper" in noise_types:
        parts.append("Median Filter (optimal for impulsive noise)")
    if "Gaussian" in noise_types:
        parts.append("Gaussian/Bilateral Filter")
        parts.append("Bayesian MAP Denoising")
    if "Blur" in noise_types:
        parts.append("Histogram Equalization (contrast enhancement)")
    if not parts:
        parts.append("Image appears clean — Histogram Equalization may improve contrast")
    recommendation = " → ".join(parts)

    return NoiseReport(
        noise_types=noise_types if noise_types else ["None Detected"],
        estimated_sigma=sigma_hat,
        sp_density=sp_density,
        laplacian_variance=lap_var,
        recommendation=recommendation,
    )
