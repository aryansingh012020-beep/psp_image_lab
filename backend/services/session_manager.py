"""Session manager — UUID lifecycle and temp file management with TTL cleanup."""
from __future__ import annotations
import asyncio
import tempfile
import shutil
import uuid
import time
import os
from pathlib import Path
from typing import Optional
import numpy as np

# In-memory registry: session_id -> {path, last_access, image}
_sessions: dict[str, dict] = {}
_SESSION_TTL_SECONDS = 1800  # 30 minutes
_CLEANUP_INTERVAL = 300       # check every 5 minutes


def create_session(image: np.ndarray) -> str:
    """Create a new session, store the image, return session_id."""
    session_id = str(uuid.uuid4())
    tmpdir = tempfile.mkdtemp(prefix=f"ics_{session_id[:8]}_")
    _sessions[session_id] = {
        "tmpdir": tmpdir,
        "image": image,
        "last_access": time.time(),
    }
    return session_id


def get_session_image(session_id: str) -> Optional[np.ndarray]:
    """Retrieve the stored image for a session, or None if not found."""
    session = _sessions.get(session_id)
    if session is None:
        return None
    session["last_access"] = time.time()
    return session["image"]


def delete_session(session_id: str) -> None:
    """Explicitly delete a session and its temp files."""
    session = _sessions.pop(session_id, None)
    if session:
        shutil.rmtree(session["tmpdir"], ignore_errors=True)


async def cleanup_expired_sessions() -> None:
    """Background task: periodically remove sessions older than TTL."""
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL)
        now = time.time()
        expired = [sid for sid, data in _sessions.items()
                   if now - data["last_access"] > _SESSION_TTL_SECONDS]
        for sid in expired:
            delete_session(sid)
