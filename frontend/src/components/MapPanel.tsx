import { useEffect } from 'react';
import { MapContainer, TileLayer, Circle, CircleMarker, Popup, LayersControl, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { LakeDto, IndicatorDto } from '../api/api';

// Fix default marker icons broken in bundlers
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({ iconUrl: '', iconRetinaUrl: '', shadowUrl: '' });

function riskColor(wqScore: number): string {
  if (wqScore >= 70) return '#22c55e';
  if (wqScore >= 50) return '#f59e0b';
  return '#ef4444';
}

function alertColor(level: string): string {
  switch (level?.toLowerCase()) {
    case 'critical': return '#dc2626';
    case 'high': return '#ef4444';
    case 'medium': return '#f59e0b';
    default: return '#22c55e';
  }
}

function AutoOpenPopup() {
  const map = useMap();
  useEffect(() => {
    map.eachLayer((layer) => {
      if ((layer as L.CircleMarker).getPopup) {
        const popup = (layer as L.CircleMarker).getPopup();
        if (popup) {
          (layer as L.CircleMarker).openPopup();
        }
      }
    });
  }, [map]);
  return null;
}

interface MapPanelProps {
  lake: LakeDto;
  indicators: IndicatorDto | null;
}

export function MapPanel({ lake, indicators }: MapPanelProps) {
  const center: [number, number] = [lake.latitude, lake.longitude];
  const wqScore = indicators?.waterQualityScore ?? 75;
  const alertLevel = indicators?.alertLevel ?? 'Normal';
  const fillColor = riskColor(wqScore);
  const dotColor = alertColor(alertLevel);

  return (
    <MapContainer
      center={center}
      zoom={13}
      style={{ height: '100%', width: '100%', borderRadius: '12px' }}
      zoomControl={true}
      attributionControl={true}
    >
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Satellite">
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; Esri"
            maxZoom={19}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Dark Map">
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            maxZoom={19}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Terrain">
          <TileLayer
            url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://opentopomap.org">OpenTopoMap</a>'
            maxZoom={17}
          />
        </LayersControl.BaseLayer>
      </LayersControl>

      {/* Monitoring radius overlay */}
      <Circle
        center={center}
        radius={1800}
        color={fillColor}
        fillColor={fillColor}
        fillOpacity={0.12}
        weight={2}
        opacity={0.6}
      />

      {/* Lake marker with popup */}
      <CircleMarker
        center={center}
        radius={10}
        color={dotColor}
        fillColor={dotColor}
        fillOpacity={1}
        weight={3}
      >
        <Popup maxWidth={260} className="riptide-popup">
          <div style={{ fontFamily: 'system-ui, sans-serif', padding: '4px 0' }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 8, color: '#1e293b' }}>
              {lake.name}
            </div>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 10 }}>
              {lake.county}, {lake.country} &middot; {lake.waterBodyType}
            </div>
            {indicators ? (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <tbody>
                  {[
                    ['Water Quality', `${Math.round(indicators.waterQualityScore)} / 100`],
                    ['Bloom Risk', `${Math.round(indicators.bloomRiskScore)} / 100`],
                    ['Eutrophication', `${Math.round(indicators.eutrophicationRiskScore)} / 100`],
                    ['Chlorophyll-A', `${indicators.chlorophyllAProxy.toFixed(2)} µg/L`],
                    ['Turbidity (EO)', `${indicators.turbidity.toFixed(2)} NTU`],
                    ['Surface Temp', `${indicators.surfaceTemperatureCelsius.toFixed(1)} °C`],
                    ['Alert Level', indicators.alertLevel],
                  ].map(([k, v]) => (
                    <tr key={k} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '4px 6px 4px 0', color: '#64748b', whiteSpace: 'nowrap' }}>{k}</td>
                      <td style={{ padding: '4px 0', fontWeight: 600, color: '#1e293b', textAlign: 'right' }}>{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ color: '#94a3b8', fontSize: 12 }}>No indicator data available.</p>
            )}
            <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 8 }}>
              {lake.latitude.toFixed(4)}°N, {lake.longitude.toFixed(4)}°E
            </div>
          </div>
        </Popup>
      </CircleMarker>

      <AutoOpenPopup />
    </MapContainer>
  );
}
