import type { IndicatorDto } from '../api/api';

interface Indicator {
  label: string;
  value: string;
  unit?: string;
  sub?: string;
}

function buildIndicators(d: IndicatorDto): Indicator[] {
  return [
    { label: 'Chlorophyll-A', value: d.chlorophyllAProxy.toFixed(2), unit: 'µg/L', sub: 'EO proxy' },
    { label: 'Turbidity', value: d.turbidity.toFixed(2), unit: 'NTU', sub: 'EO proxy' },
    { label: 'Surface Temp', value: d.surfaceTemperatureCelsius.toFixed(1), unit: '°C', sub: 'EO proxy' },
    { label: 'Total Susp. Matter', value: d.totalSuspendedMatterProxy.toFixed(2), unit: 'g/m³', sub: 'EO proxy' },
    { label: 'Nutrient Pressure', value: d.nutrientPressureIndex.toFixed(3), unit: 'idx', sub: 'Normalized' },
    { label: 'Pred. Turbidity', value: d.predictedInSituTurbidity.toFixed(2), unit: 'NTU', sub: 'ML estimate' },
    ...(d.nitrateMgL != null ? [{ label: 'Nitrate', value: d.nitrateMgL.toFixed(2), unit: 'mg/L', sub: 'In-situ' }] : []),
    ...(d.ammoniumMgL != null ? [{ label: 'Ammonium', value: d.ammoniumMgL.toFixed(2), unit: 'mg/L', sub: 'In-situ' }] : []),
  ];
}

interface IndicatorsGridProps {
  indicators: IndicatorDto | null;
}

export function IndicatorsGrid({ indicators }: IndicatorsGridProps) {
  const fmtDate = (s: string) =>
    new Date(s).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="panel">
      <h3 className="panel-title">
        Current Indicators
        {indicators && (
          <span className="panel-date">{fmtDate(indicators.date)}</span>
        )}
      </h3>
      {indicators ? (
        <div className="indicators-grid">
          {buildIndicators(indicators).map((ind) => (
            <div key={ind.label} className="indicator-card">
              <p className="indicator-label">{ind.label}</p>
              <p className="indicator-value">
                {ind.value}
                {ind.unit && <span className="indicator-unit">{ind.unit}</span>}
              </p>
              {ind.sub && <p className="indicator-sub">{ind.sub}</p>}
            </div>
          ))}
        </div>
      ) : (
        <p className="no-data">No indicator data available</p>
      )}
    </div>
  );
}
