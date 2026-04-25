const API_BASE = (import.meta.env as Record<string, string>)['VITE_API_URL'] ?? 'http://localhost:5093';

export interface LakeDto {
  id: string;
  name: string;
  county: string;
  country: string;
  waterBodyType: string;
  latitude: number;
  longitude: number;
  description: string;
}

export interface IndicatorDto {
  date: string;
  chlorophyllAProxy: number;
  turbidity: number;
  totalSuspendedMatterProxy: number;
  surfaceTemperatureCelsius: number;
  studyTurbidityNtu: number | null;
  predictedInSituTurbidity: number;
  nitrateMgL: number | null;
  nitriteMgL: number | null;
  ammoniumMgL: number | null;
  nutrientPressureIndex: number;
  bloomRiskScore: number;
  eutrophicationRiskScore: number;
  waterQualityScore: number;
  alertLevel: string;
  isStudyActual: boolean;
  isEoActual: boolean;
}

export interface TimeseriesPointDto {
  date: string;
  chlorophyllAProxy: number;
  turbidity: number;
  totalSuspendedMatterProxy: number;
  surfaceTemperatureCelsius: number;
  bloomRiskScore: number;
  eutrophicationRiskScore: number;
  waterQualityScore: number;
  predictedInSituTurbidity: number;
  alertLevel: string;
}

export interface RiskSummaryDto {
  lakeId: string;
  lakeName: string;
  calculatedAtUtc: string;
  bloomRiskScore: number;
  eutrophicationRiskScore: number;
  waterQualityScore: number;
  riskLevel: string;
  explanation: string;
}

export interface AlertDto {
  id: string;
  date: string;
  severity: string;
  parameter: string;
  message: string;
  value: number;
  threshold: number;
  isAcknowledged: boolean;
}

export interface LayerDto {
  id: string;
  name: string;
  layerType: string;
  capturedAtUtc: string;
  sourceFile: string;
  format: string;
  minValue: number;
  maxValue: number;
  isMock: boolean;
}

export interface DashboardDto {
  lake: LakeDto;
  latestIndicators: IndicatorDto | null;
  riskSummary: RiskSummaryDto | null;
  timeseries: TimeseriesPointDto[];
  alerts: AlertDto[];
  layers: LayerDto[];
}

export async function fetchDashboard(): Promise<DashboardDto> {
  const res = await fetch(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<DashboardDto>;
}
