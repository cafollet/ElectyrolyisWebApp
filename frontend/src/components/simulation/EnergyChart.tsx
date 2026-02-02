/**
 * Energy convergence chart component.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Card } from '../common';

interface EnergyChartProps {
  energyHistory: number[];
  finalEnergy?: number;
  title?: string;
}

export function EnergyChart({ energyHistory, finalEnergy, title = 'Energy Convergence' }: EnergyChartProps) {
  if (!energyHistory || energyHistory.length === 0) {
    return (
      <Card title={title}>
        <div className="h-64 flex items-center justify-center text-gray-500">
          No energy history data available
        </div>
      </Card>
    );
  }

  const data = energyHistory.map((energy, index) => ({
    iteration: index + 1,
    energy,
  }));

  const minEnergy = Math.min(...energyHistory);
  const maxEnergy = Math.max(...energyHistory);
  const padding = (maxEnergy - minEnergy) * 0.1 || 0.1;

  return (
    <Card title={title}>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="iteration"
              label={{ value: 'Iteration', position: 'bottom', offset: 0 }}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              domain={[minEnergy - padding, maxEnergy + padding]}
              label={{ value: 'Energy (Ha)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => value.toFixed(3)}
            />
            <Tooltip
              formatter={(value: number) => [value.toFixed(6) + ' Ha', 'Energy']}
              labelFormatter={(label) => `Iteration ${label}`}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Line
              type="monotone"
              dataKey="energy"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#2563eb' }}
            />
            {finalEnergy && (
              <ReferenceLine
                y={finalEnergy}
                stroke="#10b981"
                strokeDasharray="5 5"
                label={{
                  value: `Final: ${finalEnergy.toFixed(4)} Ha`,
                  position: 'right',
                  fill: '#10b981',
                  fontSize: 12,
                }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}