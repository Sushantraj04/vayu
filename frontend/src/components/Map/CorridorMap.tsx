import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Layers, Flame, Radio, ShieldAlert, Wind, MapPin } from 'lucide-react';
import { getAqiColor, getAqiCategory } from '../../lib/aqi';

interface StationItem {
  id: string;
  name: string;
  city: string;
  latitude: number;
  longitude: number;
  data_source: string;
  is_stale: boolean;
  pm25?: number;
  aqi?: number;
  data_origin?: 'MEASURED' | 'MODELLED';
}

interface FireItem {
  id: string;
  latitude: number;
  longitude: number;
  frp_mw: number;
  brightness_temp_k?: number;
  satellite?: string;
  confidence?: string;
}

interface HotspotItem {
  id: string;
  centroid_lat: number;
  centroid_lon: number;
  radius_km: number;
  cluster_size: number;
  severity: string;
  probable_source: string;
  max_frp_mw: number;
  mean_pm25?: number;
  reasoning: string;
}

interface CitizenReportItem {
  public_id: string;
  public_lat: number;
  public_lon: number;
  user_category: string;
  user_pm25?: number;
  is_satellite_verified: boolean;
}

interface CorridorMapProps {
  stations?: StationItem[];
  fires?: FireItem[];
  hotspots?: HotspotItem[];
  reports?: CitizenReportItem[];
  corridorNodes?: { city: string; lat: number; lon: number; order: number }[];
  windDirectionDeg?: number;
  windSpeedKmh?: number;
  selectedCity?: string;
  onSelectStation?: (stationId: string) => void;
  className?: string;
}

