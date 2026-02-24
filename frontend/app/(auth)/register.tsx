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
  Switch,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, Link } from 'expo-router';
import { Icon } from '../../src/components/Icon';
import { useAuthStore } from '../../src/store/authStore';
import { useTranslation } from '../../src/store/languageStore';
import { BiometricService } from '../../src/services/BiometricService';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';

// Cross-platform alert
const showAlert = (title: string, message: string) => {
  if (Platform.OS === 'web') {
    window.alert(`${title}\n\n${message}`);
  } else {
    Alert.alert(title, message);
  }
};

export default function RegisterScreen() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [enableBiometric, setEnableBiometric] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showSafetyReminder, setShowSafetyReminder] = useState(false);
  const { register } = useAuthStore();
  const { t } = useTranslation();

  // Calculate if user is minor
  const calculateAge = (dateStr: string): number | null => {
    if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return null;
    try {
      const birth = new Date(dateStr);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
        age--;
      }
      return age;
    } catch {
      return null;
    }
  };

  const isMinor = calculateAge(birthDate) !== null && (calculateAge(birthDate) || 0) < 18;

  useEffect(() => {
    checkBiometricAvailability();
  }, []);

  const checkBiometricAvailability = async () => {
    const available = await BiometricService.isAvailable();
    setBiometricAvailable(available);
  };

  const handleRegister = async () => {
    if (!name || !email || !password) {
      showAlert(t('error'), t('fillAllFieldsError'));
      return;
    }

    if (password !== confirmPassword) {
      showAlert(t('error'), t('passwordMismatchError'));
      return;
    }

    if (password.length < 6) {
      showAlert(t('error'), t('passwordMinLengthError'));
      return;
    }

    if (!acceptedTerms) {
      showAlert(t('error'), t('acceptTermsRequired') || 'Devi accettare i Termini e le Condizioni');
      return;
    }

    setLoading(true);
    try {
      await register(email, password, name);
      
      // Save credentials if biometric is enabled
      if (enableBiometric && biometricAvailable) {
        await BiometricService.setBiometricEnabled(true);
        await BiometricService.saveCredentials(email, password);
      }
      
      router.replace('/(tabs)');
    } catch (error: any) {
      showAlert(t('error'), error.message || t('registrationFailed'));
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
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => router.back()}
              data-testid="register-back-button"
            >
              <Icon name="arrow-back" size={24} color={COLORS.text} />
            </TouchableOpacity>
            <View style={styles.logoContainer}>
              <Image 
                source={require('../../assets/images/logo.jpg')} 
                style={styles.logoImage}
                resizeMode="contain"
              />
            </View>
            <Text style={styles.title}>{t('createAccount')}</Text>
            <Text style={styles.subtitle}>{t('startSpiritualJourney')}</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Icon name="person-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('fullName')}
                placeholderTextColor={COLORS.textMuted}
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
                data-testid="register-name-input"
              />
            </View>

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
                data-testid="register-email-input"
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
                data-testid="register-password-input"
              />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                <Icon
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={20}
                  color={COLORS.textLight}
                />
              </TouchableOpacity>
            </View>

            <View style={styles.inputContainer}>
              <Icon name="shield-checkmark-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder={t('confirmPassword')}
                placeholderTextColor={COLORS.textMuted}
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry={!showPassword}
                data-testid="register-confirm-password-input"
              />
            </View>

            {/* Biometric Option - only shown on mobile */}
            {biometricAvailable && (
              <View style={styles.biometricOption}>
                <View style={styles.biometricOptionLeft}>
                  <Icon name="finger-print" size={24} color={COLORS.primary} />
                  <Text style={styles.biometricOptionText}>{t('enableBiometric')}</Text>
                </View>
                <Switch
                  value={enableBiometric}
                  onValueChange={setEnableBiometric}
                  trackColor={{ false: COLORS.border, true: COLORS.primary + '50' }}
                  thumbColor={enableBiometric ? COLORS.primary : COLORS.textMuted}
                  data-testid="biometric-switch"
                />
              </View>
            )}

            {/* Terms and Conditions */}
            <View style={styles.termsContainer}>
              <Pressable
                style={styles.checkbox}
                onPress={() => setAcceptedTerms(!acceptedTerms)}
                data-testid="terms-checkbox"
              >
                <Text style={styles.checkboxIcon}>
                  {acceptedTerms ? '☑️' : '⬜'}
                </Text>
              </Pressable>
              <View style={styles.termsTextContainer}>
                <Text style={styles.termsText}>
                  {t('iAccept') || 'Accetto i'}{' '}
                </Text>
                <Pressable onPress={() => router.push('/privacy')}>
                  <Text style={styles.termsLink}>
                    {t('termsAndConditions') || 'Termini e Condizioni'}
                  </Text>
                </Pressable>
              </View>
            </View>

            <TouchableOpacity
              style={[styles.primaryButton, !acceptedTerms && styles.primaryButtonDisabled]}
              onPress={handleRegister}
              disabled={loading || !acceptedTerms}
              data-testid="register-submit-button"
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.primaryButtonText}>{t('registerButton')}</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>{t('alreadyHaveAccount')}</Text>
            <TouchableOpacity onPress={() => router.back()} data-testid="login-link">
              <Text style={styles.linkText}>{t('loginButton')}</Text>
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
  },
  header: {
    alignItems: 'center',
    marginBottom: SPACING.xl,
  },
  backButton: {
    position: 'absolute',
    left: 0,
    top: 0,
    padding: SPACING.sm,
  },
  logoContainer: {
    width: 100,
    height: 100,
    borderRadius: BORDER_RADIUS.xl,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
    marginTop: SPACING.xl,
    ...SHADOWS.medium,
    overflow: 'hidden',
  },
  logoImage: {
    width: 100,
    height: 100,
    borderRadius: BORDER_RADIUS.xl,
  },
  title: {
    fontSize: 28,
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
  biometricOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    marginTop: SPACING.xs,
  },
  biometricOptionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  biometricOptionText: {
    fontSize: 14,
    color: COLORS.text,
    fontWeight: '500',
  },
  primaryButtonDisabled: {
    opacity: 0.5,
  },
  termsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.md,
    paddingHorizontal: SPACING.xs,
  },
  checkbox: {
    marginRight: SPACING.sm,
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxIcon: {
    fontSize: 22,
  },
  termsTextContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    flex: 1,
  },
  termsText: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  termsLink: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
