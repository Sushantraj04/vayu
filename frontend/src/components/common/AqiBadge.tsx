import React from 'react';
import { getAqiCategory } from '@/lib/aqi';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, CheckCircle, ShieldAlert, AlertCircle, Info } from 'lucide-react';

interface AqiBadgeProps {
  aqi: number | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const AqiBadge: React.FC<AqiBadgeProps> = ({ aqi, size = 'md', showLabel = true }) => {
  const { i18n } = useTranslation();
  const category = getAqiCategory(aqi);

  if (aqi === null || aqi === undefined || !category) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-300 dark:border-slate-700">
        <Info className="w-3.5 h-3.5" />
        <span>No Data</span>
      </span>
    );
  }

  const label = i18n.language === 'hi' ? category.hindiName : category.name;

  const renderIcon = () => {
    switch (category.severity) {
      case 'low':
        return <CheckCircle className="w-3.5 h-3.5" />;
      case 'moderate':
        return <Info className="w-3.5 h-3.5" />;
      case 'elevated':
        return <AlertCircle className="w-3.5 h-3.5" />;
      case 'high':
      case 'critical':
        return <AlertTriangle className="w-3.5 h-3.5" />;
      case 'emergency':
        return <ShieldAlert className="w-3.5 h-3.5 animate-pulse" />;
    }
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-2.5 py-1 gap-1.5',
    lg: 'text-base px-3.5 py-1.5 gap-2 font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md font-tabular border font-medium transition-colors ${category.bgLight} ${sizeClasses[size]}`}
      style={{ borderLeftColor: category.color, borderLeftWidth: '4px' }}
      title={`${category.name} (NAQI ${aqi})`}
    >
      {renderIcon()}
      <span className="font-mono font-bold">{aqi}</span>
      {showLabel && <span className="opacity-90 ml-0.5">{label}</span>}
    </span>
  );
};
