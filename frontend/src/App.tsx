import { useCallback, useEffect, useState } from 'react';
import { fetchDashboard, type DashboardDto } from './api/api';
import { RiskGauge } from './components/RiskGauge';
import { MapPanel } from './components/MapPanel';
import { Chart } from './components/Chart';
import { AlertsPanel } from './components/AlertsPanel';
import { IndicatorsGrid } from './components/IndicatorsGrid';
import './App.css';

const POLL_INTERVAL_MS = 60_000;

function alertLevelBadgeClass(level: string) {
  switch (level?.toLowerCase()) {
    case 'critical': return 'status-critical';
    case 'high': return 'status-high';
    case 'medium': return 'status-medium';
    case 'low': return 'status-low';
    default: return 'status-normal';
  }
}

export default function App() {
  const [data, setData] = useState<DashboardDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const dash = await fetchDashboard();
      setData(dash);
      setError(null);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load]);

  const lake = data?.lake;
  const indicators = data?.latestIndicators ?? null;
  const riskSummary = data?.riskSummary ?? null;
  const alertLevel = riskSummary?.riskLevel ?? indicators?.alertLevel ?? 'Normal';

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">Riptide</span>
          </div>
          <div className="header-divider" />
          <div className="header-lake">
            {lake ? (
              <>
                <span className="lake-name">{lake.name}</span>
                <span className="lake-meta">{lake.county}, {lake.country}</span>
              </>
            ) : (
              <span className="lake-name">Loading…</span>
            )}
          </div>
        </div>
        <div className="header-right">
          {!loading && !error && (
            <span className={`status-badge ${alertLevelBadgeClass(alertLevel)}`}>
              {alertLevel}
            </span>
          )}
          {lastUpdated && (
            <span className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button className="refresh-btn" onClick={load} title="Refresh">↺</button>
        </div>
      </header>

      {/* ── Error banner ── */}
      {error && (
        <div className="error-banner">
          <span>⚠ {error}</span>
          <button onClick={load}>Retry</button>
        </div>
      )}

      {/* ── Explanation ── */}
      {riskSummary?.explanation && (
        <div className="explanation-bar">
          <span className="explanation-icon">ℹ</span>
          {riskSummary.explanation}
        </div>
      )}

      <main className="main">
        {/* ── Gauges row ── */}
        <section className="gauges-row">
          <div className="gauge-card">
            <RiskGauge
              label="Water Quality Index"
              score={riskSummary?.waterQualityScore ?? indicators?.waterQualityScore ?? 0}
              inverted
              sublabel="Higher = better"
            />
          </div>
          <div className="gauge-card">
            <RiskGauge
              label="Bloom Risk"
              score={riskSummary?.bloomRiskScore ?? indicators?.bloomRiskScore ?? 0}
              sublabel="Algal bloom potential"
            />
          </div>
          <div className="gauge-card">
            <RiskGauge
              label="Eutrophication Risk"
              score={riskSummary?.eutrophicationRiskScore ?? indicators?.eutrophicationRiskScore ?? 0}
              sublabel="Nutrient pressure"
            />
          </div>
        </section>

        {/* ── Middle row: map + side panel ── */}
        <section className="middle-row">
          <div className="map-card">
            {loading ? (
              <div className="map-placeholder">
                <div className="spinner" />
                <p>Loading map…</p>
              </div>
            ) : lake ? (
              <MapPanel lake={lake} indicators={indicators} />
            ) : (
              <div className="map-placeholder"><p>No lake data</p></div>
            )}
          </div>

          <div className="side-panel">
            <IndicatorsGrid indicators={indicators} />
            <AlertsPanel alerts={data?.alerts ?? []} />
          </div>
        </section>

        {/* ── Chart ── */}
        {data && data.timeseries.length > 0 && (
          <section>
            <Chart data={data.timeseries} />
          </section>
        )}
      </main>

      <footer className="footer">
        <span>Riptide Water Quality Monitor &mdash; Pilot: Lacul Tarnița</span>
        <span>Data: Sentinel-2 EO proxies + in-situ sampling &mdash; ML: Random Forest turbidity prediction</span>
      </footer>
    </div>
  );
}
