import { create } from 'zustand';
import { api } from '../utils/api';

interface ConsentState {
  hasAccepted: boolean | null;  // null = not checked yet
  isChecking: boolean;
  checkConsent: () => Promise<boolean>;
  acceptTerms: () => Promise<void>;
  reset: () => void;
}

export const useConsentStore = create<ConsentState>((set, get) => ({
  hasAccepted: null,
  isChecking: false,

  checkConsent: async () => {
    set({ isChecking: true });
    try {
      const status = await api.getConsentStatus();
      const accepted = status.accepted === true;
      set({ hasAccepted: accepted, isChecking: false });
      return accepted;
    } catch (error) {
      console.log('Error checking consent:', error);
      // If error, assume not accepted to be safe
      set({ hasAccepted: false, isChecking: false });
      return false;
    }
  },

  acceptTerms: async () => {
    try {
      await api.acceptTerms('1.0');
      set({ hasAccepted: true });
    } catch (error) {
      console.log('Error accepting terms:', error);
      throw error;
    }
  },

  reset: () => {
    set({ hasAccepted: null, isChecking: false });
  },
}));
