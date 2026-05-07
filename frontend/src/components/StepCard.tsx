import React, { useState } from 'react';
import type { StepResult } from '../types/api';
import { ImageComparison } from './ImageComparison';
import { StatPanel } from './StatPanel';
import { ChartImage } from './ChartImage';
import { InteractiveHistogram } from './charts/InteractiveHistogram';
import { InteractiveSNR } from './charts/InteractiveSNR';
import { InteractiveConvergence } from './charts/InteractiveConvergence';

const THEORY: Record<string, { title: string; body: string }> = {
  noise_analysis: {
    title: 'Noise as a Stochastic Process',
    body: `Image noise is modeled as a 2D random field N(x,y) where each pixel's noise contribution is a realization of a random variable. Gaussian noise follows N ~ 𝒩(0, σ²). The noise variance σ² is estimated using the robust median absolute deviation estimator: σ̂ = median(|r|) / 0.6745, where r = I − G_σ(I) is the high-frequency residual obtained by subtracting a Gaussian-blurred version of the image.`,
  },
  statistical_analysis: {
    title: 'First and Second Order Statistics of Random Fields',
    body: `The mean E[I] and variance Var[I] characterize the first and second moments of the pixel intensity distribution. The 2D autocorrelation function R(τ_x, τ_y) = E[I(x,y)·I(x+τ_x, y+τ_y)] reveals the spatial dependence structure of the random field. For white noise, R is a 2D delta function. For spatially correlated noise, R has broader support.`,
  },
  gaussian_filter: {
    title: 'LTI Filtering of Random Processes',
    body: `A Gaussian filter acts as an LTI system with impulse response h(x,y) = (1/(2πσ²))·exp(−(x²+y²)/(2σ²)). By the convolution theorem, the output PSD is S_out(u,v) = |H(u,v)|²·S_in(u,v), where H(u,v) is the Fourier transform of the kernel. This acts as a low-pass filter suppressing high-frequency noise components.`,
  },
  median_filter: {
    title: 'Nonlinear Robust Estimation',
    body: `Unlike linear filters, the median filter is a nonlinear order-statistic filter. It replaces each pixel by the median of its neighborhood. The median is the ML estimator under a Laplace (double-exponential) noise model, making it optimal for impulsive (salt-and-pepper) noise removal while preserving edges, which linear filters smear.`,
  },
  bilateral_filter: {
    title: 'Joint Spatial-Radiometric Gaussian Weighting',
    body: `The bilateral filter computes a weighted average where weights depend on both spatial proximity (Gaussian with σ_s) and radiometric similarity (Gaussian with σ_r). Pixels far in intensity receive near-zero weight, preserving edges. It approximates the posterior mean under a piecewise-constant image prior with Gaussian noise.`,
  },
  histogram_equalization: {
    title: 'CDF-Based Intensity Redistribution',
    body: `Histogram equalization transforms pixel intensities using the empirical CDF as the mapping function: T(r) = (L−1)·CDF(r), where L is the number of gray levels. This maximizes the entropy of the output distribution, producing a nearly uniform histogram. It is an information-theoretic operation that maximizes the amount of visual information extracted from the dynamic range.`,
  },
  bayesian_map: {
    title: 'MAP Estimation under Gaussian Prior',
    body: `The MAP estimator maximizes p(x|y) ∝ p(y|x)·p(x). With a Gaussian likelihood p(y|x) = 𝒩(x, σ_n²) and a Gaussian prior p(x) = 𝒩(μ_x, σ_x²), the posterior is also Gaussian (conjugate family). The MAP/MMSE estimate is x̂ = μ_x + K·(y − μ_x), where K = σ_x²/(σ_x²+σ_n²) is the Wiener gain that adaptively blends observation and prior based on local SNR.`,
  },
  mrf_prior: {
    title: 'Markov Random Fields and MAP-MRF Estimation',
    body: `A Markov Random Field models the image as a random field satisfying the Markov property: p(x_i | x_j, all j≠i) = p(x_i | x_j, j ∈ N_i). By the Hammersley-Clifford theorem, the joint distribution factorizes over cliques (Gibbs distribution). The energy E(x) = data_fidelity + β·smoothness_prior is minimized using Iterated Conditional Modes (ICM): at each step x_i is updated to minimize E conditioned on all other pixels — a coordinate-descent MAP algorithm.`,
  },
};

