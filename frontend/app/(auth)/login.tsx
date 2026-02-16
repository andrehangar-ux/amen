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

  const handleBiometricLogin = async () => {
    setLoading(true);
    try {
      const authenticated = await BiometricService.authenticate(t('biometricPrompt'));
      
      if (authenticated) {
        const credentials = await BiometricService.getCredentials();
        if (credentials) {
          await login(credentials.email, credentials.password);
          router.replace('/(tabs)');
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
      
      router.replace('/(tabs)');
    } catch (error: any) {
      Alert.alert(t('error'), error.message || t('loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      if (Platform.OS === 'web') {
        // Web flow: redirect directly to Emergent Auth with web callback
        const redirectUrl = `${window.location.origin}/auth-callback`;
        const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
        window.location.href = authUrl;
        return;
      }

      // Mobile flow: use backend bridge page that redirects to app deep link
      const appSchemeUrl = Linking.createURL('auth-callback');
      // Extract scheme from the deep link URL (e.g. "amen" from "amen://auth-callback")
      const schemeMatch = appSchemeUrl.match(/^([^:]+):\/\//);
      const scheme = schemeMatch ? schemeMatch[1] : 'amen';

      const redirectUrl = `${API_URL}/api/auth/mobile-redirect?scheme=${encodeURIComponent(scheme)}`;
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;

      console.log('Mobile Google auth - scheme:', scheme);
      console.log('Mobile Google auth - appSchemeUrl:', appSchemeUrl);
      console.log('Mobile Google auth - redirectUrl:', redirectUrl);

      const result = await WebBrowser.openAuthSessionAsync(authUrl, appSchemeUrl);

      console.log('Auth result:', result.type);

      if (result.type === 'success' && result.url) {
        console.log('Auth redirect URL:', result.url);

        // Parse session_id from the returned URL
        let sessionId: string | null = null;
        for (const pattern of [/[?&#]session_id=([^&]+)/, /session_id=([^&]+)/]) {
          const match = result.url.match(pattern);
          if (match) { sessionId = match[1]; break; }
        }

        if (sessionId) {
          await googleLogin(sessionId);
          router.replace('/(tabs)');
        } else {
          console.error('No session_id in URL:', result.url);
          Alert.alert(t('error'), t('googleSessionNotFound'));
        }
      } else if (result.type === 'cancel' || result.type === 'dismiss') {
        console.log('User cancelled/dismissed Google login');
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

            <TouchableOpacity
              onPress={() => router.push('/(auth)/forgot-password')}
              style={styles.forgotPasswordLink}
              data-testid="forgot-password-link"
            >
              <Text style={styles.forgotPasswordText}>{t('forgotPassword')}</Text>
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
  forgotPasswordLink: {
    alignSelf: 'flex-end',
  },
  forgotPasswordText: {
    color: COLORS.primary,
    fontSize: 13,
    fontWeight: '500',
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
