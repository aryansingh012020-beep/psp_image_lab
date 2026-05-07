import numpy as np
import cv2
from services.filters import apply_gaussian_filter, apply_median_filter

img = np.ones((100, 100, 3), dtype=np.float32) * 0.5
noise = np.random.normal(0, 0.1, img.shape).astype(np.float32)
img = np.clip(img + noise, 0.0, 1.0)

print("Original image mean:", img.mean())
print("Original image std:", img.std())

res_g = apply_gaussian_filter(img, 2.0)
print("Gaussian output mean:", res_g.mean())
print("Gaussian output std:", res_g.std())
print("Difference max:", np.abs(img - res_g).max())

res_m = apply_median_filter(img, 5)
print("Median output std:", res_m.std())
print("Difference max:", np.abs(img - res_m).max())
