import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore } from '@/store/useAppStore';
import { 
  Camera, 
  MapPin, 
  ShieldCheck, 
  RefreshCw,
  Clock,
  Check,
  X,
  FileText
} from 'lucide-react';
import { api } from '@/lib/api';
import { ReportModal } from '@/components/Citizen/ReportModal';

export const CitizenReportView: React.FC = () => {
  const { t } = useTranslation();
  const { currentRole } = useAppStore();

  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadReports = async () => {
    setIsLoading(true);
    try {
      const data = await api.getReports(filterStatus || undefined);
      setReports(data || []);
    } catch (e: any) {
      console.error('Failed to load reports:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [filterStatus]);

  const handleModerate = async (reportId: string, newStatus: 'VERIFIED' | 'REJECTED') => {
    try {
      await api.moderateReport(reportId, { status: newStatus });
      loadReports();
    } catch (e: any) {
      alert(`Moderation failed: ${e.message}`);
    }
  };

  const isAuthority = currentRole === 'authority' || currentRole === 'admin';

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Camera className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>Citizen Science & Ground Truth Incident Reporting</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Crowdsourced ground pollution intelligence cross-validated against NASA VIIRS satellite radiometry and ground sensors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 py-1.5 px-3 rounded-lg border border-slate-200 dark:border-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="VERIFIED">Verified Only</option>
            <option value="PENDING">Pending Only</option>
          </select>

          <button
            onClick={() => setIsModalOpen(true)}
            className="py-2 px-3.5 rounded-xl font-semibold text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-2 shadow-sm cursor-pointer"
          >
            <Camera className="w-4 h-4" />
            <span>New Citizen Report</span>
          </button>

          <button
            onClick={loadReports}
            title="Refresh Reports"
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-teal-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Reports Feed Table */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Community Incident Feed ({reports.length} Reports)</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">Privacy by Design: ~500m Grid Anonymized</span>
        </div>

        {reports.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No citizen reports found for the selected filter. Click "New Citizen Report" to submit an observation.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">Report ID</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Location (~500m Grid)</th>
                  <th className="py-2.5 px-3">Sensor Value</th>
                  <th className="py-2.5 px-3">Satellite Cross-Check</th>
                  <th className="py-2.5 px-3">Status</th>
                  {isAuthority && <th className="py-2.5 px-3 text-right">Moderation</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono">
                {reports.map((r) => (
                  <tr key={r.id || r.public_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-3 font-bold text-slate-900 dark:text-white font-mono">
                      {r.public_id}
                    </td>
                    <td className="py-3 px-3 font-sans capitalize text-slate-700 dark:text-slate-300">
                      {r.user_category?.replace('_', ' ')}
                    </td>
                    <td className="py-3 px-3 text-[11px] text-slate-500 font-mono">
                      {r.public_lat?.toFixed(3)}°N, {r.public_lon?.toFixed(3)}°E
                    </td>
                    <td className="py-3 px-3 text-[11px] text-slate-600 dark:text-slate-300 font-mono">
                      {r.user_pm25 ? `${r.user_pm25} µg/m³` : 'N/A'}
                    </td>
                    <td className="py-3 px-3">
                      {r.is_satellite_verified ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                          ✓ Verified by VIIRS
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-300 dark:border-slate-700">
                          Pending Satellite Pass
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.status === 'VERIFIED'
                          ? 'bg-emerald-500/10 text-emerald-500'
                          : r.status === 'REJECTED'
                          ? 'bg-red-500/10 text-red-500'
                          : 'bg-amber-500/10 text-amber-500'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    {isAuthority && (
                      <td className="py-3 px-3 text-right space-x-1 font-sans">
                        {r.status === 'PENDING' && (
                          <>
                            <button
                              onClick={() => handleModerate(r.id, 'VERIFIED')}
                              className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium cursor-pointer"
                            >
                              Verify
                            </button>
                            <button
                              onClick={() => handleModerate(r.id, 'REJECTED')}
                              className="px-2 py-1 rounded bg-red-600 hover:bg-red-500 text-white font-medium cursor-pointer"
                            >
                              Reject
                            </button>
                          </>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ReportModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadReports}
      />
    </div>
  );
};
