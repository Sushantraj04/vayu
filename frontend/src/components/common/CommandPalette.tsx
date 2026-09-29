import React, { useEffect, useState } from 'react';
import { useAppStore, AppView, UserRole } from '@/store/useAppStore';
import { 
  Search, 
  Map, 
  Flame, 
  AlertTriangle, 
  Cpu, 
  Database, 
  Share2, 
  FileText, 
  Sun, 
  Moon, 
  UserCheck, 
  Camera,
  X 
} from 'lucide-react';

export const CommandPalette: React.FC = () => {
  const { 
    isCommandPaletteOpen, 
    setCommandPaletteOpen, 
    setView, 
    setRole, 
    currentRole,
    theme, 
    toggleTheme,
    setReportModalOpen 
  } = useAppStore();
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!isCommandPaletteOpen);
      }
      if (e.key === 'Escape' && isCommandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, setCommandPaletteOpen]);

  if (!isCommandPaletteOpen) return null;

  const items = [
    { label: 'Situation Room (Operational Map)', icon: <Map className="w-4 h-4 text-brand-500" />, action: () => setView('situation') },
    { label: 'Indo-Gangetic Corridor Overview', icon: <Flame className="w-4 h-4 text-orange-500" />, action: () => setView('corridors') },
    { label: 'Active Alerts & Emergency Queue', icon: <AlertTriangle className="w-4 h-4 text-red-500" />, action: () => setView('alerts') },
    { label: 'Citizen Pollution Report Flow', icon: <Camera className="w-4 h-4 text-emerald-500" />, action: () => { setView('reports'); setReportModalOpen(true); } },
    { label: 'Model Performance & Backtesting', icon: <Cpu className="w-4 h-4 text-purple-500" />, action: () => setView('models') },
    { label: 'Data Sources Health & Quality Matrix', icon: <Database className="w-4 h-4 text-blue-500" />, action: () => setView('sources') },
    { label: 'Federated Learning Network Console', icon: <Share2 className="w-4 h-4 text-cyan-500" />, action: () => setView('network') },
    { label: 'API & Digital Public Good Documentation', icon: <FileText className="w-4 h-4 text-slate-500" />, action: () => setView('docs') },
    { label: `Toggle Theme (Currently ${theme})`, icon: theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />, action: toggleTheme },
    // Role switching shortcuts
    { label: 'Switch to Public / Citizen Mode', icon: <UserCheck className="w-4 h-4 text-emerald-600" />, action: () => setRole('public') },
    { label: 'Switch to Authority (Situation Room) Mode', icon: <UserCheck className="w-4 h-4 text-brand-600" />, action: () => setRole('authority') },
    { label: 'Switch to Analyst / Modeler Mode', icon: <UserCheck className="w-4 h-4 text-purple-600" />, action: () => setRole('analyst') },
  ];

  const filtered = items.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-slate-950/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 dark:border-slate-800">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            autoFocus
            type="text"
            placeholder="Type a command or jump to screen..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm focus:outline-none placeholder:text-slate-400 dark:text-slate-100"
          />
          <button 
            onClick={() => setCommandPaletteOpen(false)}
            className="p-1 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto py-2">
          {filtered.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-slate-500">
              No matching commands or screens found.
            </div>
          ) : (
            filtered.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  item.action();
                  setCommandPaletteOpen(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800/80 text-slate-800 dark:text-slate-200 transition-colors"
              >
                <div className="p-1.5 rounded-md bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                  {item.icon}
                </div>
                <span>{item.label}</span>
              </button>
            ))
          )}
        </div>

        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-950/60 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-500 flex justify-between items-center font-mono">
          <span>Navigate with arrows or click</span>
          <span>ESC to close</span>
        </div>
      </div>
    </div>
  );
};
