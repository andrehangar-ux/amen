import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

interface User {
  user_id: string;
  email: string;
  name: string;
  picture?: string;
  preferred_bible: string;
  language: string;
}

interface AuthState {
  user: User | null;
  sessionToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setSessionToken: (token: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  googleLogin: (sessionId: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  sessionToken: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setSessionToken: (token) => set({ sessionToken: token }),

  login: async (email, password) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login fallito');
      }
      
      const data = await response.json();
      await AsyncStorage.setItem('session_token', data.session_token);
      set({ user: data.user, sessionToken: data.session_token, isAuthenticated: true });
    } catch (error) {
      throw error;
    }
  },

  register: async (email, password, name) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registrazione fallita');
      }
      
      const data = await response.json();
      await AsyncStorage.setItem('session_token', data.session_token);
      set({ user: data.user, sessionToken: data.session_token, isAuthenticated: true });
    } catch (error) {
      throw error;
    }
  },

  googleLogin: async (sessionId) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/google-callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login Google fallito');
      }
      
      const data = await response.json();
      await AsyncStorage.setItem('session_token', data.session_token);
      set({ user: data.user, sessionToken: data.session_token, isAuthenticated: true });
    } catch (error) {
      throw error;
    }
  },

  logout: async () => {
    try {
      const token = get().sessionToken || await AsyncStorage.getItem('session_token');
      if (token) {
        await fetch(`${API_URL}/api/auth/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        });
      }
    } catch (e) {
      console.log('Logout error:', e);
    } finally {
      await AsyncStorage.removeItem('session_token');
      set({ user: null, sessionToken: null, isAuthenticated: false });
    }
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const token = await AsyncStorage.getItem('session_token');
      if (!token) {
        set({ isLoading: false });
        return;
      }
      
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const user = await response.json();
        set({ user, sessionToken: token, isAuthenticated: true, isLoading: false });
      } else {
        await AsyncStorage.removeItem('session_token');
        set({ isLoading: false });
      }
    } catch (error) {
      console.log('Check auth error:', error);
      set({ isLoading: false });
    }
  },
}));