export const CorridorMap: React.FC<CorridorMapProps> = ({
  stations = [],
  fires = [],
  hotspots = [],
  reports = [],
  corridorNodes = [],
  windDirectionDeg,
  windSpeedKmh,
  selectedCity,
  onSelectStation,
  className = 'h-[540px]'
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  // Layer groups
  const stationsLayerRef = useRef<L.LayerGroup>(L.layerGroup());
  const firesLayerRef = useRef<L.LayerGroup>(L.layerGroup());
  const hotspotsLayerRef = useRef<L.LayerGroup>(L.layerGroup());
  const reportsLayerRef = useRef<L.LayerGroup>(L.layerGroup());
  const corridorLayerRef = useRef<L.LayerGroup>(L.layerGroup());

  // Visibility state
  const [showStations, setShowStations] = useState(true);
  const [showFires, setShowFires] = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);
  const [showReports, setShowReports] = useState(true);
  const [showCorridor, setShowCorridor] = useState(true);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [28.6139, 77.2090], // Delhi center
      zoom: 7,
      zoomControl: false,
    });

    // Dark cartographic tiles for telemetry situation room
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18,
      subdomains: 'abcd',
    }).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Add layer groups to map
    stationsLayerRef.current.addTo(map);
    firesLayerRef.current.addTo(map);
    hotspotsLayerRef.current.addTo(map);
    reportsLayerRef.current.addTo(map);
    corridorLayerRef.current.addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Stations Layer
  useEffect(() => {
    const layer = stationsLayerRef.current;
    layer.clearLayers();

    if (!showStations) return;

    stations.forEach((stn) => {
      const pm25 = stn.pm25 ?? 95;
      const aqi = stn.aqi ?? Math.round(pm25 * 2.2);
      const color = getAqiColor(aqi);
      const category = getAqiCategory(aqi);
      const origin = stn.data_origin || 'MEASURED';

      const marker = L.circleMarker([stn.latitude, stn.longitude], {
        radius: 9,
        fillColor: color,
        color: '#ffffff',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.85,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; min-width: 180px; padding: 4px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="font-size: 13px; color: #0f172a;">${stn.name}</strong>
            <span style="font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 700; ${
              origin === 'MEASURED' ? 'background: #dcfce7; color: #166534;' : 'background: #fef3c7; color: #92400e;'
            }">${origin}</span>
          </div>
          <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">${stn.city}</div>
          <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;">
            <span style="font-size: 20px; font-weight: 800; color: ${color};">${aqi}</span>
            <span style="font-size: 11px; font-weight: 600; color: ${color};">${category}</span>
          </div>
          <div style="font-size: 11px; color: #475569;">PM2.5: <strong>${pm25} ug/m3</strong></div>
          <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">Source: ${stn.data_source}</div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      if (onSelectStation) {
        marker.on('click', () => onSelectStation(stn.id));
      }
      marker.addTo(layer);
    });
  }, [stations, showStations, onSelectStation]);

  // Update Active Fires Layer
  useEffect(() => {
    const layer = firesLayerRef.current;
    layer.clearLayers();

    if (!showFires) return;

    fires.forEach((fire) => {
      // Radius scaled to FRP
      const radius = Math.min(18, Math.max(4, Math.sqrt(fire.frp_mw) * 0.8));

      const marker = L.circleMarker([fire.latitude, fire.longitude], {
        radius,
        fillColor: '#ef4444',
        color: '#fbbf24',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.75,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; padding: 4px;">
          <div style="color: #ef4444; font-weight: 700; font-size: 12px; display: flex; align-items: center; gap: 4px;">
            🔥 Active Fire (NASA FIRMS VIIRS)
          </div>
          <div style="font-size: 11px; margin-top: 4px;">
            FRP: <strong>${fire.frp_mw.toFixed(1)} MW</strong>
          </div>
          <div style="font-size: 10px; color: #64748b;">
            Bright Temp: ${fire.brightness_temp_k ? `${fire.brightness_temp_k.toFixed(1)} K` : 'N/A'}
          </div>
          <div style="font-size: 10px; color: #94a3b8;">
            Confidence: ${fire.confidence || 'nominal'} | Sat: ${fire.satellite || 'VIIRS'}
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.addTo(layer);
    });
  }, [fires, showFires]);

  // Update Hotspots Layer
  useEffect(() => {
    const layer = hotspotsLayerRef.current;
    layer.clearLayers();

    if (!showHotspots) return;

    hotspots.forEach((h) => {
      const severityColors: Record<string, string> = {
        CRITICAL: '#7f1d1d',
        SEVERE: '#dc2626',
        HIGH: '#ea580c',
        MODERATE: '#d97706',
      };
      const fillColor = severityColors[h.severity] || '#ea580c';

      const circle = L.circle([h.centroid_lat, h.centroid_lon], {
        radius: h.radius_km * 1000,
        fillColor,
        color: fillColor,
        weight: 2,
        opacity: 0.7,
        fillOpacity: 0.25,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; max-width: 240px; padding: 4px;">
          <div style="font-weight: 800; font-size: 12px; color: ${fillColor}; text-transform: uppercase;">
            ⚠️ [${h.severity}] ${h.probable_source}
          </div>
          <div style="font-size: 11px; color: #334155; margin: 4px 0;">
            ${h.reasoning}
          </div>
          <div style="font-size: 10px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 4px;">
            Points: ${h.cluster_size} | Radius: ${h.radius_km} km | Peak FRP: ${h.max_frp_mw} MW
          </div>
        </div>
      `;

      circle.bindPopup(popupHtml);
      circle.addTo(layer);
    });
  }, [hotspots, showHotspots]);

  // Update Citizen Reports Layer
  useEffect(() => {
    const layer = reportsLayerRef.current;
    layer.clearLayers();

    if (!showReports) return;

    reports.forEach((rep) => {
      const marker = L.circleMarker([rep.public_lat, rep.public_lon], {
        radius: 6,
        fillColor: '#38bdf8',
        color: '#0284c7',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.7,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; padding: 4px;">
          <div style="font-size: 11px; font-weight: 700; color: #0284c7;">
            📢 Citizen Report (${rep.public_id})
          </div>
          <div style="font-size: 11px; text-transform: capitalize; margin-top: 2px;">
            ${rep.user_category.replace('_', ' ')}
          </div>
          <div style="font-size: 10px; color: #64748b;">
            Privacy Grid: ~500m cell (${rep.public_lat}, ${rep.public_lon})
          </div>
          ${
            rep.is_satellite_verified
              ? '<div style="font-size: 10px; color: #16a34a; font-weight: 600;">✓ Cross-verified by satellite</div>'
              : ''
          }
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.addTo(layer);
    });
  }, [reports, showReports]);

  // Update Corridor Spine Polyline Layer
  useEffect(() => {
    const layer = corridorLayerRef.current;
    layer.clearLayers();

    if (!showCorridor || corridorNodes.length < 2) return;

    const sortedNodes = [...corridorNodes].sort((a, b) => a.order - b.order);
    const latlngs: [number, number][] = sortedNodes.map((n) => [n.lat, n.lon]);

    // Spine polyline
    const polyline = L.polyline(latlngs, {
      color: '#0d9488',
      weight: 3,
      opacity: 0.7,
      dashArray: '6, 6',
    });
    polyline.addTo(layer);

    // Spine node markers
    sortedNodes.forEach((n) => {
      const nodeMarker = L.circleMarker([n.lat, n.lon], {
        radius: 4,
        fillColor: '#0d9488',
        color: '#ffffff',
        weight: 1,
        fillOpacity: 0.9,
      });
      nodeMarker.bindTooltip(`${n.order}. ${n.city}`, { permanent: false, direction: 'top' });
      nodeMarker.addTo(layer);
    });
  }, [corridorNodes, showCorridor]);

  return (
    <div className={`relative w-full rounded-xl overflow-hidden border border-slate-700/60 shadow-xl ${className}`}>
      {/* Map DOM Container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Floating Layer Control Overlay */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-lg p-3 text-xs shadow-lg text-slate-200">
        <div className="flex items-center gap-1.5 font-semibold text-slate-100 mb-2 border-b border-slate-700/60 pb-1.5">
          <Layers className="w-3.5 h-3.5 text-teal-400" />
          <span>Airshed Layers</span>
        </div>

        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={showStations}
              onChange={(e) => setShowStations(e.target.checked)}
              className="rounded bg-slate-800 border-slate-600 text-teal-500 focus:ring-0 w-3.5 h-3.5"
            />
            <Radio className="w-3 h-3 text-emerald-400" />
            <span>Stations ({stations.length})</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={showFires}
              onChange={(e) => setShowFires(e.target.checked)}
              className="rounded bg-slate-800 border-slate-600 text-red-500 focus:ring-0 w-3.5 h-3.5"
            />
            <Flame className="w-3 h-3 text-red-400" />
            <span>VIIRS Fires ({fires.length})</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={showHotspots}
              onChange={(e) => setShowHotspots(e.target.checked)}
              className="rounded bg-slate-800 border-slate-600 text-amber-500 focus:ring-0 w-3.5 h-3.5"
            />
            <ShieldAlert className="w-3 h-3 text-amber-400" />
            <span>Hotspots ({hotspots.length})</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={showReports}
              onChange={(e) => setShowReports(e.target.checked)}
              className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0 w-3.5 h-3.5"
            />
            <MapPin className="w-3 h-3 text-sky-400" />
            <span>Citizen Reports ({reports.length})</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
            <input
              type="checkbox"
              checked={showCorridor}
              onChange={(e) => setShowCorridor(e.target.checked)}
              className="rounded bg-slate-800 border-slate-600 text-teal-500 focus:ring-0 w-3.5 h-3.5"
            />
            <div className="w-3 h-0.5 border-b border-dashed border-teal-400" />
            <span>Corridor Spine</span>
          </label>
        </div>

        {/* Ambient Wind Vector Display */}
        {windSpeedKmh !== undefined && windDirectionDeg !== undefined && (
          <div className="mt-2.5 pt-2 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-300">
            <div className="flex items-center gap-1 text-slate-400">
              <Wind className="w-3 h-3 text-teal-400" />
              <span>Wind:</span>
            </div>
            <div className="font-mono font-semibold text-teal-300 flex items-center gap-1">
              <span>{windSpeedKmh.toFixed(1)} km/h</span>
              <span
                className="inline-block transform"
                style={{ transform: `rotate(${windDirectionDeg}deg)` }}
                title={`Wind direction: ${windDirectionDeg}°`}
              >
                ↓
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
