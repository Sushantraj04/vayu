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
  Radio
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
    setActionMessage('Running DBSCAN Spatio-temporal Clustering...');
    try {
      const res = await api.detectHotspots(48);
      setActionMessage(`DBSCAN Complete: ${res.count} active hotspots detected.`);
      loadData();
    } catch (e: any) {
      setActionMessage(`Failed to run DBSCAN: ${e.message}`);
    }
  };

  const handleEvaluateAlerts = async () => {
    setActionMessage('Evaluating multi-rule triggers (Sustained AQI, Spikes, Plumes)...');
    try {
      const res = await api.evaluateAlerts();
      setActionMessage(`Rule Engine Complete: ${res.count} alerts dispatched.`);
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

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* Action Notification Banner */}
      {actionMessage && (
        <div className="p-3 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs flex items-center justify-between">
          <span className="font-mono">{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* 1. TOP KPI STRIP */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Corridor Risk Index */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>{t('situation_room.corridor_risk_index')}</span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold">
              CRITICAL
            </span>
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold font-mono text-rose-600 dark:text-rose-400">
              {corridorSummary?.risk_index ?? 78.4}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ 100</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-rose-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${corridorSummary?.risk_index ?? 78.4}%` }}
            ></div>
          </div>
        </div>

        {/* Active Emergency Alerts */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Active CAP 1.2 Alerts</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
              {alerts.length}
            </span>
            <span className="text-xs text-amber-600 font-medium">ITU-T X.1303</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 truncate">
            {alerts[0]?.title_en || 'Trans-boundary advisory active'}
          </p>
        </div>

        {/* Active Fires (VIIRS) */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>{t('situation_room.active_fires')}</span>
            <Flame className="w-3.5 h-3.5 text-orange-500" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold font-mono text-orange-600 dark:text-orange-400">
              {fires.length}
            </span>
            <span className="text-xs text-slate-400 font-mono">NASA FIRMS 375m</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 truncate">
            Crop burning radiometry in Punjab/Haryana
          </p>
        </div>

        {/* Selected Airshed Focus */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Receptor City Focus</span>
            <Activity className="w-3.5 h-3.5 text-teal-500" />
          </div>
          <div className="flex items-center justify-between mt-2">
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="text-base font-bold bg-transparent text-slate-900 dark:text-white focus:outline-none cursor-pointer"
            >
              {corridorNodes.map((n) => (
                <option key={n.city} value={n.city} className="bg-slate-900 text-white">
                  {n.city}
                </option>
              ))}
            </select>
            <AqiBadge aqi={320} size="sm" />
          </div>
          <p className="text-[11px] text-slate-400 mt-1 truncate">
            Indo-Gangetic Airshed Hub Node
          </p>
        </div>
      </div>

      {/* 2. MAIN SITUATION ROOM CANVAS (MAP + CONTROLS + HOTSPOTS) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left: Operational Analytics & Triggers */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span>Operational Control</span>
              </span>
              <button onClick={loadData} title="Refresh Live Data" className="text-slate-400 hover:text-white">
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-teal-400' : ''}`} />
              </button>
            </div>

            {/* AI Operational Triggers */}
            <div className="space-y-2">
              <button
                onClick={handleDetectHotspots}
                className="w-full py-2.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center justify-between transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Flame className="w-3.5 h-3.5 text-orange-400" />
                  <span>Run DBSCAN Clustering</span>
                </div>
                <ArrowRight className="w-3 h-3 text-slate-400" />
              </button>

              <button
                onClick={handleEvaluateAlerts}
                className="w-full py-2.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center justify-between transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Evaluate Alert Triggers</span>
                </div>
                <ArrowRight className="w-3 h-3 text-slate-400" />
              </button>

              <button
                onClick={() => setView('alerts')}
                className="w-full py-2.5 px-3 rounded-lg bg-teal-600/10 hover:bg-teal-600/20 text-teal-300 border border-teal-500/30 text-xs font-semibold flex items-center justify-between transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Radio className="w-3.5 h-3.5 text-teal-400" />
                  <span>CAP 1.2 Feed & Sirens</span>
                </div>
                <ArrowRight className="w-3 h-3 text-teal-400" />
              </button>
            </div>

            {/* Corridor Spine Sequence */}
            <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-2">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Spine Node Trajectory
              </div>
              <div className="space-y-1 text-xs">
                {corridorNodes.map((n) => (
                  <div
                    key={n.city}
                    onClick={() => setSelectedCity(n.city)}
                    className={`flex items-center justify-between p-1.5 rounded cursor-pointer transition-colors ${
                      selectedCity === n.city ? 'bg-teal-500/20 text-teal-300 font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <span>{n.order}. {n.city}</span>
                    <span className="text-[10px] font-mono opacity-60">{n.lat.toFixed(2)}°N</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800/80 text-xs space-y-1.5">
            <div className="font-semibold text-teal-900 dark:text-teal-300 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Trans-boundary Airshed Directive</span>
            </div>
            <p className="text-[11px] text-teal-800/80 dark:text-teal-300/80 leading-snug">
              Coordinated cross-state action required: Crop residue curbs in Sangrur/Patiala directly mitigate 48h PM2.5 surge in Delhi-NCR.
            </p>
          </div>
        </div>

        {/* Center: Live Interactive Corridor Map */}
        <div className="lg:col-span-2">
          <CorridorMap
            stations={stations}
            fires={fires}
            hotspots={hotspots}
            reports={reports}
            corridorNodes={corridorNodes}
            windDirectionDeg={attribution?.meteorology?.wind_direction_deg || 315}
            windSpeedKmh={attribution?.meteorology?.wind_speed_kmh || 12.5}
            selectedCity={selectedCity}
            className="h-[580px]"
          />
        </div>

        {/* Right: Detected Hotspots Queue */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between overflow-y-auto space-y-4">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-orange-500" />
                <span>Detected Hotspots ({hotspots.length})</span>
              </span>
              <span className="text-[10px] text-teal-600 dark:text-teal-400 font-semibold font-mono">DBSCAN</span>
            </div>

            <div className="mt-3 space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {hotspots.length === 0 ? (
                <div className="text-xs text-slate-500 p-4 text-center">
                  No active clusters detected in recent lookback window.
                </div>
              ) : (
                hotspots.map((hs) => (
                  <div
                    key={hs.id}
                    className="p-3 rounded-lg border text-xs bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/80 space-y-1.5"
                  >
                    <div className="flex items-start justify-between">
                      <span className="font-semibold text-slate-900 dark:text-white">{hs.probable_source}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
                        hs.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-orange-500/20 text-orange-400'
                      }`}>
                        {hs.severity}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-400">
                      Points: <strong>{hs.cluster_size}</strong> | Radius: <strong>{hs.radius_km} km</strong> | Peak FRP: <strong>{hs.max_frp_mw} MW</strong>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-snug line-clamp-3">
                      {hs.reasoning}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 3. KINEMATIC SOURCE ATTRIBUTION PANEL */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-600 dark:text-teal-400" />
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Kinematic Atmospheric Source Attribution for {selectedCity}
            </h2>
          </div>

          {attribution && (
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="text-slate-400">
                Confidence: <strong className="text-teal-400">{attribution.confidence_pct}%</strong>
              </span>
              <span className="text-slate-400">
                Local Share: <strong className="text-slate-200">{attribution.local_share_pct}%</strong>
              </span>
            </div>
          )}
        </div>

        {attribution ? (
          <div className="space-y-4">
            {/* Scientific Explanation Box */}
            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700 text-xs text-slate-200 leading-relaxed font-mono">
              {attribution.plain_language_reasoning}
            </div>

            {/* Diagnostic Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
                <div className="text-slate-400">Dominant Source</div>
                <div className="font-bold text-slate-100 mt-1">{attribution.dominant_source}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
                <div className="text-slate-400">Surface Wind Vector</div>
                <div className="font-bold text-teal-400 mt-1 font-mono">
                  {attribution.meteorology?.wind_direction_cardinal} ({Math.round(attribution.meteorology?.wind_direction_deg)}°) @ {attribution.meteorology?.wind_speed_kmh?.toFixed(1)} km/h
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
                <div className="text-slate-400">Boundary Layer Height</div>
                <div className="font-bold text-slate-100 mt-1 font-mono">
                  {Math.round(attribution.meteorology?.boundary_layer_height_m)} m (Inversion Trapping)
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/60">
                <div className="text-slate-400">Attributed Upwind Sectors</div>
                <div className="font-bold text-slate-100 mt-1 font-mono">
                  {attribution.attributed_sources?.length || 0} active regional plumes
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700 text-xs text-slate-400">
            Awaiting kinematic wind field projection...
          </div>
        )}
      </div>
    </div>
  );
};
