import React from 'react';

interface Props {
  stats: Record<string, unknown>;
}

const THRESHOLDS: Record<string, { warn: number; field: 'high' | 'low' }> = {
  variance:       { warn: 0.05, field: 'high' },
  estimated_sigma:{ warn: 0.05, field: 'high' },
  sp_density:     { warn: 0.005, field: 'high' },
};

const SNR_FIELDS = ['snr_after_db', 'snr_before_db', 'snr_db', 'snr_linear'];

function fmt(v: unknown): string {
  if (typeof v === 'number') {
    if (!isFinite(v)) return v > 0 ? '+∞' : '−∞';
    if (Math.abs(v) >= 1000) return v.toFixed(1);
    return Number(v.toPrecision(4)).toString();
  }
  if (typeof v === 'string') return v;
  if (Array.isArray(v)) return `[${v.length} values]`;
  if (typeof v === 'object' && v !== null) return '{ … }';
  return String(v);
}

function rowColor(key: string, val: unknown): string | undefined {
  const lk = key.toLowerCase();
  if (SNR_FIELDS.includes(lk) && typeof val === 'number' && val > 20) return '#3ecf8e';
  for (const [field, rule] of Object.entries(THRESHOLDS)) {
    if (lk.includes(field) && typeof val === 'number') {
      if (rule.field === 'high' && val > rule.warn) return '#E03C31';
    }
  }
  return undefined;
}

function flattenStats(stats: Record<string, unknown>, prefix = ''): [string, unknown][] {
  const rows: [string, unknown][] = [];
  for (const [k, v] of Object.entries(stats)) {
    const fullKey = prefix ? `${prefix}.${k}` : k;
    if (Array.isArray(v) && v.length > 10) {
      rows.push([fullKey, `[${v.length} elements]`]);
    } else if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
      rows.push(...flattenStats(v as Record<string, unknown>, fullKey));
    } else {
      rows.push([fullKey, v]);
    }
  }
  return rows;
}

export const StatPanel: React.FC<Props> = ({ stats }) => {
  const rows = flattenStats(stats);
  if (rows.length === 0) return null;

  return (
    <div style={{ overflowX: 'auto', background: '#fff', border: '3px solid #000' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: 12,
        fontFamily: 'var(--font-mono)',
      }}>
        <thead>
          <tr style={{ borderBottom: '3px solid #000', background: '#F4F4F0' }}>
            <th style={{ textAlign: 'left', padding: '8px 12px', color: '#000', fontWeight: 700, fontSize: 12, textTransform: 'uppercase' }}>Metric</th>
            <th style={{ textAlign: 'right', padding: '8px 12px', color: '#000', fontWeight: 700, fontSize: 12, textTransform: 'uppercase' }}>Value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([key, val], i) => {
            const color = rowColor(key, val);
            return (
              <tr
                key={key}
                style={{
                  background: i % 2 === 0 ? '#fff' : '#F4F4F0',
                  borderBottom: '1px solid #000',
                }}
              >
                <td style={{ padding: '8px 12px', color: '#444', whiteSpace: 'nowrap', fontWeight: 600 }}>
                  {key}
                </td>
                <td style={{ padding: '8px 12px', textAlign: 'right', color: color ?? '#000', fontWeight: color ? 700 : 500 }}>
                  {fmt(val)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
