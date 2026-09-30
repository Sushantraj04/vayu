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
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased selection:bg-teal-500/20 selection:text-teal-400 relative">
      {/* Subtle Tactical Engineering Grid Texture */}
      <div className="fixed inset-0 bg-tactical-grid opacity-60 pointer-events-none z-0" />
      <div className="relative z-10 flex flex-col min-h-screen">
        <TopBar />
        <div className="flex-1 flex overflow-hidden">
          <NavRail />
          <main className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden min-w-0 scroll-smooth">
            <Breadcrumbs />
            <div className="flex-1 p-4 sm:p-6 lg:p-8">
              {children}
            </div>
          </main>
        </div>
        <CommandPalette />
      </div>
    </div>
  );
};
