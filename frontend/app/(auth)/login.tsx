import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Icon } from '../../src/components/Icon';
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { useAuthStore } from '../../src/store/authStore';
import { useTranslation } from '../../src/store/languageStore';
import { BiometricService } from '../../src/services/BiometricService';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';
import { TermsModal } from '../../src/components/TermsModal';
import { api } from '../../src/utils/api';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [hasSavedCredentials, setHasSavedCredentials] = useState(false);
  const { login, googleLogin } = useAuthStore();
  const { t } = useTranslation();

  useEffect(() => {
    checkBiometric();
  }, []);

  const checkBiometric = async () => {
    const available = await BiometricService.isAvailable();
    const enabled = await BiometricService.isBiometricEnabled();
    const hasCredentials = await BiometricService.hasSavedCredentials();
    
    setBiometricAvailable(available && enabled);
    setHasSavedCredentials(hasCredentials);
    
    // Auto-trigger biometric login if available and enabled
    if (available && enabled && hasCredentials) {
      handleBiometricLogin();
    }
  };

  // Check consent and navigate
  const checkConsentAndNavigate = async () => {
    console.log('[Login] Navigating to index for consent check');
    // Navigate to index, which will handle consent check
    router.replace('/');
  };

  const handleTermsAccept = () => {
    setShowTermsModal(false);
    if (pendingNavigation) {
      setPendingNavigation(false);
      router.replace('/(tabs)');
    }
  };

  const handleBiometricLogin = async () => {
    setLoading(true);
    try {
      const authenticated = await BiometricService.authenticate(t('biometricPrompt'));
      
      if (authenticated) {
        const credentials = await BiometricService.getCredentials();
        if (credentials) {
          await login(credentials.email, credentials.password);
          await checkConsentAndNavigate();
        }
      }
    } catch (error: any) {
      Alert.alert(t('error'), error.message || t('biometricFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert(t('error'), t('enterEmailPassword'));
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      
      // Save credentials if biometric is enabled
      const biometricEnabled = await BiometricService.isBiometricEnabled();
      if (biometricEnabled) {
        await BiometricService.saveCredentials(email, password);
      }
      
      // Check consent before navigating
      await checkConsentAndNavigate();
    } catch (error: any) {
      Alert.alert(t('error'), error.message || t('loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      // Build redirect URL using window.location.origin only (required for OAuth)
      // On native platforms, use Linking to get the app URL
      let redirectUrl: string;
      
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location?.origin) {
        redirectUrl = `${window.location.origin}/auth-callback`;
      } else {
        // For native platforms, use the backend URL
        const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
        redirectUrl = backendUrl ? `${backendUrl}/auth-callback` : '';
      }
      
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      
      console.log('Starting Google auth with redirect:', redirectUrl);
      
      if (Platform.OS === 'web') {
        // Per il web, facciamo un redirect diretto
        window.location.href = authUrl;
        return;
      }
      
      // Per mobile (Expo Go), usiamo WebBrowser
      const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
      
      console.log('Auth result type:', result.type);
      
      if (result.type === 'success' && result.url) {
        console.log('Full redirect URL:', result.url);
        
        // Parse session_id from URL
        let sessionId = null;
        const url = result.url;
        
        const patterns = [
          /#session_id=([^&]+)/,
          /\?session_id=([^&]+)/,
          /session_id=([^&]+)/
        ];
        
        for (const pattern of patterns) {
          const match = url.match(pattern);
          if (match) {
            sessionId = match[1];
            console.log('Found session_id with pattern:', pattern);
            break;
          }
        }
        
        if (sessionId) {
          try {
            await googleLogin(sessionId);
            router.replace('/(tabs)');
          } catch (loginError: any) {
            console.error('Google login API error:', loginError);
            Alert.alert(t('error'), loginError.message || t('googleLoginFailed'));
          }
        } else {
          console.error('No session_id in URL:', url);
          Alert.alert(t('error'), t('googleSessionNotFound'));
        }
      } else if (result.type === 'cancel') {
        console.log('User cancelled Google login');
      }
    } catch (error: any) {
      console.error('Google login error:', error);
      Alert.alert(t('error'), error.message || t('googleLoginFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.logoContainer}>
              <Image 
                source={require('../../assets/images/logo.jpg')} 
                style={styles.logoImage}
                resizeMode="contain"
              />
            </View>
            <Text style={styles.subtitle}>{t('dailySpiritualCompanion')}</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Icon name="mail-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('email')}
                placeholderTextColor={COLORS.textMuted}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                data-testid="login-email-input"
              />
            </View>

            <View style={styles.inputContainer}>
              <Icon name="lock-closed-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor={COLORS.textMuted}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                data-testid="login-password-input"
              />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                <Icon
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={20}
                  color={COLORS.textLight}
                />
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.primaryButton}
              onPress={handleLogin}
              disabled={loading}
              data-testid="login-submit-button"
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.primaryButtonText}>{t('loginButton')}</Text>
              )}
            </TouchableOpacity>

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>{t('orDivider')}</Text>
              <View style={styles.dividerLine} />
            </View>

            <TouchableOpacity
              style={styles.googleButton}
              onPress={handleGoogleLogin}
              disabled={loading}
              data-testid="google-login-button"
            >
              <Icon name="logo-google" size={20} color={COLORS.text} />
              <Text style={styles.googleButtonText}>{t('continueWithGoogle')}</Text>
            </TouchableOpacity>

            {/* Biometric Login Button */}
            {biometricAvailable && hasSavedCredentials && (
              <TouchableOpacity
                style={styles.biometricButton}
                onPress={handleBiometricLogin}
                disabled={loading}
                data-testid="biometric-login-button"
              >
                <Icon name="finger-print" size={24} color={COLORS.primary} />
                <Text style={styles.biometricButtonText}>{t('biometricLogin')}</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>{t('noAccount')}</Text>
            <TouchableOpacity onPress={() => router.push('/(auth)/register')} data-testid="register-link">
              <Text style={styles.linkText}>{t('registerButton')}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
      
      {/* Terms Modal */}
      <TermsModal 
        visible={showTermsModal} 
        onAccept={handleTermsAccept} 
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: SPACING.lg,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: SPACING.xxl,
  },
  logoContainer: {
    width: 120,
    height: 120,
    borderRadius: BORDER_RADIUS.xl,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
    ...SHADOWS.medium,
    overflow: 'hidden',
  },
  logoImage: {
    width: 120,
    height: 120,
    borderRadius: BORDER_RADIUS.xl,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textLight,
    textAlign: 'center',
  },
  form: {
    gap: SPACING.md,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    height: 56,
  },
  inputIcon: {
    marginRight: SPACING.sm,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SPACING.sm,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: SPACING.md,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },
  dividerText: {
    marginHorizontal: SPACING.md,
    color: COLORS.textMuted,
    fontSize: 14,
  },
  googleButton: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: SPACING.sm,
  },
  googleButtonText: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: '500',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SPACING.xxl,
    gap: SPACING.xs,
  },
  footerText: {
    color: COLORS.textLight,
    fontSize: 14,
  },
  linkText: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  biometricButton: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.md,
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.primary + '30',
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  biometricButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '500',
  },
});
