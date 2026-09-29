import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  AlertTriangle, 
  Download, 
  ShieldAlert, 
  Info, 
  RefreshCw, 
  Rss, 
  Check, 
  Play
} from 'lucide-react';
import { api } from '@/lib/api';

export const AlertsView: React.FC = () => {
  const { t } = useTranslation();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadAlerts = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAlerts();
      setAlerts(data || []);
    } catch (e: any) {
      console.error('Failed to load alerts:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleEvaluateRules = async () => {
    setIsEvaluating(true);
    setStatusMsg('Evaluating environmental rules across all corridor telemetry...');
    try {
      const res = await api.evaluateAlerts();
      setStatusMsg(`Evaluation complete: ${res.count} alerts generated/updated.`);
      loadAlerts();
    } catch (e: any) {
      setStatusMsg(`Rule evaluation error: ${e.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleAcknowledge = async (id: string) => {
    try {
      await api.acknowledgeAlert(id);
      loadAlerts();
    } catch (e: any) {
      alert(`Could not acknowledge alert: ${e.message}`);
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await api.resolveAlert(id);
      loadAlerts();
    } catch (e: any) {
      alert(`Could not resolve alert: ${e.message}`);
    }
  };

  const downloadCapXml = (capId: string) => {
    window.open(`/api/v1/alerts/cap/${encodeURIComponent(capId)}`, '_blank');
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <span>Emergency Alert Lifecycle & OASIS CAP 1.2 Dispatch</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Automated threshold evaluation, bilingual English/Hindi advisories, and international disaster standard feeds.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <a
            href="/api/v1/alerts/feed.atom"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-orange-500/10 hover:bg-orange-500/20 text-orange-400 border border-orange-500/30 text-xs font-semibold transition-colors"
          >
            <Rss className="w-3.5 h-3.5" />
            <span>CAP 1.2 Atom Feed</span>
          </a>

          <button
            onClick={handleEvaluateRules}
            disabled={isEvaluating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <Play className={`w-3.5 h-3.5 ${isEvaluating ? 'animate-spin' : ''}`} />
            <span>Evaluate Rules Now</span>
          </button>

          <button
            onClick={loadAlerts}
            title="Refresh Alerts"
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-teal-400' : ''}`} />
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs flex items-center justify-between">
          <span className="font-mono">{statusMsg}</span>
          <button onClick={() => setStatusMsg(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Alerts Table */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-500" />
            <span>Active Corridor Alerts ({alerts.filter((a) => a.status !== 'RESOLVED').length})</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">Cooldown Deduplication: 3 Hours</span>
        </div>

        {alerts.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No active alerts detected. The airshed is currently within baseline limits.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border transition-all ${
                  alert.status === 'NEW'
                    ? 'bg-rose-500/5 border-rose-500/30'
                    : alert.status === 'ACKNOWLEDGED'
                    ? 'bg-amber-500/5 border-amber-500/30'
                    : 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800 opacity-60'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-red-500/20 text-red-500'
                          : alert.severity === 'SEVERE'
                          ? 'bg-rose-500/20 text-rose-600 dark:text-rose-400'
                          : 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                      }`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs font-bold text-slate-900 dark:text-white">{alert.title_en}</span>
                    </div>

                    <div className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                      {alert.title_hi}
                    </div>

                    <div className="text-[11px] text-slate-500 font-mono">
                      CAP: {alert.cap_identifier} • City: {alert.city} • Trigger: {alert.rule_trigger}
                    </div>
                  </div>

                  {/* Status Badge & Actions */}
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-semibold font-mono ${
                      alert.status === 'NEW'
                        ? 'bg-rose-500 text-white'
                        : alert.status === 'ACKNOWLEDGED'
                        ? 'bg-amber-500 text-white'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                    }`}>
                      {alert.status}
                    </span>

                    {alert.status === 'NEW' && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="px-2.5 py-1 rounded-md bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium cursor-pointer"
                      >
                        Acknowledge
                      </button>
                    )}

                    {alert.status !== 'RESOLVED' && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium cursor-pointer"
                      >
                        Resolve
                      </button>
                    )}

                    <button
                      onClick={() => downloadCapXml(alert.cap_identifier)}
                      title="Download OASIS CAP 1.2 XML Document"
                      className="p-1.5 rounded-md border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 cursor-pointer flex items-center gap-1 text-xs"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>XML</span>
                    </button>
                  </div>
                </div>

                {/* Underlying Physical Evidence */}
                <div className="mt-3 p-3 rounded-lg bg-white/70 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300 space-y-1">
                  <span className="font-semibold text-slate-900 dark:text-white flex items-center gap-1">
                    <Info className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                    <span>Physical Advisory Details:</span>
                  </span>
                  <p className="text-[11px] leading-relaxed">{alert.description_en}</p>
                  <p className="text-[11px] leading-relaxed opacity-80">{alert.description_hi}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
