import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { useTranslation, useLanguageStore } from '../src/store/languageStore';
import { api } from '../src/utils/api';
import { NotificationService } from '../src/services/NotificationService';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

// Helper to show long text alerts
const showInfoAlert = (title: string, message: string, buttonText: string) => {
  if (Platform.OS === 'web') {
    window.alert(`${title}\n\n${message}`);
  } else {
    Alert.alert(title, message, [{ text: buttonText, style: 'default' }]);
  }
};

// Cross-platform confirm dialog
const showConfirm = (title: string, message: string, onConfirm: () => void, cancelText: string, confirmText: string) => {
  if (Platform.OS === 'web') {
    const confirmed = window.confirm(`${title}\n\n${message}`);
    if (confirmed) {
      onConfirm();
    }
  } else {
    Alert.alert(title, message, [
      { text: cancelText, style: 'cancel' },
      { text: confirmText, style: 'destructive', onPress: onConfirm },
    ]);
  }
};

const LANGUAGES = [
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
];

const BIBLE_EDITIONS = [
  { id: 'nuova_diodati', name: 'Nuova Diodati', language: 'it' },
  { id: 'reina_valera', name: 'Reina Valera 1960', language: 'es' },
  { id: 'kjv', name: 'King James Version', language: 'en' },
  { id: 'schlachter', name: 'Schlachter', language: 'de' },
  { id: 'louis_segond', name: 'Louis Segond', language: 'fr' },
  { id: 'acf', name: 'Almeida Corrigida Fiel', language: 'pt' },
];

