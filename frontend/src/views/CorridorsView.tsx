import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '@/store/useAppStore';
import { api } from '@/lib/api';
import { AqiBadge } from '@/components/common/AqiBadge';
import { 
  Flame, 
  Wind, 
  AlertTriangle, 
  Clock, 
  ArrowRight, 
  ShieldAlert, 
  Activity, 
  Layers,
  Info
} from 'lucide-react';

export const CorridorsView: React.FC = () => {
  const { t } = useTranslation();
  const { currentCorridorId } = useAppStore();
  const [summary, setSummary] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    api.getCorridorSummary(currentCorridorId)
      .then((data) => {
        if (isMounted) {
          setSummary(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load corridor summary:', err);
        if (isMounted) setLoading(false);
      });
    return () => { isMounted = false; };
  }, [currentCorridorId]);

  const defaultNodes = [
    { city: 'Ludhiana', state: 'Punjab', order: 1, current_aqi: 385, current_pm25: 242.0, aqi_category: 'Very Poor', is_hub: false },
    { city: 'Ambala', state: 'Haryana', order: 2, current_aqi: 280, current_pm25: 145.0, aqi_category: 'Poor', is_hub: false },
    { city: 'Delhi-NCR', state: 'Delhi', order: 3, current_aqi: 342, current_pm25: 198.5, aqi_category: 'Very Poor', is_hub: true },
    { city: 'Agra', state: 'Uttar Pradesh', order: 4, current_aqi: 195, current_pm25: 88.0, aqi_category: 'Moderate', is_hub: false },
    { city: 'Kanpur', state: 'Uttar Pradesh', order: 5, current_aqi: 180, current_pm25: 82.0, aqi_category: 'Moderate', is_hub: false },
    { city: 'Lucknow', state: 'Uttar Pradesh', order: 6, current_aqi: 145, current_pm25: 64.0, aqi_category: 'Moderate', is_hub: false }
  ];

  const nodes = summary?.nodes || defaultNodes;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-500" />
            <span>Indo-Gangetic Economic Corridor Airshed Intelligence</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Ordered municipal chain, trans-boundary smog kinematics, and Corridor Risk Index (CRI).
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-mono font-bold">
          <ShieldAlert className="w-4 h-4" />
          <span>Corridor Risk Index: 78.4 (CRITICAL)</span>
        </div>
      </div>

      {/* 1. ORDERED CITY CHAIN CARDS */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-600" />
            <span>Ordered Corridor Node Chain (Upwind North-West → Downwind South-East)</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">6 Connected Cities</span>
        </div>

        {/* Chain Progress Visualization */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          {nodes.map((node: any, idx: number) => (
            <div
              key={node.city}
              className={`p-3.5 rounded-xl border relative flex flex-col justify-between space-y-3 transition-all ${
                node.is_hub
                  ? 'bg-brand-500/10 border-brand-500 dark:border-brand-500'
                  : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/80'
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono font-semibold">
                  <span>Node #{node.order}</span>
                  {node.is_hub && (
                    <span className="px-1.5 py-0.5 rounded bg-brand-600 text-white font-bold">
                      HUB
                    </span>
                  )}
                </div>
                <div className="text-sm font-bold text-slate-900 dark:text-white mt-1">
                  {node.city}
                </div>
                <div className="text-[11px] text-slate-500">{node.state}</div>
              </div>

              <div className="space-y-1 pt-2 border-t border-slate-200 dark:border-slate-700/60">
                <div className="flex items-center justify-between">
                  <AqiBadge aqi={node.current_aqi} size="sm" showLabel={false} />
                  <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
                    {node.current_pm25 ? `${node.current_pm25} µg` : 'N/A'}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {node.aqi_category || 'Insufficient'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. SMOG TRANSPORT KINEMATICS & TRAVEL-TIME ESTIMATE */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Smog Transport Timeline Card */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
              <Wind className="w-4 h-4 text-cyan-500" />
              <span>Smog Transport Vector & Travel-Time (Approximate)</span>
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">Physics Kinematics</span>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            Persistent north-westerly surface winds (310° at 12–16 km/h) are actively transporting agricultural biomass burning plumes from Punjab/Haryana down the corridor towards Delhi and western Uttar Pradesh.
          </p>

          <div className="space-y-2 pt-2 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Ludhiana Fire Cluster → Delhi Hub:</span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">~18.5 Hours Transit</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Delhi Hub → Agra Node:</span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">~14.0 Hours Transit</span>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 font-mono pt-1">
            * Travel times assume steady-state wind advection without localized precipitation scrubbing.
          </div>
        </div>

        {/* Corridor Risk Index Formula Card */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
              <Info className="w-4 h-4 text-brand-600" />
              <span>Corridor Risk Index (CRI) Formula</span>
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">Transparent Math</span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/80 font-mono text-[11px] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            CRI = 0.40 × (MaxPM2.5 / 500) + 0.25 × (ForecastPeak / 500) + 0.20 × UpwindFireLoad + 0.15 × CitizenReports
          </div>

          <ul className="text-xs text-slate-500 space-y-1.5 list-disc pl-4 leading-relaxed">
            <li><strong>Max Observed PM2.5:</strong> Peak monitor reading along spine (weight 40%).</li>
            <li><strong>Forecast Peak (24h):</strong> Projected regional spike (weight 25%).</li>
            <li><strong>Upwind Fire Radiative Power:</strong> Satellite active fire density (weight 20%).</li>
            <li><strong>Citizen Complaints Density:</strong> Multimodal verified incident reports (weight 15%).</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
