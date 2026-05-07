"""POST /api/process/{session_id} — executes the full analysis/filter pipeline."""
from __future__ import annotations
import time
import traceback
import numpy as np
from fastapi import APIRouter, HTTPException

from services import session_manager
from services.noise_detector import classify_noise
from services.stat_analyzer import analyze as stat_analyze
from services.filters import (
    apply_gaussian_filter,
    apply_median_filter,
    apply_bilateral_filter,
    apply_histogram_equalization,
)
from services.bayesian_estimator import apply_bayesian_map
from services.markov_field import apply_mrf
from services import visualizer
from utils.image_io import ndarray_to_base64_png, get_luminance
from models.schemas import (
    ProcessRequest, PipelineResult, StepResult, StepCharts, StepChartsData, SummaryReport
)

router = APIRouter()

STEP_LABELS = {
    "noise_analysis":        "Noise Analysis",
    "statistical_analysis":  "Statistical Analysis",
    "gaussian_filter":       "Gaussian Filter",
    "median_filter":         "Median Filter",
    "bilateral_filter":      "Bilateral Filter",
    "histogram_equalization": "Histogram Equalization",
    "bayesian_map":          "Bayesian MAP Denoising",
    "mrf_prior":             "MRF ICM Smoothing",
}


def _snr_db(arr: np.ndarray) -> float:
    """PSNR-style SNR: 10·log10(1 / MSE_of_high_freq_residual).
    Uses the HF residual as proxy for noise energy — gives meaningful
    improvement values even on clean images."""
    from scipy.ndimage import gaussian_filter
    lum = get_luminance(arr).astype(np.float64)
    blurred = gaussian_filter(lum, sigma=1.5)
    residual = lum - blurred
    mse = float(np.mean(residual ** 2))
    if mse <= 1e-12:
        return 60.0   # essentially noise-free
    return float(10.0 * np.log10(1.0 / mse))


