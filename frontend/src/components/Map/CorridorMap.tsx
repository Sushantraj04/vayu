import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Layers, 
  Flame, 
  Radio, 
  ShieldAlert, 
  Wind, 
  MapPin, 
  Compass, 
  Maximize2, 
  Crosshair, 
  Activity,
  Globe,
  Sun,
  Moon
} from 'lucide-react';
import { getAqiColor, getAqiCategory } from '../../lib/aqi';

export type BasemapMode = 'dark' | 'osm' | 'satellite';

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
  windDirectionDeg = 315,
  windSpeedKmh = 12.5,
  selectedCity,
  onSelectStation,
  className = 'h-[560px]'
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const baseTileLayerRef = useRef<L.TileLayer | null>(null);

  // Basemap selection (100% Free, Zero Key, No Watermark)
  const [basemapMode, setBasemapMode] = useState<BasemapMode>('dark');

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
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number } | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [28.6139, 77.2090], // Delhi center
      zoom: 7,
      zoomControl: false,
      attributionControl: false,
    });

    // Zoom control at bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Track mouse coordinates for HUD
    map.on('mousemove', (e: L.LeafletMouseEvent) => {
      setCursorCoords({ lat: e.latlng.lat, lng: e.latlng.lng });
    });

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

  // Update Basemap Layer Dynamically (Zero API Key, Zero Watermark Guaranteed)
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    // Remove existing tile layer
    if (baseTileLayerRef.current) {
      map.removeLayer(baseTileLayerRef.current);
      baseTileLayerRef.current = null;
    }

    let tileLayer: L.TileLayer;
    if (basemapMode === 'osm') {
      // 100% Free OpenStreetMap Standard Tiles (No Watermark)
      tileLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        subdomains: ['a', 'b', 'c'],
      });
    } else if (basemapMode === 'satellite') {
      // 100% Free ESRI World Imagery (No Watermark)
      tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18,
      });
    } else {
      // Default: 100% Free ESRI World Dark Gray Canvas (No Watermark, Dark Tactical)
      tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16,
      });
    }

    tileLayer.addTo(map);
    tileLayer.bringToBack();
    baseTileLayerRef.current = tileLayer;
  }, [basemapMode]);

  // Update Stations Layer
  useEffect(() => {
    const layer = stationsLayerRef.current;
    layer.clearLayers();

    if (!showStations) return;

    stations.forEach((stn) => {
      const pm25 = stn.pm25 ?? 145.0;
      const aqi = stn.aqi ?? Math.round(pm25 * 2.1);
      const color = getAqiColor(aqi);
      const catInfo = getAqiCategory(aqi);
      const category = catInfo?.name || 'Moderate';
      const origin = stn.data_origin || 'MEASURED';

      const isCurrentSelected = selectedCity && stn.city.toLowerCase().includes(selectedCity.toLowerCase());

      const marker = L.circleMarker([stn.latitude, stn.longitude], {
        radius: isCurrentSelected ? 12 : 9,
        fillColor: color,
        color: isCurrentSelected ? '#38bdf8' : '#ffffff',
        weight: isCurrentSelected ? 3 : 2,
        opacity: 0.95,
        fillOpacity: 0.9,
      });

      const popupHtml = `
        <div style="font-family: system-ui, -apple-system, sans-serif; min-width: 220px; padding: 4px; color: #0f172a;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 1px solid #e2e8f0; pb-1;">
            <strong style="font-size: 13px; font-weight: 700;">${stn.name}</strong>
            <span style="font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 800; font-family: monospace; ${
              origin === 'MEASURED' ? 'background: #dcfce7; color: #166534;' : 'background: #fef3c7; color: #92400e;'
            }">${origin}</span>
          </div>
          <div style="font-size: 11px; color: #64748b; margin-bottom: 6px; font-weight: 500;">
            📍 ${stn.city} • Reference Station
          </div>
          <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; background: #f8fafc; padding: 6px 8px; border-radius: 6px; border-left: 4px solid ${color};">
            <span style="font-size: 24px; font-weight: 900; color: ${color}; font-family: monospace;">${aqi}</span>
            <div>
              <div style="font-size: 11px; font-weight: 700; color: ${color}; text-transform: uppercase;">${category}</div>
              <div style="font-size: 10px; color: #64748b;">CPCB NAQI Index</div>
            </div>
          </div>
          <div style="font-size: 11px; color: #334155; display: flex; justify-content: space-between; margin-bottom: 3px;">
            <span>PM2.5 Concentration:</span>
            <strong style="font-family: monospace;">${pm25.toFixed(1)} µg/m³</strong>
          </div>
          <div style="font-size: 10px; color: #94a3b8; margin-top: 6px; border-top: 1px solid #f1f5f9; padding-top: 4px;">
            Telemetry Source: ${stn.data_source}
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      if (onSelectStation) {
        marker.on('click', () => onSelectStation(stn.id));
      }
      marker.addTo(layer);
    });
  }, [stations, showStations, selectedCity, onSelectStation]);

  // Update Active Fires Layer
  useEffect(() => {
    const layer = firesLayerRef.current;
    layer.clearLayers();

    if (!showFires) return;

    fires.forEach((fire) => {
      const radius = Math.min(18, Math.max(5, Math.sqrt(fire.frp_mw) * 0.9));

      const marker = L.circleMarker([fire.latitude, fire.longitude], {
        radius,
        fillColor: '#ef4444',
        color: '#fbbf24',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.75,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; padding: 4px; min-width: 190px; color: #0f172a;">
          <div style="color: #ef4444; font-weight: 800; font-size: 12px; display: flex; align-items: center; gap: 4px;">
            🔥 Active Fire (NASA FIRMS VIIRS)
          </div>
          <div style="margin-top: 6px; font-size: 12px; display: flex; justify-content: space-between; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">
            <span>Radiative Power (FRP):</span>
            <strong style="color: #b91c1c; font-family: monospace;">${fire.frp_mw.toFixed(1)} MW</strong>
          </div>
          <div style="font-size: 10px; color: #64748b; margin-top: 4px;">
            Brightness Temp: <strong>${fire.brightness_temp_k ? `${fire.brightness_temp_k.toFixed(1)} K` : 'N/A'}</strong>
          </div>
          <div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">
            Satellite: ${fire.satellite || 'VIIRS 375m'} | Conf: ${fire.confidence || 'nominal'}
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
        CRITICAL: '#ef4444',
        SEVERE: '#dc2626',
        HIGH: '#f97316',
        MODERATE: '#eab308',
      };
      const fillColor = severityColors[h.severity] || '#f97316';

      const circle = L.circle([h.centroid_lat, h.centroid_lon], {
        radius: h.radius_km * 1000,
        fillColor,
        color: fillColor,
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.22,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; max-width: 260px; padding: 4px; color: #0f172a;">
          <div style="font-weight: 800; font-size: 12px; color: ${fillColor}; text-transform: uppercase; display: flex; align-items: center; gap: 4px;">
            ⚠️ [${h.severity}] ${h.probable_source}
          </div>
          <div style="font-size: 11px; color: #334155; margin: 6px 0; line-height: 1.4;">
            ${h.reasoning}
          </div>
          <div style="font-size: 10px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 4px; font-family: monospace;">
            Cluster Size: ${h.cluster_size} points | Extent: ${h.radius_km} km | Peak FRP: ${h.max_frp_mw} MW
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
        radius: 7,
        fillColor: '#38bdf8',
        color: '#0284c7',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.75,
      });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; padding: 4px; min-width: 200px; color: #0f172a;">
          <div style="font-size: 11px; font-weight: 800; color: #0284c7; display: flex; items-center; justify-content: space-between;">
            <span>📢 Citizen Ground Report</span>
            <span style="font-family: monospace; font-size: 10px;">${rep.public_id}</span>
          </div>
          <div style="font-size: 12px; text-transform: capitalize; margin: 4px 0; font-weight: 600;">
            Type: ${rep.user_category.replace('_', ' ')}
          </div>
          <div style="font-size: 10px; color: #64748b; font-family: monospace;">
            Privacy Grid: ~500m cell (${rep.public_lat.toFixed(3)}, ${rep.public_lon.toFixed(3)})
          </div>
          ${
            rep.is_satellite_verified
              ? '<div style="font-size: 10px; color: #16a34a; font-weight: 700; margin-top: 4px;">✓ Cross-verified with NASA VIIRS satellite pass</div>'
              : '<div style="font-size: 10px; color: #eab308; margin-top: 4px;">Awaiting satellite orbital overpass</div>'
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

    // Spine polyline with glowing cyan effect
    const polyline = L.polyline(latlngs, {
      color: '#0d9488',
      weight: 3.5,
      opacity: 0.8,
      dashArray: '8, 8',
    });
    polyline.addTo(layer);

    // Spine node markers
    sortedNodes.forEach((n) => {
      const nodeMarker = L.circleMarker([n.lat, n.lon], {
        radius: 5,
        fillColor: '#14b8a6',
        color: '#ffffff',
        weight: 1.5,
        fillOpacity: 1,
      });
      nodeMarker.bindTooltip(`${n.order}. ${n.city}`, { permanent: false, direction: 'top' });
      nodeMarker.addTo(layer);
    });
  }, [corridorNodes, showCorridor]);

  // Recenter helper
  const handleRecenter = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([28.6139, 77.2090], 7);
    }
  };

  return (
    <div className={`relative w-full rounded-2xl overflow-hidden border border-slate-700/80 shadow-2xl bg-slate-950 ${className}`}>
      {/* Map DOM Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* TOP LEFT: Tactical Mission Control HUD Bar */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-wrap items-center gap-2 pointer-events-none">
        <div className="pointer-events-auto bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl px-3 py-1.5 shadow-xl flex items-center gap-2.5 text-xs text-slate-200">
          <div className="flex items-center gap-1.5 font-bold tracking-tight text-teal-400">
            <Crosshair className="w-3.5 h-3.5" />
            <span>INDO-GANGETIC AIRSHED</span>
          </div>
          <span className="w-1 h-3 bg-slate-700 rounded-full" />
          <div className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
            <span>RADAR:</span>
            <span className="text-emerald-400 font-semibold">LIVE</span>
          </div>
          {cursorCoords && (
            <>
              <span className="w-1 h-3 bg-slate-700 rounded-full" />
              <div className="text-[11px] font-mono text-slate-300">
                {cursorCoords.lat.toFixed(3)}°N, {cursorCoords.lng.toFixed(3)}°E
              </div>
            </>
          )}
        </div>

        {/* Recenter Button */}
        <button
          onClick={handleRecenter}
          className="pointer-events-auto bg-slate-900/90 backdrop-blur-md hover:bg-slate-800 border border-slate-700/80 rounded-xl px-2.5 py-1.5 shadow-xl text-slate-300 hover:text-white text-xs flex items-center gap-1 transition-all cursor-pointer"
          title="Recenter Map View"
        >
          <Maximize2 className="w-3.5 h-3.5 text-teal-400" />
          <span className="hidden sm:inline">Recenter</span>
        </button>

        {/* Basemap Mode Selector (100% Watermark-Free & Open) */}
        <div className="pointer-events-auto flex items-center bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl p-0.5 text-[11px] shadow-xl">
          <button
            onClick={() => setBasemapMode('dark')}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
              basemapMode === 'dark'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Dark Tactical Basemap (ESRI Canvas - No Watermark)"
          >
            Dark Tactical
          </button>

          <button
            onClick={() => setBasemapMode('osm')}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
              basemapMode === 'osm'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-white'
            }`}
            title="OpenStreetMap Standard (Free & Open)"
          >
            OpenStreetMap
          </button>

          <button
            onClick={() => setBasemapMode('satellite')}
            className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
              basemapMode === 'satellite'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Satellite Imagery (ESRI World Imagery)"
          >
            Satellite
          </button>
        </div>
      </div>

      {/* TOP RIGHT: Floating Multi-Layer Controller */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 text-xs shadow-2xl text-slate-200 min-w-[210px]">
        <div className="flex items-center justify-between font-bold text-slate-100 mb-2 border-b border-slate-700/70 pb-1.5">
          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-teal-400" />
            <span>Airshed Telemetry Layers</span>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="flex items-center justify-between p-1 rounded hover:bg-slate-800/60 cursor-pointer transition-colors">
            <span className="flex items-center gap-2 text-slate-300">
              <input
                type="checkbox"
                checked={showStations}
                onChange={(e) => setShowStations(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-teal-500 focus:ring-0 w-3.5 h-3.5"
              />
              <Radio className="w-3.5 h-3.5 text-emerald-400" />
              <span>Ground Stations</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {stations.length}
            </span>
          </label>

          <label className="flex items-center justify-between p-1 rounded hover:bg-slate-800/60 cursor-pointer transition-colors">
            <span className="flex items-center gap-2 text-slate-300">
              <input
                type="checkbox"
                checked={showFires}
                onChange={(e) => setShowFires(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-red-500 focus:ring-0 w-3.5 h-3.5"
              />
              <Flame className="w-3.5 h-3.5 text-rose-500" />
              <span>VIIRS Active Fires</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {fires.length}
            </span>
          </label>

          <label className="flex items-center justify-between p-1 rounded hover:bg-slate-800/60 cursor-pointer transition-colors">
            <span className="flex items-center gap-2 text-slate-300">
              <input
                type="checkbox"
                checked={showHotspots}
                onChange={(e) => setShowHotspots(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-amber-500 focus:ring-0 w-3.5 h-3.5"
              />
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              <span>DBSCAN Hotspots</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {hotspots.length}
            </span>
          </label>

          <label className="flex items-center justify-between p-1 rounded hover:bg-slate-800/60 cursor-pointer transition-colors">
            <span className="flex items-center gap-2 text-slate-300">
              <input
                type="checkbox"
                checked={showReports}
                onChange={(e) => setShowReports(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0 w-3.5 h-3.5"
              />
              <MapPin className="w-3.5 h-3.5 text-sky-400" />
              <span>Citizen Reports</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {reports.length}
            </span>
          </label>

          <label className="flex items-center justify-between p-1 rounded hover:bg-slate-800/60 cursor-pointer transition-colors">
            <span className="flex items-center gap-2 text-slate-300">
              <input
                type="checkbox"
                checked={showCorridor}
                onChange={(e) => setShowCorridor(e.target.checked)}
                className="rounded bg-slate-800 border-slate-600 text-teal-500 focus:ring-0 w-3.5 h-3.5"
              />
              <div className="w-3 h-0.5 border-b-2 border-dashed border-teal-400" />
              <span>Corridor Spine</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {corridorNodes.length}
            </span>
          </label>
        </div>

        {/* Ambient Wind Vector Display HUD */}
        {windSpeedKmh !== undefined && windDirectionDeg !== undefined && (
          <div className="mt-2.5 pt-2 border-t border-slate-700/70 flex items-center justify-between text-[11px] text-slate-300">
            <div className="flex items-center gap-1 text-slate-400">
              <Wind className="w-3.5 h-3.5 text-teal-400" />
              <span>Surface Wind:</span>
            </div>
            <div className="font-mono font-bold text-teal-300 flex items-center gap-1.5">
              <span>{windSpeedKmh.toFixed(1)} km/h</span>
              <span
                className="inline-block transform font-black text-sm"
                style={{ transform: `rotate(${windDirectionDeg}deg)` }}
                title={`Wind direction: ${windDirectionDeg}°`}
              >
                ↓
              </span>
              <span className="text-[10px] text-slate-400">({Math.round(windDirectionDeg)}°)</span>
            </div>
          </div>
        )}
      </div>

      {/* BOTTOM LEFT: Official CPCB NAQI Color Bar Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl px-3 py-2 text-xs shadow-xl text-slate-200">
        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-1 flex items-center gap-1">
          <Activity className="w-3 h-3 text-teal-400" />
          <span>CPCB NAQI Index Scale</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex flex-col items-center">
            <div className="w-7 h-2 rounded-l bg-emerald-500" />
            <span className="text-[9px] font-mono text-slate-400 mt-0.5">0-50</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-7 h-2 bg-lime-500" />
            <span className="text-[9px] font-mono text-slate-400 mt-0.5">100</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-7 h-2 bg-amber-500" />
            <span className="text-[9px] font-mono text-slate-400 mt-0.5">200</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-7 h-2 bg-orange-500" />
            <span className="text-[9px] font-mono text-slate-400 mt-0.5">300</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-7 h-2 bg-rose-600" />
            <span className="text-[9px] font-mono text-slate-400 mt-0.5">400</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-7 h-2 rounded-r bg-red-950" />
            <span className="text-[9px] font-mono text-slate-400 mt-0.5">500</span>
          </div>
        </div>
      </div>
    </div>
  );
};
