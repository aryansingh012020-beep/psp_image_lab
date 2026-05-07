"""POST /api/upload — image ingestion, validation, and session creation."""
from __future__ import annotations
import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
import numpy as np

from services import session_manager
from utils.image_io import pil_to_float32, ndarray_to_base64_png
from models.schemas import UploadResponse, ImageMetadata

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/tiff", "image/bmp", "image/webp",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=UploadResponse)
async def upload_image(image: UploadFile = File(...)) -> UploadResponse:
    # ── Content-type validation ──────────────────────────────────────────────
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type '{image.content_type}'. "
                   "Accepted: JPEG, PNG, TIFF, BMP, WEBP.",
        )

    raw_bytes = await image.read()

    # ── Size validation ──────────────────────────────────────────────────────
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw_bytes) / 1024:.1f} KB). Max 10 MB.",
        )

    # ── Decode with PIL ──────────────────────────────────────────────────────
    try:
        pil_img = Image.open(io.BytesIO(raw_bytes))
        pil_img.load()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}")

    # ── Format / channel validation ──────────────────────────────────────────
    fmt = pil_img.format or "UNKNOWN"
    mode = pil_img.mode

    # Normalize to RGB or L
    if mode not in ("RGB", "L"):
        if mode == "RGBA":
            pil_img = pil_img.convert("RGB")
        elif mode in ("P", "LA", "PA"):
            pil_img = pil_img.convert("RGB")
        elif mode in ("I", "F"):
            pil_img = pil_img.convert("L")
        else:
            pil_img = pil_img.convert("RGB")

    channels = 1 if pil_img.mode == "L" else 3
    width, height = pil_img.size

    # ── Convert to float32 ───────────────────────────────────────────────────
    arr = pil_to_float32(pil_img)  # (H, W, C) in [0, 1]

    # ── Create session ───────────────────────────────────────────────────────
    session_id = session_manager.create_session(arr)

    # ── Encode back to base64 PNG for response ───────────────────────────────
    image_b64 = ndarray_to_base64_png(arr)

    return UploadResponse(
        session_id=session_id,
        image_base64=image_b64,
        metadata=ImageMetadata(
            width=width,
            height=height,
            channels=channels,
            format=fmt,
            file_size_kb=len(raw_bytes) / 1024.0,
        ),
    )
