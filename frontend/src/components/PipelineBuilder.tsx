import React, { useState } from 'react';
import { processImage, addNoise } from '../api/client';
import { useSessionStore } from '../store/sessionStore';
import type { StepId, StepParams } from '../types/api';

interface StepConfig {
  id: StepId;
  label: string;
  tooltip: string;
  color: string;
}

const STEPS: StepConfig[] = [
  { id: 'noise_analysis',       label: 'Noise Analysis',          tooltip: 'Detects noise variance, salt-and-pepper density, and blur using the MAD estimator on the high-frequency residual.',    color: '#F2B705' },
  { id: 'statistical_analysis', label: 'Statistical Analysis',    tooltip: 'Computes mean, variance, entropy, and 2D autocorrelation of the image — characterises the random field structure.',      color: '#F2B705' },
  { id: 'gaussian_filter',      label: 'Gaussian Filter (LTI)',   tooltip: 'Low-pass LTI filter. Suppresses high-frequency Gaussian noise by convolving with a Gaussian kernel of width σ.',          color: '#0055A4' },
  { id: 'median_filter',        label: 'Median Filter',           tooltip: 'Nonlinear order-statistic filter. Optimal ML estimator under a Laplace noise model. Removes salt-and-pepper well.',       color: '#0055A4' },
  { id: 'bilateral_filter',     label: 'Bilateral Filter',        tooltip: 'Edge-preserving filter. Weights neighbours by spatial distance AND intensity similarity, killing noise without smearing edges.', color: '#0055A4' },
  { id: 'histogram_equalization', label: 'Histogram Equalization', tooltip: 'CDF-based intensity redistribution. Maximises output entropy and dynamic range — improves contrast on dark/flat images.', color: '#3ecf8e' },
  { id: 'bayesian_map',         label: 'Bayesian MAP Denoising',  tooltip: 'Pixelwise Wiener filter. MAP estimate under Gaussian likelihood + Gaussian prior. Gain K = σ²_x / (σ²_x + σ²_n).',             color: '#E03C31' },
  { id: 'mrf_prior',            label: 'MRF ICM Smoothing',       tooltip: 'Markov Random Field via Iterated Conditional Modes. Minimises Gibbs energy E(x) = data fidelity + β · smoothness prior.',    color: '#E03C31' },
];

const DEFAULT_PARAMS: StepParams = {
  gaussian_sigma:        1.5,
  median_kernel_size:    3,
  bilateral_d:           9,
  bilateral_sigma_color: 75.0,
  bilateral_sigma_space: 75.0,
  mrf_iterations:        10,
  mrf_beta:              1.0,
  bayesian_noise_var:    undefined,
};

const KERNEL_SIZES = [3, 5, 7, 9, 11];

