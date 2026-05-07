"""All image filtering algorithms — float32 in, float32 out."""
from __future__ import annotations
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter as scipy_gaussian


def apply_gaussian_filter(image: np.ndarray, sigma: float) -> np.ndarray:
    """
    Apply a Gaussian LTI filter to a float32 image.
    Uses scipy.ndimage.gaussian_filter per channel.
    PSP: LTI system — output PSD = |H(u,v)|^2 * S_in(u,v).
    """
    result = np.zeros_like(image)
    for c in range(image.shape[2]):
        result[:, :, c] = scipy_gaussian(image[:, :, c], sigma=sigma)
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def apply_median_filter(image: np.ndarray, kernel_size: int) -> np.ndarray:
    """
    Apply a median (order-statistic) filter.
    Optimal ML estimator under Laplacian noise model (S&P removal).
    Converts to uint8 for cv2.medianBlur, converts back to float32.
    """
    if kernel_size % 2 == 0:
        kernel_size += 1  # ensure odd

    uint8 = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    result = np.zeros_like(uint8)
    for c in range(uint8.shape[2]):
        result[:, :, c] = cv2.medianBlur(uint8[:, :, c], kernel_size)
    return (result.astype(np.float32) / 255.0)


def apply_bilateral_filter(
    image: np.ndarray,
    d: int,
    sigma_color: float,
    sigma_space: float,
) -> tuple[np.ndarray, str | None]:
    """
    Apply a bilateral filter (edge-preserving spatial-radiometric Gaussian weighting).
    Returns (filtered_image, error_message_or_None).
    Rejects images larger than 2000×2000.
    """
    h, w = image.shape[:2]
    if h > 2000 or w > 2000:
        return image, (
            f"Bilateral filter skipped: image ({w}×{h}) exceeds 2000×2000 limit. "
            "Resize the image and resubmit."
        )

    uint8 = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    result = np.zeros_like(uint8)
    for c in range(uint8.shape[2]):
        result[:, :, c] = cv2.bilateralFilter(
            uint8[:, :, c], d=d,
            sigmaColor=sigma_color,
            sigmaSpace=sigma_space,
        )
    return (result.astype(np.float32) / 255.0), None


def apply_histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    CDF-based intensity redistribution (histogram equalization).
    For grayscale: equalizeHist on the single channel.
    For RGB: convert to YCrCb, equalize Y only, convert back.
    Maximizes output entropy (information-theoretic).
    """
    uint8 = (np.clip(image, 0, 1) * 255).astype(np.uint8)

    if image.shape[2] == 1:
        equalized = cv2.equalizeHist(uint8[:, :, 0])
        result = equalized[:, :, np.newaxis].astype(np.float32) / 255.0
    else:
        # RGB → YCrCb
        ycrcb = cv2.cvtColor(uint8, cv2.COLOR_RGB2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        rgb_eq = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)
        result = rgb_eq.astype(np.float32) / 255.0

    return np.clip(result, 0.0, 1.0)
