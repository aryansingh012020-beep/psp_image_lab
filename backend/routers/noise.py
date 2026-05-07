"""POST /api/noise/{session_id} — inject artificial Gaussian noise into the session image."""
from __future__ import annotations
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import session_manager
from utils.image_io import ndarray_to_base64_png

router = APIRouter()


class NoiseRequest(BaseModel):
    sigma: float = Field(default=0.08, ge=0.01, le=0.5, description="Gaussian noise std dev (0–1 scale)")
    noise_type: str = Field(default="gaussian", description="'gaussian' or 'salt_pepper'")
    sp_density: float = Field(default=0.05, ge=0.0, le=0.5, description="Salt & pepper density (0–1)")


class NoiseResponse(BaseModel):
    image_base64: str
    sigma_used: float
    noise_type: str


@router.post("/noise/{session_id}", response_model=NoiseResponse)
async def add_noise(session_id: str, req: NoiseRequest) -> NoiseResponse:
    """Inject artificial noise into the stored session image and update the session."""
    image = session_manager.get_session_image(session_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    noisy = image.copy().astype(np.float32)

    if req.noise_type == "gaussian":
        noise = np.random.normal(0.0, req.sigma, noisy.shape).astype(np.float32)
        noisy = np.clip(noisy + noise, 0.0, 1.0)

    elif req.noise_type == "salt_pepper":
        rng = np.random.default_rng()
        total = noisy.shape[0] * noisy.shape[1]
        n_sp = int(total * req.sp_density)
        # Salt
        coords_salt = (
            rng.integers(0, noisy.shape[0], n_sp // 2),
            rng.integers(0, noisy.shape[1], n_sp // 2),
        )
        noisy[coords_salt[0], coords_salt[1], :] = 1.0
        # Pepper
        coords_pepper = (
            rng.integers(0, noisy.shape[0], n_sp // 2),
            rng.integers(0, noisy.shape[1], n_sp // 2),
        )
        noisy[coords_pepper[0], coords_pepper[1], :] = 0.0

    elif req.noise_type == "both":
        # Gaussian layer
        noise = np.random.normal(0.0, req.sigma, noisy.shape).astype(np.float32)
        noisy = np.clip(noisy + noise, 0.0, 1.0)
        # Salt & pepper layer
        rng = np.random.default_rng()
        total = noisy.shape[0] * noisy.shape[1]
        n_sp = int(total * req.sp_density)
        coords_salt = (rng.integers(0, noisy.shape[0], n_sp // 2), rng.integers(0, noisy.shape[1], n_sp // 2))
        noisy[coords_salt[0], coords_salt[1], :] = 1.0
        coords_pepper = (rng.integers(0, noisy.shape[0], n_sp // 2), rng.integers(0, noisy.shape[1], n_sp // 2))
        noisy[coords_pepper[0], coords_pepper[1], :] = 0.0

    # Update the session image so the pipeline runs on the noisy version
    session_manager._sessions[session_id]["image"] = noisy

    return NoiseResponse(
        image_base64=ndarray_to_base64_png(noisy),
        sigma_used=req.sigma,
        noise_type=req.noise_type,
    )