interface SliderRowProps {
  label: string; min: number; max: number; step: number;
  value: number; onChange: (v: number) => void; unit?: string;
}
const SliderRow: React.FC<SliderRowProps> = ({ label, min, max, step, value, onChange, unit = '' }) => (
  <div style={{ marginTop: 12 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
      <span className="input-label">{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 700, color: '#000' }}>
        {Number.isInteger(value) ? value : value.toFixed(2)}{unit}
      </span>
    </div>
    <input
      type="range" className="range-slider"
      min={min} max={max} step={step} value={value}
      onChange={e => onChange(parseFloat(e.target.value))}
    />
  </div>
);

export const PipelineBuilder: React.FC = () => {
  const [selected, setSelected] = useState<Set<StepId>>(new Set(STEPS.map(s => s.id)));
  const [params, setParams] = useState<StepParams>(DEFAULT_PARAMS);
  const [bayesianOverride, setBayesianOverride] = useState(false);
  const [bayesianVar, setBayesianVar] = useState(0.01);

  // Noise injection state
  const [noiseType, setNoiseType] = useState<'gaussian' | 'salt_pepper' | 'both'>('gaussian');
  const [noiseSigma, setNoiseSigma] = useState(0.08);
  const [spDensity, setSpDensity] = useState(0.05);
  const [noiseApplied, setNoiseApplied] = useState(false);
  const [isAddingNoise, setIsAddingNoise] = useState(false);
  const [noiseError, setNoiseError] = useState<string | null>(null);

  const { sessionId, originalImage, metadata, isProcessing, setResult, setProcessing, setError } = useSessionStore();

  const applyNoise = async () => {
    if (!sessionId) return;
    setIsAddingNoise(true);
    setNoiseError(null);
    try {
      const resp = await addNoise(sessionId, noiseSigma, noiseType, spDensity);
      // Update the preview image in the store to show the noisy version
      useSessionStore.setState({ originalImage: resp.image_base64 });
      setNoiseApplied(true);
    } catch (e: unknown) {
      setNoiseError(e instanceof Error ? e.message : 'Failed to apply noise');
    } finally {
      setIsAddingNoise(false);
    }
  };

  const toggleStep = (id: StepId) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const setParam = <K extends keyof StepParams>(key: K, val: StepParams[K]) =>
    setParams(p => ({ ...p, [key]: val }));

  const runPipeline = async () => {
    if (!sessionId) return;
    setProcessing(true);
    setError(null);
    try {
      // Maintain the canonical backend ordering
      const ORDER: StepId[] = [
        'noise_analysis', 'statistical_analysis',
        'gaussian_filter', 'median_filter', 'bilateral_filter',
        'histogram_equalization', 'bayesian_map', 'mrf_prior'
      ];
      const orderedSteps = ORDER.filter(id => selected.has(id));
      const result = await processImage(sessionId, {
        steps: orderedSteps,
        params: {
          ...params,
          bayesian_noise_var: bayesianOverride ? bayesianVar : undefined,
        },
      });
      setResult(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Processing failed');
      setProcessing(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100%', minHeight: 'calc(100vh - 80px)' }}>

      {/* ── Left Panel — Pipeline Config ─────────────────────────────────── */}
      <div style={{
        width: 320, flexShrink: 0,
        borderRight: '3px solid #000',
        display: 'flex', flexDirection: 'column',
        background: '#fff',
        overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{ padding: '24px 24px 16px', borderBottom: '3px solid #000', background: '#F2B705' }}>
          <h2 style={{ fontSize: 20, marginBottom: 4 }}>CONFIGURATION</h2>
          <p style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase' }}>Select processing steps</p>
        </div>

        {/* ── Noise Injection Panel ──────────────────────────── */}
        <div style={{ borderBottom: '3px solid #000', background: noiseApplied ? '#3ecf8e' : '#fff' }}>
          <div style={{ padding: '16px', borderBottom: '2px solid #000', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: 14, fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>🔴 Add Artificial Noise</p>
              <p style={{ fontSize: 11, color: '#444', margin: 0, marginTop: 2 }}>Corrupt image to demonstrate denoising</p>
            </div>
            {noiseApplied && (
              <span style={{ background: '#000', color: '#fff', padding: '2px 8px', fontSize: 11, fontWeight: 700 }}>APPLIED</span>
            )}
          </div>

          <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Noise Type Selector */}
            <div>
              <p className="input-label" style={{ marginBottom: 6 }}>Noise Type</p>
              <div style={{ display: 'flex', gap: 8 }}>
                {(['gaussian', 'salt_pepper', 'both'] as const).map(t => (
                  <button
                    key={t}
                    onClick={() => setNoiseType(t)}
                    style={{
                      flex: 1, padding: '6px 4px', fontSize: 10, fontWeight: 700,
                      textTransform: 'uppercase', border: '2px solid #000',
                      background: noiseType === t ? '#E03C31' : '#fff',
                      color: noiseType === t ? '#fff' : '#000',
                      cursor: 'pointer', boxShadow: noiseType === t ? '2px 2px 0 #000' : 'none',
                    }}
                  >
                    {t === 'salt_pepper' ? 'S&P' : t}
                  </button>
                ))}
              </div>
            </div>

            {/* Sigma Slider (Gaussian) */}
            {(noiseType === 'gaussian' || noiseType === 'both') && (
              <SliderRow label="Noise Strength (σ)" min={0.02} max={0.4} step={0.01} value={noiseSigma} onChange={setNoiseSigma} />
            )}

            {/* Density Slider (S&P) */}
            {(noiseType === 'salt_pepper' || noiseType === 'both') && (
              <SliderRow label="S&P Density" min={0.01} max={0.3} step={0.01} value={spDensity} onChange={setSpDensity} />
            )}

            {noiseError && <div className="error-box" style={{ fontSize: 11 }}>{noiseError}</div>}

            <button
              className="btn btn-full"
              style={{ background: '#E03C31', color: '#fff', border: '3px solid #000', boxShadow: '4px 4px 0 #000' }}
              onClick={applyNoise}
              disabled={isAddingNoise}
            >
              {isAddingNoise ? <><div className="spinner" style={{ width: 14, height: 14 }} /> APPLYING...</> : '⚡ CORRUPT IMAGE'}
            </button>
          </div>
        </div>

        {/* Steps list */}
        <div style={{ padding: '0', flex: 1, overflowY: 'auto' }}>
          {STEPS.map(step => {
            const active = selected.has(step.id);
            return (
              <div key={step.id} style={{ borderBottom: '3px solid #000', background: active ? '#F4F4F0' : '#fff' }}>
                <div
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: 16,
                    padding: '16px', cursor: 'pointer',
                  }}
                  onClick={() => toggleStep(step.id)}
                >
                  <input
                    type="checkbox"
                    className="checkbox-custom"
                    checked={active}
                    onChange={() => toggleStep(step.id)}
                    onClick={e => e.stopPropagation()}
                    style={{ marginTop: 2 }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{
                        width: 12, height: 12, border: '2px solid #000',
                        background: active ? step.color : '#fff', flexShrink: 0,
                      }} />
                      <span style={{ fontSize: 16, fontWeight: 700, color: '#000', textTransform: 'uppercase' }}>
                        {step.label}
                      </span>
                    </div>
                    <p style={{ fontSize: 12, color: '#444', marginTop: 4, lineHeight: 1.5, fontWeight: 500 }}>
                      {step.tooltip}
                    </p>
                  </div>
                </div>

                {/* Sub-params */}
                {active && (
                  <div style={{ padding: '0 16px 16px 52px' }}>

                    {/* Gaussian */}
                    {step.id === 'gaussian_filter' && (
                      <SliderRow label="Kernel σ" min={0.3} max={5} step={0.1} value={params.gaussian_sigma} onChange={v => setParam('gaussian_sigma', v)} />
                    )}

                    {/* Median */}
                    {step.id === 'median_filter' && (
                      <div style={{ marginTop: 12 }}>
                        <p className="input-label" style={{ marginBottom: 6 }}>Kernel Size</p>
                        <div style={{ display: 'flex', gap: 8 }}>
                          {KERNEL_SIZES.map(k => (
                            <button
                              key={k}
                              onClick={() => setParam('median_kernel_size', k)}
                              style={{
                                flex: 1, padding: '6px 0', fontSize: 13, fontWeight: 700,
                                border: '2px solid #000', cursor: 'pointer',
                                background: params.median_kernel_size === k ? '#0055A4' : '#fff',
                                color: params.median_kernel_size === k ? '#fff' : '#000',
                                boxShadow: params.median_kernel_size === k ? '2px 2px 0 #000' : 'none',
                              }}
                            >
                              {k}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Bilateral */}
                    {step.id === 'bilateral_filter' && (
                      <>
                        <SliderRow label="Diameter (d)" min={3} max={15} step={2} value={params.bilateral_d} onChange={v => setParam('bilateral_d', Math.round(v))} />
                        <SliderRow label="σ Color" min={10} max={150} step={5} value={params.bilateral_sigma_color} onChange={v => setParam('bilateral_sigma_color', v)} />
                        <SliderRow label="σ Space" min={10} max={150} step={5} value={params.bilateral_sigma_space} onChange={v => setParam('bilateral_sigma_space', v)} />
                      </>
                    )}

                    {/* Bayesian */}
                    {step.id === 'bayesian_map' && (
                      <div style={{ marginTop: 8 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginBottom: 8 }}>
                          <input type="checkbox" className="checkbox-custom" checked={bayesianOverride} onChange={e => setBayesianOverride(e.target.checked)} />
                          <span className="input-label" style={{ margin: 0 }}>Override variance</span>
                        </label>
                        {bayesianOverride && (
                          <SliderRow label="σ_n²" min={0.001} max={0.1} step={0.001} value={bayesianVar} onChange={setBayesianVar} />
                        )}
                      </div>
                    )}

                    {/* MRF */}
                    {step.id === 'mrf_prior' && (
                      <>
                        <SliderRow label="β Smoothness" min={0.1} max={5} step={0.1} value={params.mrf_beta} onChange={v => setParam('mrf_beta', v)} />
                        <SliderRow label="Iterations" min={5} max={50} step={1} value={params.mrf_iterations} onChange={v => setParam('mrf_iterations', Math.round(v))} />
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Run button */}
        <div style={{ padding: 24, borderTop: '3px solid #000', background: '#fff' }}>
          <button
            className="btn btn-primary btn-full"
            onClick={runPipeline}
            disabled={isProcessing || selected.size === 0}
          >
            {isProcessing ? (
              <><div className="spinner" /> PROCESSING...</>
            ) : (
              <>RUN PIPELINE</>
            )}
          </button>
          {isProcessing && (
            <div style={{ marginTop: 16 }}>
              <div className="progress-bar-track progress-bar-indeterminate">
                <div className="progress-bar-fill" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Right Panel — Image Preview ───────────────────────────────────── */}
      <div style={{ flex: 1, padding: 32, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 24, background: '#F4F4F0' }}>
        <div>
          <h2 style={{ fontSize: 24, marginBottom: 8 }}>IMAGE PREVIEW</h2>
          <p style={{ fontSize: 14, fontWeight: 500, color: '#444' }}>Configure the pipeline on the left and run to process.</p>
        </div>

        {/* Image */}
        {originalImage && (
          <div className="surface" style={{ padding: 24, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img
              src={`data:image/png;base64,${originalImage}`}
              alt="Original"
              style={{
                maxWidth: '100%', maxHeight: 500,
                boxShadow: '6px 6px 0 #000'
              }}
            />
          </div>
        )}

        {/* Metadata */}
        {metadata && (
          <div className="surface-2" style={{ border: '3px solid #000', boxShadow: '6px 6px 0 #000', background: '#fff' }}>
            <h3 style={{ fontSize: 16, borderBottom: '3px solid #000', paddingBottom: 8, marginBottom: 16, display: 'inline-block' }}>METADATA</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 16 }}>
              {[
                ['Dimensions', `${metadata.width} × ${metadata.height}`],
                ['Channels',   metadata.channels === 1 ? 'Grayscale' : 'RGB'],
                ['Format',     metadata.format],
                ['Size',       `${metadata.file_size_kb.toFixed(1)} KB`],
              ].map(([k, v]) => (
                <div key={String(k)} style={{ background: '#F4F4F0', border: '3px solid #000', padding: '8px 12px', boxShadow: '3px 3px 0 #000' }}>
                  <p style={{ fontSize: 10, color: '#444', textTransform: 'uppercase', fontWeight: 700 }}>{k}</p>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: '#000', marginTop: 4 }}>{v}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
