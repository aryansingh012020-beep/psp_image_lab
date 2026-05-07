import urllib.request
import json
import numpy as np
import cv2
import base64
import os

# 1. Create a noisy image
img = np.ones((100, 100, 3), dtype=np.uint8) * 128
noise = np.random.normal(0, 50, img.shape).astype(np.int16)
img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
cv2.imwrite("test_noisy.png", img)

# 2. Upload
print("Uploading...")
boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
with open("test_noisy.png", "rb") as f:
    file_content = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="image"; filename="test_noisy.png"\r\n'
    f'Content-Type: image/png\r\n\r\n'
).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req_up = urllib.request.Request("http://localhost:8000/api/upload", data=body, method="POST")
req_up.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

try:
    with urllib.request.urlopen(req_up) as r_up:
        resp_data = json.loads(r_up.read().decode('utf-8'))
        session_id = resp_data["session_id"]
        print("Session ID:", session_id)
except Exception as e:
    print("Upload failed:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
    exit(1)

# 3. Process
print("Processing...")
req_data = {
    "steps": ["noise_analysis", "gaussian_filter", "median_filter", "bilateral_filter", "histogram_equalization", "bayesian_map", "mrf_prior"],
    "params": {}
}
req_proc = urllib.request.Request(f"http://localhost:8000/api/process/{session_id}", data=json.dumps(req_data).encode('utf-8'), method="POST")
req_proc.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req_proc) as r_proc:
        data = json.loads(r_proc.read().decode('utf-8'))
        print("Steps completed:", [s["step_id"] for s in data["steps"]])
        for s in data["steps"]:
            if s.get("error"):
                print(f"Error in {s['step_id']}: {s['error']}")
except Exception as e:
    print("Process failed:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
