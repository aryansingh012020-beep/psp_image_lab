"""Image I/O helpers — Base64 encode/decode, format normalization."""
from __future__ import annotations
import base64
import io
import numpy as np
import cv2
from PIL import Image


def pil_to_float32(pil_img: Image.Image) -> np.ndarray:
    """Convert a PIL Image to a float32 numpy array normalized to [0, 1]."""
    arr = np.array(pil_img, dtype=np.float32)
    # Ensure we have channel-last format
    if arr.ndim == 2:
        arr = arr[:, :, np.newaxis]  # (H, W, 1)
    # Normalize to [0, 1]
    arr = arr / 255.0
    return arr


def float32_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Convert a float32 array in [0, 1] to uint8 [0, 255]."""
    clipped = np.clip(arr, 0.0, 1.0)
    return (clipped * 255.0).astype(np.uint8)


def ndarray_to_base64_png(arr: np.ndarray) -> str:
    """Encode a float32 numpy array (H,W,C) or (H,W,1) as a base64 PNG string."""
    uint8 = float32_to_uint8(arr)
    if uint8.shape[2] == 1:
        uint8 = uint8[:, :, 0]  # grayscale
    success, buf = cv2.imencode(".png", uint8 if uint8.ndim == 2 else cv2.cvtColor(uint8, cv2.COLOR_RGB2BGR))
    if not success:
        raise RuntimeError("Failed to encode image to PNG")
    return base64.b64encode(buf).decode("utf-8")


def base64_to_ndarray(b64: str) -> np.ndarray:
    """Decode a base64-encoded PNG/JPEG back to a float32 numpy array (H,W,C)."""
    raw = base64.b64decode(b64)
    buf = np.frombuffer(raw, dtype=np.uint8)
    bgr = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    if bgr is None:
        raise ValueError("Failed to decode base64 image data")
    if bgr.ndim == 2:
        bgr = bgr[:, :, np.newaxis]
    elif bgr.shape[2] == 3:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    elif bgr.shape[2] == 4:
        bgr = cv2.cvtColor(bgr, cv2.COLOR_BGRA2RGBA)
    return bgr.astype(np.float32) / 255.0


def get_luminance(arr: np.ndarray) -> np.ndarray:
    """Return luminance (Y) channel as (H, W) float32 array."""
    if arr.shape[2] == 1:
        return arr[:, :, 0]
    # BT.601 luma weights
    return (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.float32)
