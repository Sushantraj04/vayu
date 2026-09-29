import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAppStore, UserRole } from '@/store/useAppStore';
import { DataFreshnessIndicator } from '@/components/common/DataFreshnessIndicator';
import { 
  Wind, 
  Search, 
  Sun, 
  Moon, 
  Globe, 
  User, 
  Layers, 
  ShieldCheck, 
  ChevronDown 
} from 'lucide-react';

export const TopBar: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { 
    theme, 
    toggleTheme, 
    currentRole, 
    setRole, 
    currentCorridorId, 
    setCorridorId, 
    setCommandPaletteOpen 
  } = useAppStore();

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'hi' ? 'en' : 'hi';
    i18n.changeLanguage(nextLang);
  };

  return (
    <header className="h-16 px-4 md:px-6 border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between gap-4">
      {/* Brand & Corridor Selector */}
      <div className="flex items-center gap-3 md:gap-6">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-teal-700 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <Wind className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-slate-900 to-slate-700 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
                VAYU-NET
              </span>
              <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
                DPG Standard
              </span>
            </div>
          </div>
        </div>

        {/* Corridor Selector */}
        <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-slate-200 dark:border-slate-800">
          <Layers className="w-4 h-4 text-slate-400" />
          <select
            value={currentCorridorId}
            onChange={(e) => setCorridorId(e.target.value)}
            aria-label="Select Corridor"
            className="text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-1.5 px-3 rounded-lg border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500 cursor-pointer"
          >
            <option value="indo-gangetic-main">Indo-Gangetic Spine (Punjab-Delhi-UP)</option>
            <option value="delhi-ncr-industrial">Delhi-NCR Industrial Belt</option>
          </select>
        </div>
      </div>

      {/* Global Search / Command Palette Trigger */}
      <div className="flex-1 max-w-md hidden md:block">
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600 transition-colors shadow-inner"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span>{t('app.search_placeholder')}</span>
          </div>
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded shadow-xs">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Controls: Freshness, Language, Theme, Role */}
      <div className="flex items-center gap-2.5">
        <DataFreshnessIndicator status="LIVE" />

        {/* Language Switcher (EN / HI) */}
        <button
          onClick={toggleLanguage}
          title="Switch Language (English / हिन्दी)"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 transition-colors"
        >
          <Globe className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
          <span className="font-semibold">{i18n.language === 'hi' ? 'HI' : 'EN'}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 transition-colors"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-600" />
          )}
        </button>

        {/* Role Selector Dropdown (Allows instant review of Citizen, Authority, Analyst experiences) */}
        <div className="relative flex items-center">
          <div className="flex items-center gap-1.5 pl-2.5 pr-2 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
            <select
              value={currentRole}
              onChange={(e) => setRole(e.target.value as UserRole)}
              aria-label="Select User Role"
              className="bg-transparent font-medium text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pr-1"
            >
              <option value="public">Role: Public / Citizen</option>
              <option value="authority">Role: Authority (Situation Room)</option>
              <option value="analyst">Role: Analyst / Modeler</option>
              <option value="admin">Role: Administrator</option>
              <option value="partner-api-key">Role: BRICS Partner</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