export default function SettingsScreen() {
  const { user, setUser, logout, setSessionToken } = useAuthStore();
  const { t } = useTranslation();
  const { setLanguage: setGlobalLanguage, currentLanguage } = useLanguageStore();
  const [name, setName] = useState(user?.name || '');
  const [language, setLanguageState] = useState(user?.language || currentLanguage || 'it');
  const [preferredBible, setPreferredBible] = useState(user?.preferred_bible || 'nuova_diodati');
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [dailyVerseEnabled, setDailyVerseEnabled] = useState(false);
  const [notificationHour, setNotificationHour] = useState(7);
  const [notificationMinute, setNotificationMinute] = useState(0);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showLanguages, setShowLanguages] = useState(false);
  const [showBibles, setShowBibles] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);

  // Load notification settings on mount
  useEffect(() => {
    loadNotificationSettings();
  }, []);

  const loadNotificationSettings = async () => {
    const isEnabled = await NotificationService.isDailyVerseEnabled();
    const time = await NotificationService.getNotificationTime();
    setDailyVerseEnabled(isEnabled);
    setNotificationsEnabled(isEnabled);
    setNotificationHour(time.hour);
    setNotificationMinute(time.minute);
  };

  const handleDailyVerseToggle = async (value: boolean) => {
    setDailyVerseEnabled(value);
    setNotificationsEnabled(value);
    
    if (value) {
      const success = await NotificationService.scheduleDailyVerseNotification(
        notificationHour,
        notificationMinute
      );
      if (!success) {
        setDailyVerseEnabled(false);
        setNotificationsEnabled(false);
        if (Platform.OS === 'web') {
          window.alert(t('notificationPermissionDenied') || 'Permessi notifiche non concessi. Abilita le notifiche nelle impostazioni del browser.');
        } else {
          Alert.alert(
            t('error'),
            t('notificationPermissionDenied') || 'Permessi notifiche non concessi. Abilita le notifiche nelle impostazioni.'
          );
        }
      } else {
        if (Platform.OS === 'web') {
          window.alert(`Notifica versetto del giorno programmata per le ${notificationHour}:${notificationMinute.toString().padStart(2, '0')}`);
        } else {
          Alert.alert(
            t('saved'),
            `Notifica versetto del giorno programmata per le ${notificationHour}:${notificationMinute.toString().padStart(2, '0')}`
          );
        }
      }
    } else {
      await NotificationService.cancelDailyVerseNotification();
    }
  };

  const handleTimeChange = async (hour: number, minute: number) => {
    setNotificationHour(hour);
    setNotificationMinute(minute);
    setShowTimePicker(false);
    
    if (dailyVerseEnabled) {
      await NotificationService.scheduleDailyVerseNotification(hour, minute);
    }
  };

  const handleTestNotification = async () => {
    try {
      await NotificationService.sendTestNotification();
      if (Platform.OS === 'web') {
        window.alert('Notifica di test inviata!');
      }
    } catch (error: any) {
      if (Platform.OS === 'web') {
        window.alert(error.message);
      } else {
        Alert.alert(t('error'), error.message);
      }
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      // Update global language immediately for UI to reflect
      await setGlobalLanguage(language);
      
      const updatedUser = await api.updateSettings({
        name,
        language,
        preferred_bible: preferredBible,
      });
      if (updatedUser) {
        setUser(updatedUser);
      }
      if (Platform.OS === 'web') {
        window.alert(t('settingsUpdated'));
      } else {
        Alert.alert(t('saved'), t('settingsUpdated'));
      }
    } catch (error) {
      console.log('Save settings error:', error);
      // Still update language locally even if API fails
      await setGlobalLanguage(language);
      if (Platform.OS === 'web') {
        window.alert(t('settingsUpdated'));
      } else {
        Alert.alert(t('saved'), t('settingsUpdated'));
      }
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    showConfirm(
      t('disconnect'),
      t('disconnectConfirm'),
      async () => {
        try {
          await logout();
          setUser(null);
          setSessionToken(null);
          router.replace('/(auth)/login');
        } catch (error) {
          console.error('Logout error:', error);
          setUser(null);
          setSessionToken(null);
          router.replace('/(auth)/login');
        }
      },
      t('cancel'),
      t('confirm')
    );
  };

  const handleDeleteAccount = () => {
    showConfirm(
      t('deleteAccount'),
      t('deleteConfirm'),
      async () => {
        try {
          await api.deleteAccount();
          if (Platform.OS === 'web') {
            window.alert(t('accountDeleted'));
          } else {
            Alert.alert(t('deleteAccount'), t('accountDeleted'));
          }
          setUser(null);
          setSessionToken(null);
          router.replace('/(auth)/login');
        } catch (error) {
          if (Platform.OS === 'web') {
            window.alert(t('error') + ': ' + t('deleteAccountError'));
          } else {
            Alert.alert(t('error'), t('deleteAccountError'));
          }
        }
      },
      t('cancel'),
      t('confirm')
    );
  };

  const selectedLanguage = LANGUAGES.find(l => l.code === language);
  const selectedBible = BIBLE_EDITIONS.find(b => b.id === preferredBible);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Icon name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('settings')}</Text>
        <TouchableOpacity onPress={saveSettings} disabled={saving}>
          {saving ? (
            <ActivityIndicator size="small" color={COLORS.primary} />
          ) : (
            <Text style={styles.saveButton}>{t('save')}</Text>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.sectionTitle}>{t('profile')}</Text>
        <View style={styles.card}>
          <Text style={styles.fieldLabel}>{t('yourName')}</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder={t('yourName')}
            placeholderTextColor={COLORS.textMuted}
          />
        </View>

        <Text style={styles.sectionTitle}>{t('language')}</Text>
        <TouchableOpacity
          style={styles.card}
          onPress={() => setShowLanguages(!showLanguages)}
        >
          <View style={styles.selectRow}>
            <Text style={styles.selectLabel}>{t('appLanguage')}</Text>
            <View style={styles.selectValue}>
              <Text style={styles.selectFlag}>{selectedLanguage?.flag}</Text>
              <Text style={styles.selectText}>{selectedLanguage?.name}</Text>
              <Icon
                name={showLanguages ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={COLORS.textMuted}
              />
            </View>
          </View>

          {showLanguages && (
            <View style={styles.optionsList}>
              {LANGUAGES.map((lang) => (
                <TouchableOpacity
                  key={lang.code}
                  style={[
                    styles.optionItem,
                    language === lang.code && styles.optionItemSelected,
                  ]}
                  onPress={() => {
                    setLanguageState(lang.code);
                    setShowLanguages(false);
                  }}
                >
                  <Text style={styles.optionFlag}>{lang.flag}</Text>
                  <Text style={styles.optionText}>{lang.name}</Text>
                  {language === lang.code && (
                    <Icon name="checkmark" size={20} color={COLORS.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </TouchableOpacity>

        <Text style={styles.sectionTitle}>{t('bible')}</Text>
        <TouchableOpacity
          style={styles.card}
          onPress={() => setShowBibles(!showBibles)}
        >
          <View style={styles.selectRow}>
            <Text style={styles.selectLabel}>{t('preferredEdition')}</Text>
            <View style={styles.selectValue}>
              <Text style={styles.selectText}>{selectedBible?.name}</Text>
              <Icon
                name={showBibles ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={COLORS.textMuted}
              />
            </View>
          </View>

          {showBibles && (
            <View style={styles.optionsList}>
              {BIBLE_EDITIONS.map((bible) => (
                <TouchableOpacity
                  key={bible.id}
                  style={[
                    styles.optionItem,
                    preferredBible === bible.id && styles.optionItemSelected,
                  ]}
                  onPress={() => {
                    setPreferredBible(bible.id);
                    setShowBibles(false);
                  }}
                >
                  <Text style={styles.optionText}>{bible.name}</Text>
                  {preferredBible === bible.id && (
                    <Icon name="checkmark" size={20} color={COLORS.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </TouchableOpacity>

        <Text style={styles.sectionTitle}>{t('notifications')}</Text>
        <View style={styles.card}>
          <View style={styles.switchRow}>
            <View style={styles.switchContent}>
              <Text style={styles.switchLabel}>{t('dailyVerseNotification')}</Text>
              <Text style={styles.switchDescription}>{t('receiveVerse')}</Text>
            </View>
            <Switch
              value={dailyVerseEnabled}
              onValueChange={handleDailyVerseToggle}
              trackColor={{ false: COLORS.border, true: COLORS.primary }}
              thumbColor="#fff"
            />
          </View>

          {dailyVerseEnabled && (
            <>
              <TouchableOpacity 
                style={[styles.switchRow, { borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: SPACING.md, paddingTop: SPACING.md }]}
                onPress={() => setShowTimePicker(!showTimePicker)}
              >
                <View style={styles.switchContent}>
                  <Text style={styles.switchLabel}>{t('notificationTime') || 'Orario notifica'}</Text>
                  <Text style={styles.switchDescription}>{t('chooseTime') || 'Scegli quando ricevere il versetto'}</Text>
                </View>
                <View style={styles.timeDisplay}>
                  <Text style={styles.timeText}>
                    {notificationHour.toString().padStart(2, '0')}:{notificationMinute.toString().padStart(2, '0')}
                  </Text>
                  <Icon name={showTimePicker ? 'chevron-up' : 'chevron-down'} size={20} color={COLORS.textMuted} />
                </View>
              </TouchableOpacity>

              {showTimePicker && (
                <View style={styles.timePickerContainer}>
                  <View style={styles.timePickerRow}>
                    <View style={styles.timePickerColumn}>
                      <Text style={styles.timePickerLabel}>{t('hour') || 'Ora'}</Text>
                      <View style={styles.timePickerButtons}>
                        <TouchableOpacity 
                          style={styles.timeButton}
                          onPress={() => handleTimeChange((notificationHour + 1) % 24, notificationMinute)}
                        >
                          <Icon name="chevron-up" size={20} color={COLORS.primary} />
                        </TouchableOpacity>
                        <Text style={styles.timeValue}>{notificationHour.toString().padStart(2, '0')}</Text>
                        <TouchableOpacity 
                          style={styles.timeButton}
                          onPress={() => handleTimeChange((notificationHour + 23) % 24, notificationMinute)}
                        >
                          <Icon name="chevron-down" size={20} color={COLORS.primary} />
                        </TouchableOpacity>
                      </View>
                    </View>
                    <Text style={styles.timeSeparator}>:</Text>
                    <View style={styles.timePickerColumn}>
                      <Text style={styles.timePickerLabel}>{t('minute') || 'Minuti'}</Text>
                      <View style={styles.timePickerButtons}>
                        <TouchableOpacity 
                          style={styles.timeButton}
                          onPress={() => handleTimeChange(notificationHour, (notificationMinute + 15) % 60)}
                        >
                          <Icon name="chevron-up" size={20} color={COLORS.primary} />
                        </TouchableOpacity>
                        <Text style={styles.timeValue}>{notificationMinute.toString().padStart(2, '0')}</Text>
                        <TouchableOpacity 
                          style={styles.timeButton}
                          onPress={() => handleTimeChange(notificationHour, (notificationMinute + 45) % 60)}
                        >
                          <Icon name="chevron-down" size={20} color={COLORS.primary} />
                        </TouchableOpacity>
                      </View>
                    </View>
                  </View>
                </View>
              )}
            </>
          )}

          <TouchableOpacity 
            style={[styles.testButton, { borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: SPACING.md, paddingTop: SPACING.md }]}
            onPress={handleTestNotification}
          >
            <Icon name="notifications" size={20} color={COLORS.primary} />
            <Text style={styles.testButtonText}>{t('sendTestNotification') || 'Invia notifica di test'}</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.sectionTitle}>{t('info')}</Text>
        <View style={styles.card}>
          <Text style={styles.infoText}>{t('email')}: {user?.email}</Text>
          <Text style={styles.infoText}>{t('appVersion')}: 1.0.0</Text>
        </View>

        {/* Privacy & Legal Section */}
        <Text style={styles.sectionTitle}>{t('privacyLegal')}</Text>
        <View style={styles.card}>
          <TouchableOpacity 
            style={styles.legalItem}
            onPress={() => router.push('/privacy')}
            data-testid="privacy-policy-button"
          >
            <Icon name="shield-checkmark" size={22} color={COLORS.primary} />
            <Text style={styles.legalText}>{t('privacyPolicy')}</Text>
            <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.legalItem}
            onPress={() => router.push('/privacy')}
            data-testid="terms-of-service-button"
          >
            <Icon name="document-text" size={22} color={COLORS.accent} />
            <Text style={styles.legalText}>{t('termsOfService')}</Text>
            <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.legalItem}
            onPress={() => router.push('/privacy')}
            data-testid="gdpr-consent-button"
          >
            <Icon name="checkbox" size={22} color="#27AE60" />
            <Text style={styles.legalText}>{t('gdprConsents')}</Text>
            <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.legalItem, { borderBottomWidth: 0 }]}
            onPress={handleDeleteAccount}
            data-testid="delete-account-button"
          >
            <Icon name="trash" size={22} color="#E74C3C" />
            <Text style={[styles.legalText, { color: '#E74C3C' }]}>{t('deleteAccount')}</Text>
            <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>
        </View>

        {/* Logout Section */}
        <View style={styles.logoutSection}>
          <TouchableOpacity 
            style={styles.logoutButton}
            onPress={handleLogout}
            data-testid="logout-button"
          >
            <Icon name="log-out" size={22} color="#fff" />
            <Text style={styles.logoutText}>{t('logoutAccount')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.card,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  saveButton: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textLight,
    marginBottom: SPACING.sm,
    marginTop: SPACING.lg,
    marginLeft: SPACING.xs,
  },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.small,
  },
  fieldLabel: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginBottom: SPACING.xs,
  },
  input: {
    fontSize: 16,
    color: COLORS.text,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  selectRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectLabel: {
    fontSize: 16,
    color: COLORS.text,
  },
  selectValue: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  selectFlag: {
    fontSize: 20,
    marginRight: SPACING.xs,
  },
  selectText: {
    fontSize: 15,
    color: COLORS.textLight,
    marginRight: SPACING.xs,
  },
  optionsList: {
    marginTop: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.md,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
  },
  optionItemSelected: {
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.sm,
    marginHorizontal: -SPACING.sm,
  },
  optionFlag: {
    fontSize: 20,
    marginRight: SPACING.md,
  },
  optionText: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  switchContent: {
    flex: 1,
  },
  switchLabel: {
    fontSize: 16,
    color: COLORS.text,
  },
  switchDescription: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  infoText: {
    fontSize: 14,
    color: COLORS.textLight,
    marginBottom: SPACING.xs,
  },
  legalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  legalText: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
    marginLeft: SPACING.md,
  },
  logoutSection: {
    marginTop: SPACING.xl,
    marginBottom: SPACING.xl * 2,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.error,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    gap: SPACING.sm,
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  timeDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
  },
  timeText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  timePickerContainer: {
    marginTop: SPACING.md,
    paddingTop: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  timePickerRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: SPACING.lg,
  },
  timePickerColumn: {
    alignItems: 'center',
  },
  timePickerLabel: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginBottom: SPACING.sm,
  },
  timePickerButtons: {
    alignItems: 'center',
  },
  timeButton: {
    padding: SPACING.sm,
    backgroundColor: COLORS.primary + '15',
    borderRadius: BORDER_RADIUS.md,
  },
  timeValue: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.text,
    marginVertical: SPACING.sm,
  },
  timeSeparator: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 24,
  },
  testButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
  },
  testButtonText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '500',
  },
});
