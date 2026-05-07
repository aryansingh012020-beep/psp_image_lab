import numpy as np
import cv2
import traceback
import sys

from services.filters import (
    apply_gaussian_filter,
    apply_median_filter,
    apply_bilateral_filter,
    apply_histogram_equalization,
)
from services.bayesian_estimator import apply_bayesian_map
from services.markov_field import apply_mrf
from services.noise_detector import classify_noise

print("Generating test image...")
# Create a 3-channel noisy image (H, W, C) float32 in [0, 1]
img = np.ones((100, 100, 3), dtype=np.float32) * 0.5
noise = np.random.normal(0, 0.1, img.shape).astype(np.float32)
img = np.clip(img + noise, 0.0, 1.0)

print(f"Original image shape: {img.shape}, dtype: {img.dtype}")

def run_step(name, func, *args, **kwargs):
    print(f"--- Running {name} ---")
    try:
        res = func(img, *args, **kwargs)
        if isinstance(res, tuple):
            if hasattr(res[0], 'shape'):
                print(f"Success! Output shape: {res[0].shape}, error: {res[1]}")
            else:
                print(f"Success! Returns tuple of len {len(res)}")
        elif isinstance(res, dict):
            print(f"Success! Output dict keys: {list(res.keys())}")
        else:
            print(f"Success! Output shape: {res.shape}")
    except Exception as e:
        print(f"FAILED: {e}")
        traceback.print_exc()

run_step("Noise Analysis", classify_noise)
run_step("Gaussian Filter", apply_gaussian_filter, 1.0)
run_step("Median Filter", apply_median_filter, 3)
run_step("Bilateral Filter", apply_bilateral_filter, 9, 75.0, 75.0)
run_step("Histogram Equalization", apply_histogram_equalization)
run_step("Bayesian MAP", apply_bayesian_map, 0.01)
run_step("MRF ICM", apply_mrf, 0.01, 1.0, 10)

print("Done.")
