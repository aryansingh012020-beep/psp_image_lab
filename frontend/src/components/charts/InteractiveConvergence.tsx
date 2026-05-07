import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  data: Array<Record<string, any>>;
}

export const InteractiveConvergence: React.FC<Props> = ({ data }) => {
  return (
    <div className="surface-2" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: 4, fontSize: 14 }}>MRF Convergence</h3>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, marginBottom: 16, fontWeight: 600 }}>
        FORMULA: E(x) = E_data(x, y) + β · E_smooth(x)
      </p>
      
      <div style={{ flex: 1, minHeight: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#000" />
            <XAxis 
              dataKey="iteration" 
              stroke="#000" 
              tick={{ fill: '#000', fontSize: 10, fontFamily: 'var(--font-mono)' }} 
            />
            <YAxis 
              stroke="#000" 
              tick={{ fill: '#000', fontSize: 10, fontFamily: 'var(--font-mono)' }} 
            />
            <Tooltip 
              contentStyle={{ border: '3px solid #000', borderRadius: 0, boxShadow: '4px 4px 0 #000' }}
              itemStyle={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0055A4' }}
              labelStyle={{ color: '#000', fontWeight: 700, marginBottom: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="energy" 
              stroke="#0055A4" 
              strokeWidth={3} 
              dot={{ stroke: '#000', strokeWidth: 2, fill: '#0055A4', r: 4 }} 
              activeDot={{ r: 6, stroke: '#000', strokeWidth: 2, fill: '#F2B705' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
