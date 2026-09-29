import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Share2, 
  Server, 
  ShieldCheck, 
  RefreshCw, 
  Play, 
  Lock,
  Globe,
  CheckCircle2,
  TrendingDown
} from 'lucide-react';
import { api } from '@/lib/api';

export const FederatedNetworkView: React.FC = () => {
  const { t } = useTranslation();

  const [networkStatus, setNetworkStatus] = useState<any | null>(null);
  const [rounds, setRounds] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statusRes, roundsRes] = await Promise.allSettled([
        api.getFederatedStatus(),
        api.getFederatedRounds(),
      ]);

      if (statusRes.status === 'fulfilled') setNetworkStatus(statusRes.value);
      if (roundsRes.status === 'fulfilled') setRounds(roundsRes.value || []);
    } catch (e) {
      console.error('Failed to load federated network data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunRound = async () => {
    setIsTraining(true);
    setStatusMsg('Dispatching local training with Differential Privacy across all nodes...');
    try {
      const res = await api.runFederatedRound();
      setStatusMsg(`FedAvg Round #${res.round.round_number} complete! Loss: ${res.round.global_loss.toFixed(4)}.`);
      loadData();
    } catch (e: any) {
      setStatusMsg(`Failed to run federated round: ${e.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  const nodes = networkStatus?.nodes || [];
  const latestRound = networkStatus?.latest_round;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Share2 className="w-5 h-5 text-teal-600 dark:text-teal-400" />
            <span>Digital Public Good: Multi-Node Federated Learning Network</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Decentralized sequence model training via FedAvg across independent municipal and BRICS airshed nodes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunRound}
            disabled={isTraining}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <Play className={`w-3.5 h-3.5 ${isTraining ? 'animate-spin' : ''}`} />
            <span>{isTraining ? 'Aggregating FedAvg...' : 'Execute FedAvg Round'}</span>
          </button>

          <button
            onClick={loadData}
            title="Refresh Network"
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

      {/* 1. DATA SOVEREIGNTY BANNER */}
      <div className="p-5 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-teal-950 dark:text-teal-200 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-teal-800 dark:text-teal-300">
            <ShieldCheck className="w-4 h-4" />
            <span>Sovereign Data Contract (DPG Standard)</span>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-mono text-teal-400">
            <Lock className="w-3.5 h-3.5" />
            <span>Local Differential Privacy (ε=2.0, δ=1e-5, C=1.5)</span>
          </div>
        </div>
        <p className="text-xs leading-relaxed opacity-95">
          "Raw environmental and citizen telemetry never leaves municipal node boundaries. Each municipal node trains local sequence parameters on its private database. Only differentially privatized weight updates travel between nodes and the coordinator via FedAvg."
        </p>
      </div>

      {/* 2. FEDERATED COORDINATOR STATUS */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400">
              <Server className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                VAYU-NET FedAvg Central Coordinator
              </h2>
              <span className="text-xs text-slate-400 font-mono">
                {networkStatus?.coordinator_version || 'vayu-fedavg-v2.1'} • {networkStatus?.nodes_count || 7} Registered Nodes (India & BRICS)
              </span>
            </div>
          </div>

          <div className="text-right">
            <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              ROUND #{latestRound?.round_number || 1} {latestRound?.status || 'COMPLETED'}
            </span>
            <div className="text-[11px] text-slate-400 mt-1 font-mono">
              Global Loss: <strong>{latestRound?.global_loss?.toFixed(4) || '0.0412'}</strong>
            </div>
          </div>
        </div>

        {/* Participating Nodes Across India & BRICS */}
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-2">
          <div className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Globe className="w-4 h-4 text-teal-400" />
            <span>Participating Nodes (India Spine & BRICS Corridors)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {nodes.map((node: any) => (
              <div
                key={node.node_id}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white">{node.city}</div>
                    <div className="text-[10px] text-slate-400 truncate max-w-[130px]">{node.corridor}</div>
                  </div>
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/10 text-emerald-500">
                    {node.status}
                  </span>
                </div>

                <div className="text-[10px] font-mono text-slate-500 space-y-0.5 pt-1 border-t border-slate-200 dark:border-slate-700/60">
                  <div>ID: {node.node_id}</div>
                  <div>Model: {node.model_type || 'PyTorch GRU'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. FEDERATED ROUNDS HISTORY TABLE */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <TrendingDown className="w-4 h-4 text-teal-500" />
          <span>Loss Convergence & Completed Federated Rounds</span>
        </h2>

        {rounds.length === 0 ? (
          <div className="p-6 text-center text-slate-400 text-xs">
            No rounds recorded yet. Click "Execute FedAvg Round" above to run the first iteration.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase">
                  <th className="py-2 px-3">Round</th>
                  <th className="py-2 px-3">Global Loss</th>
                  <th className="py-2 px-3">Weight Divergence</th>
                  <th className="py-2 px-3">Participating Nodes</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {rounds.map((r) => (
                  <tr key={r.id || r.round_number} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                      #{r.round_number}
                    </td>
                    <td className="py-2.5 px-3 text-teal-500 font-bold">
                      {r.global_loss?.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {r.weight_divergence?.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-sans">
                      {Array.isArray(r.participating_nodes) ? r.participating_nodes.length : 3} nodes
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-500 font-bold">
                        {r.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-400 font-sans">
                      {new Date(r.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
