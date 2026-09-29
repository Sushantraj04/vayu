import React from 'react';
import { useAppStore } from '@/store/useAppStore';
import { AppShell } from '@/components/layout/AppShell';
import { PublicPortal } from '@/views/PublicPortal';
import { SituationRoom } from '@/views/SituationRoom';
import { CorridorsView } from '@/views/CorridorsView';
import { CitizenReportView } from '@/views/CitizenReportView';
import { AlertsView } from '@/views/AlertsView';
import { AnalystConsole } from '@/views/AnalystConsole';
import { FederatedNetworkView } from '@/views/FederatedNetworkView';
import { SettingsView } from '@/views/SettingsView';
import { DocsView } from '@/views/DocsView';

export const App: React.FC = () => {
  const { currentView } = useAppStore();

  const renderActiveView = () => {
    switch (currentView) {
      case 'public':
        return <PublicPortal />;
      case 'situation':
        return <SituationRoom />;
      case 'corridors':
        return <CorridorsView />;
      case 'reports':
        return <CitizenReportView />;
      case 'alerts':
        return <AlertsView />;
      case 'models':
      case 'sources':
        return <AnalystConsole />;
      case 'network':
        return <FederatedNetworkView />;
      case 'settings':
        return <SettingsView />;
      case 'docs':
        return <DocsView />;
      default:
        return <PublicPortal />;
    }
  };

  return (
    <AppShell>
      {renderActiveView()}
    </AppShell>
  );
};

export default App;
