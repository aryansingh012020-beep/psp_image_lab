import React from 'react';

interface Props {
  src: string;         // base64 PNG string
  alt?: string;
  caption?: string;
  style?: React.CSSProperties;
}

export const ChartImage: React.FC<Props> = ({ src, alt = 'Chart', caption, style }) => {
  if (!src) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, ...style }}>
      <img
        src={`data:image/png;base64,${src}`}
        alt={alt}
        style={{
          width: '100%',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          background: 'var(--color-chart-bg)',
        }}
      />
      {caption && (
        <p style={{ fontSize: 10, color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)', textAlign: 'center' }}>
          {caption}
        </p>
      )}
    </div>
  );
};
