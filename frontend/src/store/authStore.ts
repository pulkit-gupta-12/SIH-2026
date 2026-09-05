/**
 * Auth Store — Zustand store for authentication state.
 * Manages user, role, tokens, login/logout.
 */
import { create } from 'zustand';
import type { AuthUser } from '../services/authService';

export type UserRole =
  | 'citizen'
  | 'field_officer'
  | 'national_admin'
  | 'business'
  | 'rule_admin';

interface AuthState {
  user: AuthUser | null;
  activeRole: UserRole | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  // Actions
  setAuth: (user: AuthUser, access: string, refresh: string) => void;
  setActiveRole: (role: UserRole) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  activeRole: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,

  setAuth: (user, access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('auth_user', JSON.stringify(user));

    // Default active role = first role in the list
    const activeRole = (user.roles[0] as UserRole) || null;
    if (activeRole) {
      localStorage.setItem('active_role', activeRole);
    }

    set({
      user,
      activeRole,
      accessToken: access,
      refreshToken: refresh,
      isAuthenticated: true,
    });
  },

  setActiveRole: (role) => {
    localStorage.setItem('active_role', role);
    set({ activeRole: role });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('active_role');
    set({
      user: null,
      activeRole: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },

  hydrate: () => {
    const access = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    const userStr = localStorage.getItem('auth_user');
    const activeRole = localStorage.getItem('active_role') as UserRole | null;

    if (access && refresh && userStr) {
      try {
        const user = JSON.parse(userStr) as AuthUser;
        set({
          user,
          activeRole: activeRole || (user.roles[0] as UserRole) || null,
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
        });
      } catch {
        // Invalid stored data, clear everything
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('active_role');
      }
    }
  },
}));
