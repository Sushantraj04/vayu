import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '@/store/useAppStore';
import { AqiBadge } from '@/components/common/AqiBadge';
import { CorridorMap } from '@/components/Map/CorridorMap';
import { api } from '@/lib/api';
import { 
  Flame, 
  AlertTriangle, 
  Wind, 
  Activity, 
  ShieldAlert, 
  Sparkles, 
  RefreshCw,
  Compass,
  ArrowRight,
  TrendingUp,
  Radio,
  Sliders,
  Bell,
  Clock,
  ExternalLink,
  ChevronRight,
  Target
} from 'lucide-react';

export const SituationRoom: React.FC = () => {
  const { t } = useTranslation();
  const { selectedCity, setSelectedCity, setView } = useAppStore();

  const [stations, setStations] = useState<any[]>([]);
  const [fires, setFires] = useState<any[]>([]);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [attribution, setAttribution] = useState<any | null>(null);
  const [corridorSummary, setCorridorSummary] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [stnRes, firesRes, hsRes, repRes, alertsRes, attrRes, corrRes] = await Promise.allSettled([
        api.getStations(),
        api.getFires(24),
        api.getHotspots('indo-gangetic-main'),
        api.getReports('VERIFIED'),
        api.getAlerts(),
        api.getAttribution(selectedCity),
        api.getCorridorSummary('indo-gangetic-main'),
      ]);

      if (stnRes.status === 'fulfilled') setStations(stnRes.value || []);
      if (firesRes.status === 'fulfilled') setFires(firesRes.value?.fires || []);
      if (hsRes.status === 'fulfilled') setHotspots(hsRes.value || []);
      if (repRes.status === 'fulfilled') setReports(repRes.value || []);
      if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value || []);
      if (attrRes.status === 'fulfilled') setAttribution(attrRes.value || null);
      if (corrRes.status === 'fulfilled') setCorridorSummary(corrRes.value || null);
    } catch (e) {
      console.error('Error loading Situation Room data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCity]);

  const handleDetectHotspots = async () => {
    setActionMessage('Executing DBSCAN Spatio-Temporal Clustering...');
    try {
      const res = await api.detectHotspots(48);
      setActionMessage(`DBSCAN Clustering Complete: ${res.count} active pollution hotspots delineated.`);
      loadData();
    } catch (e: any) {
      setActionMessage(`Failed to execute DBSCAN: ${e.message}`);
    }
  };

  const handleEvaluateAlerts = async () => {
    setActionMessage('Evaluating multi-rule triggers (Sustained AQI, Spikes, Plumes)...');
    try {
      const res = await api.evaluateAlerts();
      setActionMessage(`Multi-Rule Engine Complete: ${res.count} OASIS alerts evaluated.`);
      loadData();
    } catch (e: any) {
      setActionMessage(`Rule evaluation failed: ${e.message}`);
    }
  };

  const corridorNodes = [
    { city: 'Ludhiana', lat: 30.9010, lon: 75.8573, order: 1 },
    { city: 'Ambala', lat: 30.3782, lon: 76.7767, order: 2 },
    { city: 'Delhi-NCR', lat: 28.6139, lon: 77.2090, order: 3 },
    { city: 'Agra', lat: 27.1767, lon: 78.0081, order: 4 },
    { city: 'Kanpur', lat: 26.4499, lon: 80.3319, order: 5 },
    { city: 'Lucknow', lat: 26.8467, lon: 80.9462, order: 6 },
  ];

  const windSpeed = attribution?.meteorology?.wind_speed_kmh || 12.0;
  const windDir = attribution?.meteorology?.wind_direction_deg || 315.0;
  const blh = attribution?.meteorology?.boundary_layer_height_m || 400.0;

  // Approximate transit time from Ludhiana (Punjab) to Delhi (~310 km)
  const transitHours = (310 / Math.max(windSpeed, 5)).toFixed(1);

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-12">
      {/* Tactical Operation Banner */}
      {actionMessage && (
        <div className="p-3.5 rounded-2xl bg-teal-500/15 border border-teal-500/30 text-teal-700 dark:text-teal-300 text-xs flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
            <span className="font-semibold">{actionMessage}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-[11px] font-mono hover:underline cursor-pointer opacity-70 hover:opacity-100"
          >
            DISMISS
          </button>
        </div>
      )}

      {/* Situation Room Header & Command Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/25 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
              <span>EMERGENCY SITUATION ROOM</span>
            </span>
            <span className="text-xs font-mono text-slate-400">CORRIDOR RISK LEVEL: CRITICAL</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2 tracking-tight">
            <span>Indo-Gangetic Airshed Command Center</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Operational fusion of ground reference networks, satellite fire radiometry, and kinematic trans-boundary advection vectors.
          </p>
        </div>

        {/* Command Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleDetectHotspots}
            disabled={isLoading}
            className="px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white border border-slate-700/80 flex items-center gap-2 shadow-sm transition-all cursor-pointer"
          >
            <Flame className="w-3.5 h-3.5 text-rose-400" />
            <span>Run DBSCAN</span>
          </button>

          <button
            onClick={handleEvaluateAlerts}
            disabled={isLoading}
            className="px-3.5 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-500 text-white flex items-center gap-2 shadow-lg shadow-teal-500/20 transition-all cursor-pointer"
          >
            <Bell className="w-3.5 h-3.5" />
            <span>Evaluate Alerts</span>
          </button>

          <button
            onClick={loadData}
            title="Refresh Situation Room"
            className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-all cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-teal-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Top Warning Strip: Trans-boundary Smog Transport Vector */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-teal-950 border border-teal-800/40 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-teal-500/20 text-teal-400 border border-teal-500/30">
            <Wind className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-teal-300 flex items-center gap-2">
              <span>Trans-Boundary Transport Vector</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-teal-500/30 text-teal-200">
                ACTIVE ADVECTION
              </span>
            </div>
            <div className="text-sm font-semibold text-slate-200 mt-0.5">
              Northwest winds ({windSpeed.toFixed(1)} km/h @ {Math.round(windDir)}°) transporting crop residue smoke from Punjab/Haryana toward Delhi-NCR.
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono shrink-0 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
          <div>
            <span className="text-slate-400 block text-[10px]">ESTIMATED TRANSIT TIME</span>
            <span className="text-base font-bold text-amber-400">~{transitHours} Hours</span>
          </div>
          <div className="w-px h-8 bg-slate-800" />
          <div>
            <span className="text-slate-400 block text-[10px]">INVERSION DEPTH</span>
            <span className="text-base font-bold text-teal-300">{Math.round(blh)} Meters</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Corridor Nodes, Interactive Map, and Hotspot Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Corridor Risk & Spine Nodes (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Corridor Risk Index Card */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Corridor Risk Index</span>
              <span className="text-xs font-mono font-bold text-rose-500 bg-rose-500/10 px-2 py-0.5 rounded">
                CRITICAL
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black font-mono text-slate-900 dark:text-white">
                {corridorSummary?.risk_index ?? 84}
              </span>
              <span className="text-xs text-slate-400 font-mono">/ 100</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              Index fused from continuous station anomalies, VIIRS fire count ({fires.length}), and shallow atmospheric mixing.
            </p>
          </div>

          {/* Corridor Spine Navigation */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
              <span>Corridor Spine Stations</span>
              <span className="text-[10px] font-mono text-teal-500">6 NODES</span>
            </div>
            <div className="space-y-1 text-xs">
              {corridorNodes.map((n) => (
                <div
                  key={n.city}
                  onClick={() => setSelectedCity(n.city)}
                  className={`flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all ${
                    selectedCity === n.city
                      ? 'bg-teal-500/15 text-teal-600 dark:text-teal-300 font-bold border border-teal-500/30'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono opacity-50">#{n.order}</span>
                    <span>{n.city}</span>
                  </div>
                  <span className="text-[10px] font-mono opacity-60">{n.lat.toFixed(2)}°N</span>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts Widget */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5 text-rose-500" />
                <span>Active Directives ({alerts.length})</span>
              </span>
              <button
                onClick={() => setView('alerts')}
                className="text-[10px] font-bold text-teal-600 dark:text-teal-400 hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                <span>View All</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            {alerts.slice(0, 2).map((al) => (
              <div
                key={al.id}
                className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-xs space-y-1"
              >
                <div className="font-bold text-slate-900 dark:text-white truncate">{al.title_en}</div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1">
                  <span>Target: {al.city}</span>
                  <span>•</span>
                  <span className="text-rose-500 font-semibold">{al.severity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center: Live Interactive Geospatial Canvas (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <CorridorMap
            stations={stations}
            fires={fires}
            hotspots={hotspots}
            reports={reports}
            corridorNodes={corridorNodes}
            windDirectionDeg={windDir}
            windSpeedKmh={windSpeed}
            selectedCity={selectedCity}
            className="h-[620px]"
          />
        </div>

        {/* Right Column: Kinematic Source Attribution & Hotspots Queue (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Kinematic Source Attribution */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
                <Target className="w-4 h-4 text-teal-500" />
                <span>Source Attribution</span>
              </span>
              <span className="text-[10px] text-teal-600 dark:text-teal-400 font-mono font-bold">
                {attribution?.confidence_pct || 65}% CONF
              </span>
            </div>

            <div className="p-3 rounded-xl bg-teal-500/10 border border-teal-500/20 text-xs text-teal-900 dark:text-teal-200 space-y-1">
              <div className="font-bold text-slate-900 dark:text-white">
                {attribution?.dominant_source || 'Mixed Regional Dispersion'}
              </div>
              <p className="text-[11px] opacity-80 leading-snug">
                {attribution?.plain_language_reasoning || 'Dispersed regional background with upwind transport along the NW corridor.'}
              </p>
            </div>

            {/* Source breakdown bars */}
            <div className="space-y-2 pt-1 text-xs">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-500">Upwind Agricultural Burning:</span>
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">55%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-rose-500 rounded-full" style={{ width: '55%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-500">Local Industrial & Traffic:</span>
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">30%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: '30%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-500">Regional Background:</span>
                  <span className="font-mono font-bold text-slate-700 dark:text-slate-300">15%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-teal-500 rounded-full" style={{ width: '15%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* DBSCAN Hotspots Queue */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-orange-500" />
                <span>Detected Hotspots ({hotspots.length})</span>
              </span>
              <span className="text-[10px] text-teal-600 dark:text-teal-400 font-semibold font-mono">DBSCAN</span>
            </div>

            <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
              {hotspots.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-400">
                  Zero active DBSCAN clusters within current threshold.
                </div>
              ) : (
                hotspots.map((h) => (
                  <div
                    key={h.id}
                    className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 dark:text-white">{h.probable_source}</span>
                      <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-500">
                        {h.severity}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      Radius: {h.radius_km} km | Peak FRP: {h.max_frp_mw} MW
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                      {h.reasoning}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
