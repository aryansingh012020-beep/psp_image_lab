import React, { useState } from 'react';
import { processImage } from '../api/client';
import { useSessionStore } from '../store/sessionStore';
import type { StepId, StepParams } from '../types/api';

interface StepConfig {
  id: StepId;
  label: string;
  tooltip: string;
  color: string;
}

const STEPS: StepConfig[] = [
  { id: 'noise_analysis', label: 'Detect Noise Level', tooltip: 'Automatically detects the noise variance in the image to guide the smart filters.', color: '#F2B705' },
  { id: 'bayesian_map',   label: 'Smart Denoise (Bayesian)', tooltip: 'Removes fine grain and noise intelligently without destroying underlying textures and details.', color: '#0055A4' },
  { id: 'mrf_prior',      label: 'Structure Preservation (MRF)', tooltip: 'Smooths the image while keeping important object edges perfectly sharp.', color: '#E03C31' },
];

const DEFAULT_PARAMS: StepParams = {
  gaussian_sigma:        1.0,
  median_kernel_size:    3,
  bilateral_d:           9,
  bilateral_sigma_color: 75.0,
  bilateral_sigma_space: 75.0,
  mrf_iterations:        10,
  mrf_beta:              1.0,
  bayesian_noise_var:    undefined,
};

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

  const { sessionId, originalImage, metadata, isProcessing, setResult, setProcessing, setError } = useSessionStore();

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
      const orderedSteps = STEPS.map(s => s.id).filter(id => selected.has(id));
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
