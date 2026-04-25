import type { AlertDto } from '../api/api';

function severityClass(s: string) {
  switch (s?.toLowerCase()) {
    case 'critical': return 'critical';
    case 'high': return 'high';
    case 'medium': return 'medium';
    default: return 'low';
  }
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: '2-digit' });
}

interface AlertsPanelProps {
  alerts: AlertDto[];
}

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  const sorted = [...alerts].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return (order[a.severity.toLowerCase() as keyof typeof order] ?? 3)
      - (order[b.severity.toLowerCase() as keyof typeof order] ?? 3);
  }).slice(0, 12);

  return (
    <div className="panel">
      <h3 className="panel-title">
        Active Alerts
        {alerts.length > 0 && <span className="alert-count">{alerts.length}</span>}
      </h3>
      {sorted.length === 0 ? (
        <div className="no-alerts">
          <span className="no-alerts-icon">✓</span>
          <p>All parameters within normal range</p>
        </div>
      ) : (
        <ul className="alerts-list">
          {sorted.map((a) => {
            const cls = severityClass(a.severity);
            return (
              <li key={a.id} className={`alert-item severity-${cls}`}>
                <div className="alert-top">
                  <span className={`severity-badge ${cls}`}>{a.severity}</span>
                  <span className="alert-param">{a.parameter}</span>
                  <span className="alert-date">{fmtDate(a.date)}</span>
                </div>
                <p className="alert-msg">{a.message}</p>
                <div className="alert-meta">
                  <span>Value: <strong>{a.value.toFixed(1)}</strong></span>
                  <span>Threshold: <strong>{a.threshold}</strong></span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
