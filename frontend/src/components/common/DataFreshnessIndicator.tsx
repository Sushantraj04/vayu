import React from 'react';
import { Wifi, WifiOff, Clock } from 'lucide-react';
import { formatTimeAgo } from '@/lib/utils';

interface DataFreshnessProps {
  lastSync?: string | Date;
  status?: 'LIVE' | 'DELAYED' | 'UNAVAILABLE';
}

export const DataFreshnessIndicator: React.FC<DataFreshnessProps> = ({
  lastSync = new Date(),
  status = 'LIVE',
}) => {
  const getBadge = () => {
    switch (status) {
      case 'LIVE':
        return {
          icon: <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />,
          text: 'Live Telemetry',
          bg: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/25',
        };
      case 'DELAYED':
        return {
          icon: <Clock className="w-3 h-3 text-amber-500" />,
          text: 'Delayed Stream',
          bg: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25',
        };
      case 'UNAVAILABLE':
        return {
          icon: <WifiOff className="w-3 h-3 text-rose-500" />,
          text: 'Source Down',
          bg: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/25',
        };
    }
  };

  const badge = getBadge();

  return (
    <div className={`hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold whitespace-nowrap shrink-0 ${badge.bg}`}>
      {badge.icon}
      <span>{badge.text}</span>
      <span className="opacity-60 text-[10px] font-mono">({formatTimeAgo(lastSync)})</span>
    </div>
  );
};
