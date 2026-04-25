import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { TimeseriesPointDto } from '../api/api';

interface ChartProps {
  data: TimeseriesPointDto[];
}

type MetricKey = 'bloomRiskScore' | 'eutrophicationRiskScore' | 'waterQualityScore' | 'chlorophyllAProxy' | 'turbidity';

const METRICS: { key: MetricKey; label: string; color: string; axis: 'left' | 'right' }[] = [
  { key: 'waterQualityScore', label: 'Water Quality', color: '#22c55e', axis: 'left' },
  { key: 'bloomRiskScore', label: 'Bloom Risk', color: '#ef4444', axis: 'left' },
  { key: 'eutrophicationRiskScore', label: 'Eutrophication Risk', color: '#f59e0b', axis: 'left' },
  { key: 'chlorophyllAProxy', label: 'Chlorophyll-A (µg/L)', color: '#38bdf8', axis: 'right' },
  { key: 'turbidity', label: 'Turbidity (NTU)', color: '#a78bfa', axis: 'right' },
];

function fmt(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

interface TooltipPayloadItem {
  dataKey: string;
  name: string;
  value: number;
  color: string;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadItem[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-date">{label}</p>
      {payload.map((p) => (
        <div key={p.dataKey} className="chart-tooltip-row">
          <span className="chart-tooltip-dot" style={{ background: p.color }} />
          <span className="chart-tooltip-name">{p.name}</span>
          <span className="chart-tooltip-value">{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </div>
      ))}
    </div>
  );
}

export function Chart({ data }: ChartProps) {
  const [active, setActive] = useState<Set<MetricKey>>(
    new Set(['waterQualityScore', 'bloomRiskScore', 'eutrophicationRiskScore'])
  );

  const chartData = data.map((pt) => ({
    date: fmt(pt.date),
    bloomRiskScore: +pt.bloomRiskScore.toFixed(1),
    eutrophicationRiskScore: +pt.eutrophicationRiskScore.toFixed(1),
    waterQualityScore: +pt.waterQualityScore.toFixed(1),
    chlorophyllAProxy: +pt.chlorophyllAProxy.toFixed(2),
    turbidity: +pt.turbidity.toFixed(2),
  }));

  const hasRight = METRICS.some((m) => m.axis === 'right' && active.has(m.key));

  function toggle(key: MetricKey) {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3 className="chart-title">Time-Series Analysis</h3>
        <div className="chart-toggles">
          {METRICS.map((m) => (
            <button
              key={m.key}
              className={`metric-toggle ${active.has(m.key) ? 'active' : ''}`}
              style={active.has(m.key) ? { borderColor: m.color, color: m.color } : {}}
              onClick={() => toggle(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 5, right: hasRight ? 10 : 0, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#4b5563', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: '#1e293b' }}
            interval={Math.floor(chartData.length / 10)}
          />
          <YAxis
            yAxisId="left"
            domain={[0, 100]}
            tick={{ fill: '#4b5563', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={32}
          />
          {hasRight && (
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: '#4b5563', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={40}
            />
          )}
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ display: 'none' }}
          />
          <ReferenceLine yAxisId="left" y={60} stroke="#ef4444" strokeDasharray="4 4" opacity={0.3} />
          {METRICS.map((m) =>
            active.has(m.key) ? (
              <Line
                key={m.key}
                yAxisId={m.axis}
                type="monotone"
                dataKey={m.key}
                name={m.label}
                stroke={m.color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
            ) : null
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
