import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Props {
  data: Array<Record<string, any>>;
}

export const InteractiveSNR: React.FC<Props> = ({ data }) => {
  return (
    <div className="surface-2" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: 4, fontSize: 14 }}>Signal-to-Noise Ratio</h3>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, marginBottom: 16, fontWeight: 600 }}>
        FORMULA: SNR = 10 · log₁₀(μ² / σ²)
      </p>
      
      <div style={{ flex: 1, minHeight: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#000" horizontal={false} />
            <XAxis 
              type="number" 
              stroke="#000" 
              tick={{ fill: '#000', fontSize: 10, fontFamily: 'var(--font-mono)' }} 
            />
            <YAxis 
              dataKey="name" 
              type="category" 
              stroke="#000" 
              tick={{ fill: '#000', fontSize: 12, fontWeight: 600 }} 
            />
            <Tooltip 
              cursor={{ fill: 'rgba(0,0,0,0.05)' }}
              contentStyle={{ border: '3px solid #000', borderRadius: 0, boxShadow: '4px 4px 0 #000' }}
              itemStyle={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#000' }}
            />
            <Bar dataKey="snr" isAnimationActive={false}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={index === 0 ? '#444444' : '#E03C31'} stroke="#000" strokeWidth={2} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