@router.post("/process/{session_id}", response_model=PipelineResult)
async def process_image(session_id: str, req: ProcessRequest) -> PipelineResult:
    image = session_manager.get_session_image(session_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    t_start = time.perf_counter()
    steps_results: list[StepResult] = []
    current_image = image.copy()
    original_image = image.copy()

    # Shared noise report (may be needed by filters)
    noise_report = None
    snr_original = _snr_db(original_image)

    for step_id in req.steps:
        if step_id not in STEP_LABELS:
            continue
        label = STEP_LABELS[step_id]
        step_error: str | None = None
        stats: dict = {}
        charts = StepCharts()
        step_image = current_image

        try:
            # ── NOISE ANALYSIS ────────────────────────────────────────────────
            if step_id == "noise_analysis":
                noise_report = classify_noise(current_image)
                stats = noise_report.to_dict()
                charts.histogram = visualizer.generate_histogram(
                    current_image, "Original Image — Pixel Histogram"
                )

            # ── STATISTICAL ANALYSIS ──────────────────────────────────────────
            elif step_id == "statistical_analysis":
                stat_rep = stat_analyze(current_image)
                stats = stat_rep
                charts.histogram = visualizer.generate_histogram(
                    current_image, "Statistical Analysis — Histogram"
                )
                charts.correlation_map = visualizer.generate_correlation_map(current_image)

            # ── GAUSSIAN FILTER ────────────────────────────────────────────────
            elif step_id == "gaussian_filter":
                sigma = req.params.gaussian_sigma
                step_image = apply_gaussian_filter(current_image, sigma)
                stat_after = stat_analyze(step_image)
                stats = {
                    "sigma": sigma,
                    "snr_before_db": _snr_db(current_image),
                    "snr_after_db": _snr_db(step_image),
                    "mean": stat_after["overall"]["mean"],
                    "variance": stat_after["overall"]["variance"],
                }
                charts.histogram = visualizer.generate_histogram(step_image, "After Gaussian Filter")
                current_image = step_image

            # ── MEDIAN FILTER ──────────────────────────────────────────────────
            elif step_id == "median_filter":
                k = req.params.median_kernel_size
                step_image = apply_median_filter(current_image, k)
                stats = {
                    "kernel_size": k,
                    "snr_before_db": _snr_db(current_image),
                    "snr_after_db": _snr_db(step_image),
                }
                charts.histogram = visualizer.generate_histogram(step_image, "After Median Filter")
                current_image = step_image

            # ── BILATERAL FILTER ───────────────────────────────────────────────
            elif step_id == "bilateral_filter":
                p = req.params
                step_image, bil_err = apply_bilateral_filter(
                    current_image, p.bilateral_d, p.bilateral_sigma_color, p.bilateral_sigma_space
                )
                if bil_err:
                    step_error = bil_err
                else:
                    stats = {
                        "d": p.bilateral_d,
                        "sigma_color": p.bilateral_sigma_color,
                        "sigma_space": p.bilateral_sigma_space,
                        "snr_before_db": _snr_db(current_image),
                        "snr_after_db": _snr_db(step_image),
                    }
                    charts.histogram = visualizer.generate_histogram(step_image, "After Bilateral Filter")
                    current_image = step_image

            # ── HISTOGRAM EQUALIZATION ─────────────────────────────────────────
            elif step_id == "histogram_equalization":
                step_image = apply_histogram_equalization(current_image)
                stat_after = stat_analyze(step_image)
                stats = {
                    "entropy_before": stat_analyze(current_image)["overall"]["entropy"],
                    "entropy_after": stat_after["overall"]["entropy"],
                    "snr_before_db": _snr_db(current_image),
                    "snr_after_db": _snr_db(step_image),
                }
                charts.histogram = visualizer.generate_histogram(step_image, "After Histogram Equalization")
                current_image = step_image

            # ── BAYESIAN MAP ───────────────────────────────────────────────────
            elif step_id == "bayesian_map":
                # Determine noise variance
                if req.params.bayesian_noise_var is not None:
                    nvar = req.params.bayesian_noise_var
                else:
                    if noise_report is None:
                        noise_report = classify_noise(current_image)
                    # Enforce a minimum noise floor so denoising is always meaningful
                    raw_sigma = noise_report.estimated_sigma
                    effective_sigma = max(raw_sigma, 0.04)  # at least σ=0.04 → variance=0.0016
                    nvar = effective_sigma ** 2

                step_image, bay_stats = apply_bayesian_map(current_image, nvar)
                stats = {
                    "noise_variance_used": bay_stats["noise_variance_used"],
                    "mean_posterior_variance": bay_stats["mean_posterior_variance"],
                    "snr_before_db": _snr_db(current_image),
                    "snr_after_db": _snr_db(step_image),
                }
                charts.wiener_gain_map = bay_stats["wiener_gain_map_base64"]
                charts.histogram = visualizer.generate_histogram(step_image, "After Bayesian MAP")
                current_image = step_image

            # ── MRF ICM ────────────────────────────────────────────────────────
            elif step_id == "mrf_prior":
                if noise_report is None:
                    noise_report = classify_noise(current_image)
                # Same minimum floor as Bayesian step
                raw_sigma = noise_report.estimated_sigma if noise_report else 0.04
                effective_sigma = max(raw_sigma, 0.04)
                sigma_n2 = effective_sigma ** 2

                mrf_out = apply_mrf(
                    current_image,
                    sigma_n2=sigma_n2,
                    beta=req.params.mrf_beta,
                    iterations=req.params.mrf_iterations,
                )
                step_image = mrf_out["filtered_image"]
                stats = {
                    "iterations_run": mrf_out["iterations_run"],
                    "beta": req.params.mrf_beta,
                    "sigma_n2": sigma_n2,
                    "final_energy": mrf_out["convergence_curve"][-1] if mrf_out["convergence_curve"] else 0.0,
                    "snr_before_db": _snr_db(current_image),
                    "snr_after_db": _snr_db(step_image),
                    "convergence_curve": mrf_out["convergence_curve"],
                }
                charts.convergence_plot = visualizer.generate_convergence_plot(
                    mrf_out["convergence_curve"]
                )
                charts.histogram = visualizer.generate_histogram(step_image, "After MRF ICM")
                current_image = step_image

        except Exception:
            step_error = traceback.format_exc()
            step_image = current_image  # fallback — keep last good image

        if charts.data is None:
            charts.data = StepChartsData()
        charts.data.histogram_data = visualizer.get_histogram_data(step_image)
        if "snr_before_db" in stats and "snr_after_db" in stats:
            charts.data.snr_data = visualizer.get_snr_data(stats["snr_before_db"], stats["snr_after_db"])
        if "convergence_curve" in stats:
            charts.data.convergence_data = visualizer.get_convergence_data(stats["convergence_curve"])

        steps_results.append(StepResult(
            step_id=step_id,
            label=label,
            image_base64=ndarray_to_base64_png(step_image),
            stats=stats,
            charts=charts,
            error=step_error,
        ))

    t_end = time.perf_counter()
    processing_ms = (t_end - t_start) * 1000.0

    snr_final = _snr_db(current_image)
    snr_improvement = snr_final - snr_original

    lum_orig = get_luminance(original_image).ravel()
    lum_final = get_luminance(current_image).ravel()

    # SNR bar chart for summary
    snr_bar_b64 = visualizer.generate_snr_bar(snr_original, snr_final)

    # Attach snr_bar to last step's chart slot (or first step if only one)
    if steps_results:
        last = steps_results[-1]
        last.charts.snr_bar = snr_bar_b64

    dominant = "None Detected"
    if noise_report and noise_report.noise_types:
        dominant = noise_report.noise_types[0]

    summary = SummaryReport(
        snr_original=snr_original,
        snr_final=snr_final,
        snr_improvement_db=snr_improvement,
        variance_original=float(lum_orig.var()),
        variance_final=float(lum_final.var()),
        dominant_noise_type=dominant,
        processing_time_ms=processing_ms,
    )

    return PipelineResult(
        session_id=session_id,
        steps=steps_results,
        summary=summary,
    )
