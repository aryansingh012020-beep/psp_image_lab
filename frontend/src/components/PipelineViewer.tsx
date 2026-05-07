import React from 'react';
import type { PipelineResult } from '../types/api';
import { SummaryBar } from './SummaryBar';
import { StepCard } from './StepCard';
import { ImageComparison } from './ImageComparison';
import { InteractiveSNR } from './charts/InteractiveSNR';

interface Props {
  result: PipelineResult;
  originalImage: string;
  onReset: () => void;
}

export const PipelineViewer: React.FC<Props> = ({ result, originalImage, onReset }) => {
  const lastStep = result.steps[result.steps.length - 1];
  const finalImage = lastStep?.image_base64 ?? originalImage;

  const downloadImage = () => {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${finalImage}`;
    link.download = 'enhanced_image.png';
    link.click();
  };

  const downloadReport = () => {
    // Basic text report generation
    const text = `
    PSP IMAGE LAB — REPORT
    ----------------------
    SNR Improvement: ${result.summary.snr_improvement_db.toFixed(2)} dB
    Dominant Noise: ${result.summary.dominant_noise_type}
    `;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'report.txt';
    link.click();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', padding: 32, gap: 32, maxWidth: 1200, margin: '0 auto', width: '100%' }}>
      
      {/* ── Summary Bar ── */}
      <SummaryBar summary={result.summary} />

      {/* ── Step Cards ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
        {result.steps.map((step, i) => (
          <StepCard
            key={step.step_id}
            result={step}
            originalImage={originalImage}
            index={i}
          />
        ))}
      </div>

      {/* ── Final Comparison ── */}
      <div className="surface" style={{ background: '#F2B705' }}>
        <h2 style={{ marginBottom: 24, fontSize: 24 }}>FINAL PIPELINE RESULT</h2>
        <ImageComparison before={originalImage} after={finalImage} />

        {/* SNR bar from last step */}
        {lastStep?.charts.data?.snr_data && (
          <div style={{ marginTop: 24, height: 300, background: '#fff', border: '3px solid #000', boxShadow: '6px 6px 0 #000' }}>
            <InteractiveSNR data={lastStep.charts.data.snr_data} />
          </div>
        )}
      </div>

      {/* ── Export Section ── */}
      <div className="surface" style={{ background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: 24, margin: 0 }}>EXPORT DATA</h2>
        <div style={{ display: 'flex', gap: 16 }}>
          <button className="btn btn-primary" onClick={downloadImage}>
            DOWNLOAD ENHANCED IMAGE
          </button>
          <button className="btn btn-ghost" onClick={downloadReport}>
            DOWNLOAD REPORT
          </button>
          <button className="btn" onClick={onReset} style={{ background: '#000', color: '#fff' }}>
            START NEW
          </button>
        </div>
      </div>
    </div>
  );
};
