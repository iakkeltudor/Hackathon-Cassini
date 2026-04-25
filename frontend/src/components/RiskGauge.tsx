interface RiskGaugeProps {
  label: string;
  score: number;
  inverted?: boolean;
  sublabel?: string;
}

function gaugeColor(score: number, inverted: boolean): string {
  const risk = inverted ? 100 - score : score;
  if (risk >= 70) return '#ef4444';
  if (risk >= 40) return '#f59e0b';
  return '#22c55e';
}

export function RiskGauge({ label, score, inverted = false, sublabel }: RiskGaugeProps) {
  const r = 48;
  const cx = 60;
  const cy = 60;
  const sw = 9;
  const circ = 2 * Math.PI * r;
  const track = 0.75 * circ;
  const fill = Math.min(1, Math.max(0, score / 100)) * track;
  const color = gaugeColor(score, inverted);

  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 120 112" width="120" height="110">
        <circle
          cx={cx} cy={cy} r={r}
          fill="none" stroke="#1e293b" strokeWidth={sw}
          strokeDasharray={`${track} ${circ - track}`}
          strokeLinecap="round"
          transform={`rotate(135 ${cx} ${cy})`}
        />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none" stroke={color} strokeWidth={sw}
          strokeDasharray={`${fill} ${circ - fill}`}
          strokeLinecap="round"
          transform={`rotate(135 ${cx} ${cy})`}
          style={{ transition: 'stroke-dasharray 0.9s ease-out, stroke 0.5s ease' }}
        />
        <text x={cx} y={cy + 2} textAnchor="middle" dominantBaseline="middle"
          fill={color} fontSize="22" fontWeight="700" fontFamily="monospace">
          {Math.round(score)}
        </text>
        <text x={cx} y={cy + 18} textAnchor="middle"
          fill="#4b5563" fontSize="10">
          / 100
        </text>
      </svg>
      <p className="gauge-label">{label}</p>
      {sublabel && <p className="gauge-sublabel">{sublabel}</p>}
    </div>
  );
}
