import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  data: Array<Record<string, any>>;
  title: string;
}

export const InteractiveHistogram: React.FC<Props> = ({ data, title }) => {
  const isRGB = data.length > 0 && 'Red' in data[0];

  return (
    <div className="surface-2" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: 4, fontSize: 14 }}>{title}</h3>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, marginBottom: 16, fontWeight: 600 }}>
        FORMULA: PDF(x) = n_x / N
      </p>
      
      <div style={{ flex: 1, minHeight: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#000" vertical={false} />
            <XAxis 
              dataKey="intensity" 
              stroke="#000" 
              tick={{ fill: '#000', fontSize: 10, fontFamily: 'var(--font-mono)' }} 
              tickFormatter={(v) => Number(v).toFixed(1)}
            />
            <YAxis 
              stroke="#000" 
              tick={{ fill: '#000', fontSize: 10, fontFamily: 'var(--font-mono)' }} 
            />
            <Tooltip 
              contentStyle={{ border: '3px solid #000', borderRadius: 0, boxShadow: '4px 4px 0 #000' }}
              itemStyle={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}
              labelStyle={{ color: '#000', fontWeight: 700, marginBottom: 4 }}
            />
            {isRGB ? (
              <>
                <Area type="step" dataKey="Red" stroke="#E03C31" fill="#E03C31" fillOpacity={0.5} isAnimationActive={false} />
                <Area type="step" dataKey="Green" stroke="#3ecf8e" fill="#3ecf8e" fillOpacity={0.5} isAnimationActive={false} />
                <Area type="step" dataKey="Blue" stroke="#0055A4" fill="#0055A4" fillOpacity={0.5} isAnimationActive={false} />
              </>
            ) : (
              <Area type="step" dataKey="Gray" stroke="#000" fill="#000" fillOpacity={0.5} isAnimationActive={false} />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
