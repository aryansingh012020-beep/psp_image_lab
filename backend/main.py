"""FastAPI application entry point with CORS and router mounting."""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import upload, process, noise
from services.session_manager import cleanup_expired_sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background session cleanup on startup."""
    task = asyncio.create_task(cleanup_expired_sessions())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Image Cleaning System API",
    version="1.0.0",
    description="Intelligent image cleaning using PSP theory — Bayesian MAP, MRF, and stochastic filters.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(noise.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
