import React from 'react';
import './styles/globals.css';
import { useSessionStore } from './store/sessionStore';
import { UploadZone } from './components/UploadZone';
import { PipelineBuilder } from './components/PipelineBuilder';
import { PipelineViewer } from './components/PipelineViewer';

const Header: React.FC<{ phase: string; onReset: () => void }> = ({ phase, onReset }) => (
  <header style={{
    borderBottom: '3px solid #000',
    background: '#fff',
    display: 'flex',
    alignItems: 'center',
    padding: '16px 24px',
    gap: 16,
    flexShrink: 0,
    position: 'sticky',
    top: 0,
    zIndex: 60,
  }}>
    {/* Logo */}
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        width: 32, height: 32,
        background: '#E03C31', border: '3px solid #000', boxShadow: '3px 3px 0 #000',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, fontWeight: 700, color: '#fff',
        fontFamily: 'var(--font-mono)',
      }}>
        Ψ
      </div>
      <div>
        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 18, color: '#000', textTransform: 'uppercase' }}>
          PSP Image Lab
        </span>
        <span style={{ fontSize: 12, color: '#000', marginLeft: 8, fontFamily: 'var(--font-mono)', fontWeight: 700, background: '#F2B705', border: '2px solid #000', padding: '0 4px' }}>
          v1.0
        </span>
      </div>
    </div>

    {/* Phase breadcrumb */}
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 24 }}>
      {(['upload', 'configure', 'results'] as const).map((p, i) => {
        const labels = { upload: 'UPLOAD', configure: 'CONFIGURE', results: 'RESULTS' };
        const isActive = p === phase;
        const isDone = ['upload', 'configure', 'results'].indexOf(p) < ['upload', 'configure', 'results'].indexOf(phase);
        return (
          <React.Fragment key={p}>
            {i > 0 && <span style={{ color: '#000', fontSize: 16, fontWeight: 700 }}>›</span>}
            <span style={{
              fontSize: 14, fontWeight: 700,
              color: isActive ? '#fff' : isDone ? '#000' : '#888',
              background: isActive ? '#0055A4' : 'transparent',
              padding: isActive ? '4px 8px' : '0',
              border: isActive ? '3px solid #000' : 'none',
              boxShadow: isActive ? '3px 3px 0 #000' : 'none',
              fontFamily: 'var(--font-mono)',
            }}>
              {isDone ? '✓ ' : ''}{labels[p]}
            </span>
          </React.Fragment>
        );
      })}
    </div>

    {/* Spacer */}
    <div style={{ flex: 1 }} />

    {phase !== 'upload' && (
      <button className="btn" style={{ padding: '8px 16px', fontSize: 12, background: '#F2B705' }} onClick={onReset}>
        RESET LAB
      </button>
    )}
  </header>
);

const App: React.FC = () => {
  const { phase, originalImage, pipelineResult, error, reset } = useSessionStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: 'var(--color-bg)' }}>
      <Header phase={phase} onReset={reset} />

      {/* ── Phase 1: Upload ─────────────────────────────────────────────── */}
      {phase === 'upload' && (
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: '48px 24px',
        }}>
          {/* Hero text */}
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h1 style={{
              fontFamily: 'var(--font-heading)', fontSize: '3rem', fontWeight: 700,
              color: '#000', marginBottom: 16, border: '5px solid #000', padding: '16px 32px',
              display: 'inline-block', background: '#F2B705', boxShadow: '10px 10px 0 #000', textTransform: 'uppercase'
            }}>
              Intelligent Image Cleaning
            </h1>
            <p style={{ color: '#000', fontSize: 16, fontWeight: 600, maxWidth: 600, margin: '24px auto 0', background: '#fff', border: '3px solid #000', padding: '16px', boxShadow: '6px 6px 0 #000' }}>
              Upload an image to run a full PSP-grounded analysis pipeline — noise estimation,
              Bayesian MAP denoising, MRF smoothing, and statistical characterization.
            </p>
          </div>

          <UploadZone />

          {/* Feature pills */}
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center', marginTop: 48, maxWidth: 800 }}>
            {[
              { icon: '⚗', text: 'MAD Noise Estimator', bg: '#0055A4', c: '#fff' },
              { icon: '∏', text: 'Bayesian MAP', bg: '#E03C31', c: '#fff' },
              { icon: '⋈', text: 'MRF ICM Smoothing', bg: '#3ecf8e', c: '#000' },
            ].map(f => (
              <div key={f.text} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '8px 16px',
                background: f.bg,
                color: f.c,
                border: '3px solid #000',
                boxShadow: '4px 4px 0 #000',
                fontSize: 14,
                fontWeight: 700,
                textTransform: 'uppercase'
              }}>
                <span style={{ fontSize: 16 }}>{f.icon}</span>
                <span>{f.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Phase 2: Configure ─────────────────────────────────────────────── */}
      {phase === 'configure' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {error && (
            <div className="error-box" style={{ margin: '16px 24px' }}>⚠ {error}</div>
          )}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <PipelineBuilder />
          </div>
        </div>
      )}

      {/* ── Phase 3: Results ─────────────────────────────────────────────── */}
      {phase === 'results' && pipelineResult && originalImage && (
        <PipelineViewer
          result={pipelineResult}
          originalImage={originalImage}
          onReset={reset}
        />
      )}
    </div>
  );
};

export default App;
