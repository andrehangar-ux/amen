import React, { useState } from 'react';
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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Icon } from '../../src/components/Icon';
import { useTranslation } from '../../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/utils/theme';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export default function ForgotPasswordScreen() {
  const [step, setStep] = useState<'email' | 'code'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { t } = useTranslation();

  const handleSendCode = async () => {
    if (!email) {
      Alert.alert(t('error'), t('enterEmailPassword'));
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Errore');
      }
      Alert.alert('', t('codeSent'));
      setStep('code');
    } catch (error: any) {
      Alert.alert(t('error'), error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!code || !newPassword || !confirmPw) {
      Alert.alert(t('error'), t('enterEmailPassword'));
      return;
    }
    if (newPassword !== confirmPw) {
      Alert.alert(t('error'), t('passwordMismatch'));
      return;
    }
    if (newPassword.length < 6) {
      Alert.alert(t('error'), 'Min 6 caratteri');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code, new_password: newPassword }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Errore');
      }
      Alert.alert('', t('passwordResetSuccess'));
      router.replace('/(auth)/login');
    } catch (error: any) {
      Alert.alert(t('error'), error.message);
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
          {/* Back Button */}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            data-testid="forgot-pw-back-btn"
          >
            <Icon name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>

          {/* Header */}
          <View style={styles.header}>
            <Icon name="lock-open-outline" size={48} color={COLORS.primary} />
            <Text style={styles.title}>{t('forgotPasswordTitle')}</Text>
            <Text style={styles.subtitle}>
              {step === 'email' ? t('forgotPasswordDesc') : t('verificationCode')}
            </Text>
          </View>

          {step === 'email' ? (
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
                  data-testid="forgot-pw-email-input"
                />
              </View>

              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleSendCode}
                disabled={loading}
                data-testid="forgot-pw-send-code-btn"
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.primaryButtonText}>{t('sendCode')}</Text>
                )}
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.form}>
              <View style={styles.inputContainer}>
                <Icon name="keypad-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder={t('verificationCode')}
                  placeholderTextColor={COLORS.textMuted}
                  value={code}
                  onChangeText={setCode}
                  keyboardType="number-pad"
                  maxLength={6}
                  data-testid="forgot-pw-code-input"
                />
              </View>

              <View style={styles.inputContainer}>
                <Icon name="lock-closed-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder={t('newPassword')}
                  placeholderTextColor={COLORS.textMuted}
                  value={newPassword}
                  onChangeText={setNewPassword}
                  secureTextEntry={!showPassword}
                  data-testid="forgot-pw-new-password-input"
                />
                <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                  <Icon name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color={COLORS.textLight} />
                </TouchableOpacity>
              </View>

              <View style={styles.inputContainer}>
                <Icon name="lock-closed-outline" size={20} color={COLORS.textLight} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder={t('confirmPassword')}
                  placeholderTextColor={COLORS.textMuted}
                  value={confirmPw}
                  onChangeText={setConfirmPw}
                  secureTextEntry={!showPassword}
                  data-testid="forgot-pw-confirm-password-input"
                />
              </View>

              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleResetPassword}
                disabled={loading}
                data-testid="forgot-pw-reset-btn"
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.primaryButtonText}>{t('resetPassword')}</Text>
                )}
              </TouchableOpacity>

              <TouchableOpacity onPress={() => setStep('email')} data-testid="forgot-pw-resend-btn">
                <Text style={styles.resendText}>{t('sendCode')}</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Back to Login */}
          <View style={styles.footer}>
            <TouchableOpacity onPress={() => router.replace('/(auth)/login')} data-testid="forgot-pw-back-login-btn">
              <Text style={styles.linkText}>{t('backToLogin')}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  keyboardView: { flex: 1 },
  scrollContent: { flexGrow: 1, padding: SPACING.lg, justifyContent: 'center' },
  backButton: { position: 'absolute', top: 0, left: 0, padding: SPACING.sm },
  header: { alignItems: 'center', marginBottom: SPACING.xxl },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.primary, marginTop: SPACING.md },
  subtitle: { fontSize: 15, color: COLORS.textLight, textAlign: 'center', marginTop: SPACING.xs, paddingHorizontal: SPACING.lg },
  form: { gap: SPACING.md },
  inputContainer: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md, paddingHorizontal: SPACING.md,
    borderWidth: 1, borderColor: COLORS.border, height: 56,
  },
  inputIcon: { marginRight: SPACING.sm },
  input: { flex: 1, fontSize: 16, color: COLORS.text },
  primaryButton: {
    backgroundColor: COLORS.primary, borderRadius: BORDER_RADIUS.md,
    height: 56, justifyContent: 'center', alignItems: 'center', marginTop: SPACING.sm,
  },
  primaryButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  resendText: { color: COLORS.primary, fontSize: 14, fontWeight: '600', textAlign: 'center', marginTop: SPACING.md },
  footer: { alignItems: 'center', marginTop: SPACING.xxl },
  linkText: { color: COLORS.primary, fontSize: 14, fontWeight: '600' },
});
