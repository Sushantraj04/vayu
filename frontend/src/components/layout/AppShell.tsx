import React from 'react';
import { TopBar } from './TopBar';
import { NavRail } from './NavRail';
import { Breadcrumbs } from './Breadcrumbs';
import { CommandPalette } from '@/components/common/CommandPalette';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <NavRail />
        <main className="flex-1 flex flex-col overflow-y-auto">
          <Breadcrumbs />
          <div className="flex-1 p-4 md:p-6 overflow-y-auto">
            {children}
          </div>
        </main>
      </div>
      <CommandPalette />
    </div>
  );
};
