import React from 'react';

interface Props {
  before: string;   // base64 PNG
  after: string;    // base64 PNG
  label?: string;
}

export const ImageComparison: React.FC<Props> = ({ before, after, label }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {label && (
        <h3 style={{ fontSize: 18, borderBottom: '3px solid #000', paddingBottom: 8, display: 'inline-block' }}>
          {label}
        </h3>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Before */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ background: '#E03C31', color: '#fff', padding: '4px 8px', fontWeight: 700, border: '3px solid #000', alignSelf: 'flex-start', boxShadow: '3px 3px 0 #000' }}>
            ORIGINAL
          </div>
          <img 
            src={`data:image/png;base64,${before}`} 
            alt="Original" 
            style={{ width: '100%', objectFit: 'contain', border: '3px solid #000', boxShadow: '6px 6px 0 #000', background: '#fff' }} 
          />
        </div>

        {/* After */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ background: '#3ecf8e', color: '#000', padding: '4px 8px', fontWeight: 700, border: '3px solid #000', alignSelf: 'flex-start', boxShadow: '3px 3px 0 #000' }}>
            ENHANCED
          </div>
          <img 
            src={`data:image/png;base64,${after}`} 
            alt="Enhanced" 
            style={{ width: '100%', objectFit: 'contain', border: '3px solid #000', boxShadow: '6px 6px 0 #000', background: '#fff' }} 
          />
        </div>
      </div>
    </div>
  );
};
