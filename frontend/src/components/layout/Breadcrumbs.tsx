import React from 'react';
import { useAppStore } from '@/store/useAppStore';
import { ChevronRight, Home } from 'lucide-react';

export const Breadcrumbs: React.FC = () => {
  const { currentView, currentCorridorId } = useAppStore();

  const getViewTitle = () => {
    switch (currentView) {
      case 'public': return 'Air Near Me (Citizen Portal)';
      case 'situation': return 'Emergency Situation Room';
      case 'corridors': return 'Economic Corridor Analysis';
      case 'alerts': return 'Emergency Alert & Directive Queue';
      case 'reports': return 'Citizen Science & Incident Moderation';
      case 'models': return 'Model Registry & Backtesting Analytics';
      case 'sources': return 'Data Sources & Ingestion Telemetry';
      case 'network': return 'Federated Network & Node Synchronization';
      case 'settings': return 'System Settings & Channel Dispatch';
      case 'docs': return 'Open API & Digital Public Good Documentation';
      default: return 'Overview';
    }
  };

  return (
    <nav className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 py-3 px-6 bg-slate-50/50 dark:bg-slate-950/40 border-b border-slate-200/80 dark:border-slate-800/80 font-medium">
      <div className="flex items-center gap-1 hover:text-slate-800 dark:hover:text-slate-200 cursor-pointer">
        <Home className="w-3.5 h-3.5" />
        <span>VAYU-NET</span>
      </div>
      <ChevronRight className="w-3 h-3 text-slate-400" />
      <span className="capitalize">{currentCorridorId.replace(/-/g, ' ')}</span>
      <ChevronRight className="w-3 h-3 text-slate-400" />
      <span className="text-slate-900 dark:text-slate-100 font-semibold">{getViewTitle()}</span>
    </nav>
  );
};
