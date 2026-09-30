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
    <header className="h-16 px-4 md:px-6 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between gap-3 w-full shrink-0 select-none">
      {/* LEFT SECTION: Brand & Corridor Selector */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Brand Logo & Name (Guaranteed Never Wrap) */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center text-white shadow-md shadow-teal-500/20 shrink-0">
            <Wind className="w-5 h-5" />
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="font-black text-lg tracking-tight bg-gradient-to-r from-slate-900 to-slate-700 dark:from-white dark:to-slate-200 bg-clip-text text-transparent whitespace-nowrap">
              VAYU-NET
            </span>
            <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wider bg-teal-50 text-teal-700 dark:bg-teal-950/70 dark:text-teal-300 border border-teal-200 dark:border-teal-800 whitespace-nowrap shrink-0">
              DPG Standard
            </span>
          </div>
        </div>

        {/* Divider */}
        <div className="hidden lg:block w-px h-6 bg-slate-200 dark:border-slate-800 shrink-0" />

        {/* Corridor Selector (Compact, Ellipsis on overflow) */}
        <div className="hidden lg:flex items-center gap-1.5 shrink-0">
          <Layers className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={currentCorridorId}
            onChange={(e) => setCorridorId(e.target.value)}
            aria-label="Select Corridor"
            className="text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 py-1.5 px-2.5 rounded-lg border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer max-w-[210px] xl:max-w-[260px] truncate"
          >
            <option value="indo-gangetic-main">Indo-Gangetic Spine</option>
            <option value="delhi-ncr-industrial">Delhi-NCR Industrial Belt</option>
          </select>
        </div>
      </div>

      {/* CENTER SECTION: Global Search / Command Palette Trigger (Fixed Size & Single Line) */}
      <div className="hidden md:flex items-center justify-center shrink-0">
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="w-56 lg:w-72 flex items-center justify-between px-3 py-1.5 rounded-xl text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600 transition-all shadow-inner cursor-pointer"
        >
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="truncate whitespace-nowrap">Search station, city...</span>
          </div>
          <kbd className="inline-block px-1.5 py-0.5 text-[9px] font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded shadow-xs shrink-0 ml-1">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* RIGHT SECTION: Freshness, Language, Theme, Role (Clean, Single Line, Never Wraps) */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Live Telemetry Indicator */}
        <DataFreshnessIndicator status="LIVE" />

        {/* Language Switcher (EN / HI) */}
        <button
          onClick={toggleLanguage}
          title="Switch Language (English / हिन्दी)"
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 transition-colors shrink-0 cursor-pointer"
        >
          <Globe className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
          <span className="whitespace-nowrap">{i18n.language === 'hi' ? 'HI' : 'EN'}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          className="p-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 transition-colors shrink-0 cursor-pointer"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-600" />
          )}
        </button>

        {/* Role Selector Pill (Compact, Clean, Never Wraps) */}
        <div className="relative flex items-center shrink-0">
          <div className="flex items-center gap-1.5 pl-2.5 pr-2 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs shadow-xs shrink-0">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
            <select
              value={currentRole}
              onChange={(e) => setRole(e.target.value as UserRole)}
              aria-label="Select User Role"
              className="bg-transparent font-bold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pr-1 whitespace-nowrap text-xs"
            >
              <option value="public" className="bg-slate-900 text-white">Public (Citizen)</option>
              <option value="authority" className="bg-slate-900 text-white">Authority (Ops)</option>
              <option value="analyst" className="bg-slate-900 text-white">Analyst (AI)</option>
              <option value="admin" className="bg-slate-900 text-white">Administrator</option>
              <option value="partner-api-key" className="bg-slate-900 text-white">BRICS Partner</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
