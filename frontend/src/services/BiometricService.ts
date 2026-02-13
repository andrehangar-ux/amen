import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const CREDENTIALS_KEY = 'amen_user_credentials';
const BIOMETRIC_ENABLED_KEY = 'amen_biometric_enabled';

export interface StoredCredentials {
  email: string;
  password: string;
}

export const BiometricService = {
  // Check if biometric authentication is available
  async isAvailable(): Promise<boolean> {
    if (Platform.OS === 'web') {
      return false; // Biometrics not available on web
    }
    
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      return compatible && enrolled;
    } catch (error) {
      console.log('Biometric check error:', error);
      return false;
    }
  },

  // Get supported authentication types
  async getSupportedTypes(): Promise<string[]> {
    if (Platform.OS === 'web') {
      return [];
    }
    
    try {
      const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
      const typeNames: string[] = [];
      
      if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        typeNames.push('fingerprint');
      }
      if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        typeNames.push('face');
      }
      if (types.includes(LocalAuthentication.AuthenticationType.IRIS)) {
        typeNames.push('iris');
      }
      
      return typeNames;
    } catch (error) {
      console.log('Get supported types error:', error);
      return [];
    }
  },

  // Authenticate with biometrics
  async authenticate(promptMessage: string = 'Accedi con biometria'): Promise<boolean> {
    if (Platform.OS === 'web') {
      return false;
    }
    
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage,
        cancelLabel: 'Annulla',
        disableDeviceFallback: false,
        fallbackLabel: 'Usa password',
      });
      
      return result.success;
    } catch (error) {
      console.log('Biometric auth error:', error);
      return false;
    }
  },

  // Save credentials securely
  async saveCredentials(email: string, password: string): Promise<boolean> {
    if (Platform.OS === 'web') {
      // For web, use localStorage as fallback (less secure but functional)
      try {
        localStorage.setItem(CREDENTIALS_KEY, JSON.stringify({ email, password }));
        return true;
      } catch (error) {
        console.log('Web storage error:', error);
        return false;
      }
    }
    
    try {
      const credentials = JSON.stringify({ email, password });
      await SecureStore.setItemAsync(CREDENTIALS_KEY, credentials);
      return true;
    } catch (error) {
      console.log('Save credentials error:', error);
      return false;
    }
  },

  // Get saved credentials
  async getCredentials(): Promise<StoredCredentials | null> {
    if (Platform.OS === 'web') {
      try {
        const stored = localStorage.getItem(CREDENTIALS_KEY);
        if (stored) {
          return JSON.parse(stored);
        }
        return null;
      } catch (error) {
        console.log('Web storage read error:', error);
        return null;
      }
    }
    
    try {
      const credentials = await SecureStore.getItemAsync(CREDENTIALS_KEY);
      if (credentials) {
        return JSON.parse(credentials);
      }
      return null;
    } catch (error) {
      console.log('Get credentials error:', error);
      return null;
    }
  },

  // Delete saved credentials
  async deleteCredentials(): Promise<boolean> {
    if (Platform.OS === 'web') {
      try {
        localStorage.removeItem(CREDENTIALS_KEY);
        localStorage.removeItem(BIOMETRIC_ENABLED_KEY);
        return true;
      } catch (error) {
        console.log('Web storage delete error:', error);
        return false;
      }
    }
    
    try {
      await SecureStore.deleteItemAsync(CREDENTIALS_KEY);
      await SecureStore.deleteItemAsync(BIOMETRIC_ENABLED_KEY);
      return true;
    } catch (error) {
      console.log('Delete credentials error:', error);
      return false;
    }
  },

  // Check if biometric login is enabled by user
  async isBiometricEnabled(): Promise<boolean> {
    if (Platform.OS === 'web') {
      try {
        return localStorage.getItem(BIOMETRIC_ENABLED_KEY) === 'true';
      } catch {
        return false;
      }
    }
    
    try {
      const enabled = await SecureStore.getItemAsync(BIOMETRIC_ENABLED_KEY);
      return enabled === 'true';
    } catch (error) {
      console.log('Check biometric enabled error:', error);
      return false;
    }
  },

  // Set biometric login preference
  async setBiometricEnabled(enabled: boolean): Promise<boolean> {
    if (Platform.OS === 'web') {
      try {
        localStorage.setItem(BIOMETRIC_ENABLED_KEY, enabled ? 'true' : 'false');
        return true;
      } catch {
        return false;
      }
    }
    
    try {
      await SecureStore.setItemAsync(BIOMETRIC_ENABLED_KEY, enabled ? 'true' : 'false');
      return true;
    } catch (error) {
      console.log('Set biometric enabled error:', error);
      return false;
    }
  },

  // Check if user has saved credentials for biometric login
  async hasSavedCredentials(): Promise<boolean> {
    const credentials = await this.getCredentials();
    return credentials !== null;
  },
};

export default BiometricService;
