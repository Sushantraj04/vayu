import { create } from 'zustand';

export type UserRole = 'public' | 'authority' | 'analyst' | 'admin' | 'partner-api-key';
export type AppView = 
  | 'public' 
  | 'situation' 
  | 'corridors' 
  | 'reports' 
  | 'alerts' 
  | 'models' 
  | 'sources' 
  | 'network' 
  | 'settings' 
  | 'docs';

interface LayerState {
  stations: boolean;
  fires: boolean;
  hotspots: boolean;
  wind: boolean;
  corridor: boolean;
  reports: boolean;
  gibs_truecolor: boolean;
  gibs_aod: boolean;
}

interface AppState {
  currentRole: UserRole;
  currentView: AppView;
  currentCorridorId: string;
  theme: 'light' | 'dark';
  isNavCollapsed: boolean;
  isCommandPaletteOpen: boolean;
  isReportModalOpen: boolean;
  selectedCity: string;
  forecastHorizon: number; // 0 (now), 24, 48, 72
  layers: LayerState;
  
  setRole: (role: UserRole) => void;
  setView: (view: AppView) => void;
  setCorridorId: (id: string) => void;
  toggleTheme: () => void;
  toggleNavCollapsed: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setReportModalOpen: (open: boolean) => void;
  setSelectedCity: (city: string) => void;
  setForecastHorizon: (hours: number) => void;
  toggleLayer: (layer: keyof LayerState) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentRole: 'authority', // Default to Situation Room authority for ops, can switch anytime
  currentView: 'situation',
  currentCorridorId: 'indo-gangetic-main',
  theme: 'dark',
  isNavCollapsed: false,
  isCommandPaletteOpen: false,
  isReportModalOpen: false,
  selectedCity: 'Delhi-NCR',
  forecastHorizon: 0,
  layers: {
    stations: true,
    fires: true,
    hotspots: true,
    wind: true,
    corridor: true,
    reports: true,
    gibs_truecolor: false,
    gibs_aod: false,
  },

  setRole: (role) => set({ 
    currentRole: role, 
    currentView: role === 'public' ? 'public' : role === 'authority' ? 'situation' : 'models' 
  }),
  setView: (view) => set({ currentView: view }),
  setCorridorId: (id) => set({ currentCorridorId: id }),
  toggleTheme: () => set((state) => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    if (next === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { theme: next };
  }),
  toggleNavCollapsed: () => set((state) => ({ isNavCollapsed: !state.isNavCollapsed })),
  setCommandPaletteOpen: (open) => set({ isCommandPaletteOpen: open }),
  setReportModalOpen: (open) => set({ isReportModalOpen: open }),
  setSelectedCity: (city) => set({ selectedCity: city }),
  setForecastHorizon: (hours) => set({ forecastHorizon: hours }),
  toggleLayer: (layer) => set((state) => ({
    layers: {
      ...state.layers,
      [layer]: !state.layers[layer],
    }
  })),
}));
