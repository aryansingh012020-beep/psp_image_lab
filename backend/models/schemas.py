"""Pydantic v2 schemas for the Image Cleaning System API."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Upload ────────────────────────────────────────────────────────────────────

class ImageMetadata(BaseModel):
    width: int
    height: int
    channels: int
    format: str
    file_size_kb: float


class UploadResponse(BaseModel):
    session_id: str
    image_base64: str
    metadata: ImageMetadata


# ── Process Request ───────────────────────────────────────────────────────────

class StepParams(BaseModel):
    gaussian_sigma: float = Field(default=1.0, ge=0.5, le=5.0)
    median_kernel_size: int = Field(default=3, ge=3, le=11)
    bilateral_d: int = Field(default=9, ge=5, le=15)
    bilateral_sigma_color: float = Field(default=75.0, ge=1.0)
    bilateral_sigma_space: float = Field(default=75.0, ge=1.0)
    mrf_iterations: int = Field(default=10, ge=5, le=50)
    mrf_beta: float = Field(default=1.0, ge=0.0)
    bayesian_noise_var: Optional[float] = Field(default=None, ge=0.0)


VALID_STEPS = [
    "noise_analysis",
    "statistical_analysis",
    "gaussian_filter",
    "median_filter",
    "bilateral_filter",
    "histogram_equalization",
    "bayesian_map",
    "mrf_prior",
]


class ProcessRequest(BaseModel):
    steps: list[str] = Field(default_factory=lambda: VALID_STEPS.copy())
    params: StepParams = Field(default_factory=StepParams)


# ── Noise Report ──────────────────────────────────────────────────────────────

class NoiseReport(BaseModel):
    noise_types: list[str]
    estimated_sigma: float
    sp_density: float
    laplacian_variance: float
    recommendation: str


# ── Stat Report ───────────────────────────────────────────────────────────────

class ChannelStats(BaseModel):
    mean: float
    variance: float
    std: float
    skewness: float
    kurtosis: float
    entropy: float
    snr_linear: float
    snr_db: float
    autocorr_lag10: float
    autocorr_lag01: float
    autocorr_lag11: float


class StatReport(BaseModel):
    overall: ChannelStats
    per_channel: list[ChannelStats]
    histogram_data: list[int]  # 256 bins, flat


# ── Pipeline Result ───────────────────────────────────────────────────────────

class StepChartsData(BaseModel):
    histogram_data: Optional[list[dict[str, Any]]] = None
    snr_data: Optional[list[dict[str, Any]]] = None
    convergence_data: Optional[list[dict[str, Any]]] = None


class StepCharts(BaseModel):
    histogram: Optional[str] = None
    correlation_map: Optional[str] = None
    snr_bar: Optional[str] = None
    convergence_plot: Optional[str] = None
    wiener_gain_map: Optional[str] = None
    data: Optional[StepChartsData] = Field(default_factory=StepChartsData)


class StepResult(BaseModel):
    step_id: str
    label: str
    image_base64: str
    stats: dict[str, Any]
    charts: StepCharts
    error: Optional[str] = None


class SummaryReport(BaseModel):
    snr_original: float
    snr_final: float
    snr_improvement_db: float
    variance_original: float
    variance_final: float
    dominant_noise_type: str
    processing_time_ms: float


class PipelineResult(BaseModel):
    session_id: str
    steps: list[StepResult]
    summary: SummaryReport
