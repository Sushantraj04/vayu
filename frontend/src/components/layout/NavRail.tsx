import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore, AppView } from '@/store/useAppStore';
import { 
  Compass, 
  Map, 
  Flame, 
  AlertTriangle, 
  Camera, 
  Cpu, 
  Database, 
  Share2, 
  Settings, 
  FileText, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

export const NavRail: React.FC = () => {
  const { t } = useTranslation();
  const { currentView, setView, isNavCollapsed, toggleNavCollapsed, currentRole } = useAppStore();

  const navItems = [
    // Citizen view
    {
      id: 'public' as AppView,
      label: t('nav.air_near_me'),
      icon: <Compass className="w-5 h-5" />,
      roles: ['public', 'authority', 'analyst', 'admin'],
      publicOnly: true,
    },
    // Authority views
    {
      id: 'situation' as AppView,
      label: t('nav.situation_room'),
      icon: <Map className="w-5 h-5" />,
      roles: ['authority', 'admin', 'analyst'],
      badge: 'LIVE',
    },
    {
      id: 'corridors' as AppView,
      label: t('nav.corridor_overview'),
      icon: <Flame className="w-5 h-5" />,
      roles: ['authority', 'analyst', 'admin'],
    },
    {
      id: 'alerts' as AppView,
      label: t('nav.alerts_queue'),
      icon: <AlertTriangle className="w-5 h-5" />,
      roles: ['authority', 'admin', 'analyst'],
      badge: '3',
      badgeColor: 'bg-rose-500 text-white',
    },
    {
      id: 'reports' as AppView,
      label: t('nav.citizen_reports'),
      icon: <Camera className="w-5 h-5" />,
      roles: ['public', 'authority', 'analyst', 'admin'],
    },
    // Analyst views
    {
      id: 'models' as AppView,
      label: t('nav.model_performance'),
      icon: <Cpu className="w-5 h-5" />,
      roles: ['analyst', 'admin'],
    },
    {
      id: 'sources' as AppView,
      label: t('nav.data_sources'),
      icon: <Database className="w-5 h-5" />,
      roles: ['analyst', 'admin', 'authority'],
    },
    {
      id: 'network' as AppView,
      label: t('nav.federated_network'),
      icon: <Share2 className="w-5 h-5" />,
      roles: ['analyst', 'admin', 'partner-api-key'],
      badge: '3 Nodes',
    },
    // Common settings & docs
    {
      id: 'settings' as AppView,
      label: t('nav.settings'),
      icon: <Settings className="w-5 h-5" />,
      roles: ['authority', 'analyst', 'admin'],
    },
    {
      id: 'docs' as AppView,
      label: t('nav.api_docs'),
      icon: <FileText className="w-5 h-5" />,
      roles: ['public', 'authority', 'analyst', 'admin', 'partner-api-key'],
    },
  ];

  // Filter items based on active role
  const visibleItems = navItems.filter((item) => {
    if (currentRole === 'public') {
      return item.id === 'public' || item.id === 'reports' || item.id === 'docs';
    }
    return item.roles.includes(currentRole);
  });

  return (
    <aside
      className={`h-[calc(100vh-4rem)] border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all duration-200 flex flex-col justify-between select-none ${
        isNavCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Navigation Links */}
      <div className="p-3 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              title={isNavCollapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/80 dark:text-brand-300 font-semibold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              <div className={`${isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-500 dark:text-slate-400'}`}>
                {item.icon}
              </div>
              {!isNavCollapsed && (
                <div className="flex-1 flex items-center justify-between text-left truncate">
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold ${item.badgeColor || 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'}`}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Collapse Toggle Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={toggleNavCollapsed}
          className="w-full flex items-center justify-center p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
          title={isNavCollapsed ? 'Expand Navigation Rail' : 'Collapse Navigation Rail'}
        >
          {isNavCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!isNavCollapsed && <span className="ml-2 text-xs">Collapse Rail</span>}
        </button>
      </div>
    </aside>
  );
};
