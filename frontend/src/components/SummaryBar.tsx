import React from 'react';
import type { SummaryReport } from '../types/api';

interface Props {
  summary: SummaryReport;
}

function fmt(n: number, d = 2): string {
  return isFinite(n) ? n.toFixed(d) : '—';
}

export const SummaryBar: React.FC<Props> = ({ summary }) => {
  const improvement = summary.snr_improvement_db;
  const impColor = improvement >= 0 ? '#3ecf8e' : '#E03C31';

  return (
    <div style={{
      background: '#fff',
      border: '3px solid #000',
      boxShadow: '6px 6px 0 #000',
      padding: '16px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      flexWrap: 'wrap',
    }}>
      <span style={{ fontFamily: 'var(--font-heading)', fontSize: 16, fontWeight: 700, color: '#000', textTransform: 'uppercase', marginRight: 8 }}>
        SUMMARY
      </span>

      <Pill label="SNR Before" value={`${fmt(summary.snr_original)} dB`} color="#000" bg="#F4F4F0" />
      <Pill label="SNR After"  value={`${fmt(summary.snr_final)} dB`}  color="#fff" bg="#0055A4" />
      <Pill
        label="Improvement"
        value={`${improvement >= 0 ? '+' : ''}${fmt(improvement)} dB`}
        color={improvement >= 0 ? '#000' : '#fff'}
        bg={impColor}
      />
      <Pill label="Noise Type" value={summary.dominant_noise_type} color="#000" bg="#F2B705" />
      <Pill label="Time" value={`${fmt(summary.processing_time_ms, 0)} ms`} color="#000" bg="#F4F4F0" />

      <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: '#000', fontFamily: 'var(--font-mono)', fontWeight: 700, border: '2px solid #000', padding: '4px 8px', background: '#fff' }}>
          σ²: {fmt(summary.variance_original, 5)} → {fmt(summary.variance_final, 5)}
        </span>
      </div>
    </div>
  );
};

const Pill: React.FC<{ label: string; value: string; color: string; bg: string }> = ({ label, value, color, bg }) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 12px',
    background: bg,
    border: '3px solid #000',
    boxShadow: '3px 3px 0 #000',
  }}>
    <span style={{ fontSize: 10, color: color === '#fff' ? 'rgba(255,255,255,0.8)' : '#444', textTransform: 'uppercase', fontWeight: 700 }}>
      {label}
    </span>
    <span style={{ fontSize: 14, fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>
      {value}
    </span>
  </div>
);
