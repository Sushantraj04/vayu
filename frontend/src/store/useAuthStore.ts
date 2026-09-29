import { create } from 'zustand';

export interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  api_key?: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (token: string, refreshToken: string, user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  const savedToken = localStorage.getItem('vayunet_token');
  const savedRefresh = localStorage.getItem('vayunet_refresh');
  const savedUser = localStorage.getItem('vayunet_user');

  return {
    token: savedToken,
    refreshToken: savedRefresh,
    user: savedUser ? JSON.parse(savedUser) : null,
    isAuthenticated: !!savedToken,

    setAuth: (token, refreshToken, user) => {
      localStorage.setItem('vayunet_token', token);
      localStorage.setItem('vayunet_refresh', refreshToken);
      localStorage.setItem('vayunet_user', JSON.stringify(user));
      set({ token, refreshToken, user, isAuthenticated: true });
    },

    logout: () => {
      localStorage.removeItem('vayunet_token');
      localStorage.removeItem('vayunet_refresh');
      localStorage.removeItem('vayunet_user');
      set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
    },
  };
});
