import { create } from 'zustand';
import { useChatStore } from './chatStore';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export interface UserProfile {
  user_id: string;
  name: string;
  email: string;
  phone_number?: string | null;
  refresh_token?: string | null;
  current_list_of_the_stocks?: any[];
  goals?: any[];
  user_chat_history?: Record<string, any>;
  recently_veiwed_stock?: any[];
}

interface UserState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  authModalMode: 'login' | 'signup';
  authError: string | null;

  // Modal actions
  openAuthModal: (mode?: 'login' | 'signup') => void;
  closeAuthModal: () => void;
  setAuthModalMode: (mode: 'login' | 'signup') => void;
  clearAuthError: () => void;

  // Auth actions
  login: (email: string, password: string) => Promise<{ success: boolean; message?: string }>;
  signup: (
    name: string,
    email: string,
    password: string,
    phoneNumber?: string
  ) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
  initAuth: () => void;
}

const STORAGE_USER_KEY = 'growwise_user';
const STORAGE_TOKEN_KEY = 'growwise_token';

export const useUserStore = create<UserState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  isAuthModalOpen: false,
  authModalMode: 'login',
  authError: null,

  openAuthModal: (mode = 'login') => {
    set({
      isAuthModalOpen: true,
      authModalMode: mode,
      authError: null,
    });
  },

  closeAuthModal: () => {
    set({
      isAuthModalOpen: false,
      authError: null,
    });
  },

  setAuthModalMode: (mode) => {
    set({
      authModalMode: mode,
      authError: null,
    });
  },

  clearAuthError: () => {
    set({ authError: null });
  },

  initAuth: () => {
    try {
      const storedUser = localStorage.getItem(STORAGE_USER_KEY);
      const storedToken = localStorage.getItem(STORAGE_TOKEN_KEY);
      if (storedUser && storedToken) {
        const parsedUser: UserProfile = JSON.parse(storedUser);
        set({
          user: parsedUser,
          token: storedToken,
          isAuthenticated: true,
        });
        useChatStore.getState().setUserId(parsedUser.user_id);
      }
    } catch (e) {
      console.warn('[useUserStore] Failed to restore session from localStorage:', e);
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, authError: null });
    try {
      const res = await fetch(`${API_BASE}/api/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      const data = await res.json();
      if (!res.ok || data.status !== 'success') {
        const message = data.detail || data.message || 'Invalid email or password.';
        set({ isLoading: false, authError: message });
        return { success: false, message };
      }

      const user: UserProfile = data.user;
      const token: string = data.token || user.refresh_token || '';

      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
      localStorage.setItem(STORAGE_TOKEN_KEY, token);
      localStorage.setItem('growwise_user_id', user.user_id);

      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        isAuthModalOpen: false,
        authError: null,
      });

      // Synchronize active chat userId with logged-in user profile
      useChatStore.getState().setUserId(user.user_id);

      return { success: true };
    } catch (err: any) {
      const msg = err.message || 'Failed to connect to authentication server.';
      set({ isLoading: false, authError: msg });
      return { success: false, message: msg };
    }
  },

  signup: async (name: string, email: string, password: string, phoneNumber?: string) => {
    set({ isLoading: true, authError: null });
    try {
      const res = await fetch(`${API_BASE}/api/users/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          phone_number: phoneNumber?.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok || data.status !== 'success') {
        const message = data.detail || data.message || 'Registration failed.';
        set({ isLoading: false, authError: message });
        return { success: false, message };
      }

      const user: UserProfile = data.user;
      const token: string = data.token || user.refresh_token || '';

      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
      localStorage.setItem(STORAGE_TOKEN_KEY, token);
      localStorage.setItem('growwise_user_id', user.user_id);

      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        isAuthModalOpen: false,
        authError: null,
      });

      // Synchronize active chat userId with logged-in user profile
      useChatStore.getState().setUserId(user.user_id);

      return { success: true };
    } catch (err: any) {
      const msg = err.message || 'Failed to connect to authentication server.';
      set({ isLoading: false, authError: msg });
      return { success: false, message: msg };
    }
  },

  logout: () => {
    localStorage.removeItem(STORAGE_USER_KEY);
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    
    // Assign a fresh guest ID for non-authenticated sessions
    const freshGuestId = `guest_${crypto.randomUUID()}`;
    localStorage.setItem('growwise_user_id', freshGuestId);
    useChatStore.getState().setUserId(freshGuestId);

    set({
      user: null,
      token: null,
      isAuthenticated: false,
      authError: null,
    });
  },
}));