const PSP_TAG: Record<string, string> = {
  noise_analysis: 'MAD Estimator',
  statistical_analysis: 'Random Field Moments',
  gaussian_filter: 'LTI / PSD',
  median_filter: 'Order Statistics',
  bilateral_filter: 'Joint Gaussian Kernel',
  histogram_equalization: 'CDF Mapping',
  bayesian_map: 'Bayesian MAP / Wiener',
  mrf_prior: 'Gibbs / ICM',
};

interface Props {
  result: StepResult;
  originalImage: string;
  index: number;
}

export const StepCard: React.FC<Props> = ({ result, originalImage, index }) => {
  const [collapsed, setCollapsed] = useState(false);
  const theory = THEORY[result.step_id];

  return (
    <div className="surface" style={{ padding: 0 }}>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 24px',
          borderBottom: collapsed ? 'none' : '3px solid #000',
          cursor: 'pointer',
          background: 'var(--bauhaus-yellow)',
        }}
        onClick={() => setCollapsed(c => !c)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{
            background: '#fff', border: '3px solid #000', boxShadow: '3px 3px 0 #000',
            padding: '4px 12px', fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)'
          }}>
            {String(index + 1).padStart(2, '0')}
          </span>
          <span style={{ fontFamily: 'var(--font-heading)', fontSize: 20, fontWeight: 700, textTransform: 'uppercase' }}>
            {result.label}
          </span>
          <span className="badge badge-blue">
            {PSP_TAG[result.step_id] ?? ''}
          </span>
          {result.error && <span className="badge badge-red">ERROR</span>}
        </div>
        <span style={{ fontSize: 24, fontWeight: 700 }}>{collapsed ? '+' : '-'}</span>
      </div>

      {!collapsed && (
        <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 32 }}>
          
          {/* ── Error ── */}
          {result.error && (
            <div className="error-box">
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{result.error}</pre>
            </div>
          )}

          {/* ── Image Comparison ── */}
          <ImageComparison
            before={originalImage}
            after={result.image_base64}
          />

          {/* ── Stats & Charts Grid ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
            
            {/* Stats Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ background: '#0055A4', color: '#fff', padding: '4px 8px', fontWeight: 700, border: '3px solid #000', alignSelf: 'flex-start', boxShadow: '3px 3px 0 #000' }}>
                STATISTICS
              </div>
              <div className="surface-2" style={{ padding: 0 }}>
                <StatPanel stats={result.stats} />
              </div>
            </div>

            {/* Interactive Charts */}
            {result.charts.data?.histogram_data && (
              <div style={{ height: 350 }}>
                <InteractiveHistogram data={result.charts.data.histogram_data} title="PIXEL HISTOGRAM" />
              </div>
            )}
            {result.charts.data?.snr_data && (
              <div style={{ height: 350 }}>
                <InteractiveSNR data={result.charts.data.snr_data} />
              </div>
            )}
            {result.charts.data?.convergence_data && (
              <div style={{ height: 350 }}>
                <InteractiveConvergence data={result.charts.data.convergence_data} />
              </div>
            )}
            
            {/* Static Heatmaps */}
            {result.charts.correlation_map && (
              <div style={{ height: 350 }}>
                <div className="surface-2" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <h3 style={{ marginBottom: 4, fontSize: 14 }}>2D AUTOCORRELATION</h3>
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                    <img src={`data:image/png;base64,${result.charts.correlation_map}`} alt="Correlation" style={{ maxHeight: '100%', maxWidth: '100%', border: '2px solid #000' }} />
                  </div>
                </div>
              </div>
            )}
            {result.charts.wiener_gain_map && (
              <div style={{ height: 350 }}>
                <div className="surface-2" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <h3 style={{ marginBottom: 4, fontSize: 14 }}>WIENER GAIN MAP</h3>
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                    <img src={`data:image/png;base64,${result.charts.wiener_gain_map}`} alt="Wiener Gain" style={{ maxHeight: '100%', maxWidth: '100%', border: '2px solid #000' }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ── Theory Box ── */}
          {theory && (
            <div className="surface-2" style={{ background: '#E03C31', color: '#fff' }}>
              <h3 style={{ borderBottom: '3px solid #000', paddingBottom: 8, marginBottom: 12 }}>
                THEORY: {theory.title}
              </h3>
              <p style={{ fontSize: 14, lineHeight: 1.6, fontWeight: 500 }}>
                {theory.body}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
