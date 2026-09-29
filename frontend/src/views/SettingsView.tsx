import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Settings, 
  Send, 
  Mail, 
  Globe, 
  ShieldAlert, 
  CheckCircle, 
  XCircle, 
  Clock,
  Key
} from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Settings className="w-5 h-5 text-slate-500" />
          <span>System Settings & Dispatch Channel Status</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Configuration of alerting dispatch webhooks, privacy retention, and operational API keys.
        </p>
      </div>

      {/* 1. DISPATCH CHANNELS STATUS (Honest labeling) */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Send className="w-4 h-4 text-brand-600" />
            <span>Emergency Alert Notification Channels</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Channels without active environment credentials are explicitly marked disabled.
          </p>
        </div>

        <div className="space-y-3">
          {/* Telegram Channel */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sky-500/10 text-sky-500">
                <Send className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">Telegram Broadcast Bot</div>
                <div className="text-[11px] text-slate-500">Instant push notifications to municipal disaster response groups</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              <span>Awaiting Token in .env</span>
            </span>
          </div>

          {/* SMTP Email */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">SMTP Email Dispatch</div>
                <div className="text-[11px] text-slate-500">Automated PDF/HTML advisories to health and transport ministries</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center gap-1.5">
              <XCircle className="w-3 h-3" />
              <span>Not Configured</span>
            </span>
          </div>

          {/* Outbound Webhook / CAP 1.2 */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
                <Globe className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">Public OASIS CAP 1.2 Feed & Outbound Webhook</div>
                <div className="text-[11px] text-slate-500">Standardized XML alert stream for NDMA / SDMA downstream consumers</div>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3" />
              <span>Active (/api/v1/alerts/cap)</span>
            </span>
          </div>
        </div>
      </div>

      {/* 2. PRIVACY & DATA RETENTION */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-600" />
          <span>Privacy by Design & Data Retention Rules</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
            <span className="text-slate-500 font-medium">Public Coordinate Precision:</span>
            <div className="text-sm font-bold font-mono text-slate-900 dark:text-white">500 Meters (~0.005°)</div>
            <p className="text-[11px] text-slate-400">Protects citizen residential anonymity across all public API feeds.</p>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1">
            <span className="text-slate-500 font-medium">Citizen Photo Retention:</span>
            <div className="text-sm font-bold font-mono text-slate-900 dark:text-white">90 Days</div>
            <p className="text-[11px] text-slate-400">Automatic Celery scheduled cleanup prunes raw imagery post season.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
