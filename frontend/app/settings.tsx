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
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { useTranslation, useLanguageStore } from '../src/store/languageStore';
import { api } from '../src/utils/api';
import { NotificationService } from '../src/services/NotificationService';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';
import OfflineManager from '../src/components/OfflineManager';
import { showPrivacyOptionsForm } from '../src/utils/ads';

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
  const [quizEnabled, setQuizEnabled] = useState(false);
  const [quizHour, setQuizHour] = useState(12);
  const [quizMinute, setQuizMinute] = useState(0);
  const [readingEnabled, setReadingEnabled] = useState(false);
  const [readingHour, setReadingHour] = useState(20);
  const [readingMinute, setReadingMinute] = useState(0);
  const [activeTimePicker, setActiveTimePicker] = useState<'verse' | 'quiz' | 'reading' | null>(null);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showLanguages, setShowLanguages] = useState(false);
  const [showBibles, setShowBibles] = useState(false);

  // Parental Controls States
  const [showParentalControls, setShowParentalControls] = useState(false);
  const [showPinModal, setShowPinModal] = useState(false);
  const [parentalControlsStatus, setParentalControlsStatus] = useState<any>(null);
  const [parentPin, setParentPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [pinError, setPinError] = useState('');
  const [socialFeaturesEnabled, setSocialFeaturesEnabled] = useState(true);
  const [socialLevel, setSocialLevel] = useState('friends_only');
  const [mediaSharingEnabled, setMediaSharingEnabled] = useState(false);
  const [loadingParental, setLoadingParental] = useState(false);
  const [pinVerified, setPinVerified] = useState(false);

  // Load parental controls on mount
  useEffect(() => {
    loadParentalControlsStatus();
  }, []);

  const loadParentalControlsStatus = async () => {
    try {
      const status = await api.getParentalControlsStatus();
      setParentalControlsStatus(status);
      setSocialFeaturesEnabled(status.social_features_enabled ?? false);
      setSocialLevel(status.social_level || 'friends_only');
      setMediaSharingEnabled(status.media_sharing_enabled ?? false);
    } catch (error) {
      console.log('Error loading parental controls:', error);
    }
  };

  const handleSetPin = async () => {
    setPinError('');
    if (newPin.length < 4 || newPin.length > 6) {
      setPinError(t('pinMustBe4to6') || 'Il PIN deve essere di 4-6 cifre');
      return;
    }
    if (!/^\d+$/.test(newPin)) {
      setPinError(t('pinMustBeNumbers') || 'Il PIN deve contenere solo numeri');
      return;
    }
    if (newPin !== confirmPin) {
      setPinError(t('pinsDoNotMatch') || 'I PIN non corrispondono');
      return;
    }
    setLoadingParental(true);
    try {
      await api.setParentPin(newPin);
      setShowPinModal(false);
      setNewPin('');
      setConfirmPin('');
      setPinVerified(true);
      await loadParentalControlsStatus();
      showInfoAlert(
        t('success') || 'Successo',
        t('parentPinSet') || 'PIN controllo genitori impostato con successo',
        'OK'
      );
    } catch (error: any) {
      setPinError(error.message || 'Errore durante il salvataggio del PIN');
    } finally {
      setLoadingParental(false);
    }
  };

  const handleVerifyPin = async () => {
    setPinError('');
    setLoadingParental(true);
    try {
      await api.verifyParentPin(parentPin);
      setPinVerified(true);
      setShowPinModal(false);
      setParentPin('');
    } catch (error: any) {
      setPinError(error.message || 'PIN non valido');
    } finally {
      setLoadingParental(false);
    }
  };

  const handleUpdateParentalControls = async () => {
    if (!parentalControlsStatus?.parent_pin_set) {
      setShowPinModal(true);
      return;
    }
    if (!pinVerified) {
      setShowPinModal(true);
      return;
    }
    setLoadingParental(true);
    try {
      await api.updateParentalControls(parentPin || newPin, {
        social_features_enabled: socialFeaturesEnabled,
        social_level: socialLevel,
        media_sharing_enabled: mediaSharingEnabled,
      });
      await loadParentalControlsStatus();
      showInfoAlert(
        t('saved') || 'Salvato',
        t('parentalControlsUpdated') || 'Impostazioni controllo genitori aggiornate',
        'OK'
      );
    } catch (error: any) {
      showInfoAlert(
        t('error') || 'Errore',
        error.message || 'Errore durante l\'aggiornamento',
        'OK'
      );
    } finally {
      setLoadingParental(false);
    }
  };

  // Load notification settings on mount
  useEffect(() => {
    loadNotificationSettings();
  }, []);

  const loadNotificationSettings = async () => {
    const settings = await NotificationService.getSettings();
    setDailyVerseEnabled(settings.verse.enabled);
    setNotificationsEnabled(settings.verse.enabled || settings.quiz.enabled || settings.reading.enabled);
    setNotificationHour(settings.verse.hour);
    setNotificationMinute(settings.verse.minute);
    setQuizEnabled(settings.quiz.enabled);
    setQuizHour(settings.quiz.hour);
    setQuizMinute(settings.quiz.minute);
    setReadingEnabled(settings.reading.enabled);
    setReadingHour(settings.reading.hour);
    setReadingMinute(settings.reading.minute);
  };

  const handleDailyVerseToggle = async (value: boolean) => {
    setDailyVerseEnabled(value);
    if (value) {
      const success = await NotificationService.scheduleDailyVerseNotification(notificationHour, notificationMinute, currentLanguage);
      if (!success) {
        setDailyVerseEnabled(false);
        Alert.alert(t('error'), t('notificationPermissionDenied') || 'Permessi notifiche non concessi.');
      }
    } else {
      await NotificationService.cancelDailyVerseNotification();
    }
  };

  const handleQuizToggle = async (value: boolean) => {
    setQuizEnabled(value);
    if (value) {
      const success = await NotificationService.scheduleQuizNotification(quizHour, quizMinute, currentLanguage);
      if (!success) {
        setQuizEnabled(false);
        Alert.alert(t('error'), t('notificationPermissionDenied') || 'Permessi notifiche non concessi.');
      }
    } else {
      await NotificationService.cancelQuizNotification();
    }
  };

  const handleReadingToggle = async (value: boolean) => {
    setReadingEnabled(value);
    if (value) {
      const success = await NotificationService.scheduleReadingNotification(readingHour, readingMinute, currentLanguage);
      if (!success) {
        setReadingEnabled(false);
        Alert.alert(t('error'), t('notificationPermissionDenied') || 'Permessi notifiche non concessi.');
      }
    } else {
      await NotificationService.cancelReadingNotification();
    }
  };

  const handleTimeChange = async (hour: number, minute: number) => {
    if (activeTimePicker === 'verse') {
      setNotificationHour(hour);
      setNotificationMinute(minute);
      if (dailyVerseEnabled) await NotificationService.scheduleDailyVerseNotification(hour, minute, currentLanguage);
    } else if (activeTimePicker === 'quiz') {
      setQuizHour(hour);
      setQuizMinute(minute);
      if (quizEnabled) await NotificationService.scheduleQuizNotification(hour, minute, currentLanguage);
    } else if (activeTimePicker === 'reading') {
      setReadingHour(hour);
      setReadingMinute(minute);
      if (readingEnabled) await NotificationService.scheduleReadingNotification(hour, minute, currentLanguage);
    }
    setActiveTimePicker(null);
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

  const renderTimePicker = (hour: number, minute: number) => (
    <View style={styles.timePickerContainer}>
      <View style={styles.timePickerRow}>
        <View style={styles.timePickerColumn}>
          <Text style={styles.timePickerLabel}>{t('hour') || 'Ora'}</Text>
          <View style={styles.timePickerButtons}>
            <TouchableOpacity style={styles.timeButton} onPress={() => handleTimeChange((hour + 1) % 24, minute)}>
              <Icon name="chevron-up" size={20} color={COLORS.primary} />
            </TouchableOpacity>
            <Text style={styles.timeValue}>{hour.toString().padStart(2, '0')}</Text>
            <TouchableOpacity style={styles.timeButton} onPress={() => handleTimeChange((hour + 23) % 24, minute)}>
              <Icon name="chevron-down" size={20} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        </View>
        <Text style={styles.timeSeparator}>:</Text>
        <View style={styles.timePickerColumn}>
          <Text style={styles.timePickerLabel}>{t('minute') || 'Min'}</Text>
          <View style={styles.timePickerButtons}>
            <TouchableOpacity style={styles.timeButton} onPress={() => handleTimeChange(hour, (minute + 15) % 60)}>
              <Icon name="chevron-up" size={20} color={COLORS.primary} />
            </TouchableOpacity>
            <Text style={styles.timeValue}>{minute.toString().padStart(2, '0')}</Text>
            <TouchableOpacity style={styles.timeButton} onPress={() => handleTimeChange(hour, (minute + 45) % 60)}>
              <Icon name="chevron-down" size={20} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </View>
  );


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

      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={true}
      >
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
          {/* Daily Verse Notification */}
          <View style={styles.switchRow}>
            <View style={styles.switchContent}>
              <Text style={styles.switchLabel}>{t('dailyVerseNotification')}</Text>
              <Text style={styles.switchDescription}>{t('receiveVerse') || 'Ricevi un versetto ogni mattina'}</Text>
            </View>
            <Switch
              value={dailyVerseEnabled}
              onValueChange={handleDailyVerseToggle}
              trackColor={{ false: COLORS.border, true: COLORS.primary }}
              thumbColor="#fff"
            />
          </View>
          {dailyVerseEnabled && (
            <TouchableOpacity 
              style={styles.timeRow}
              onPress={() => setActiveTimePicker(activeTimePicker === 'verse' ? null : 'verse')}
            >
              <Icon name="time-outline" size={18} color={COLORS.textMuted} />
              <Text style={styles.timeRowLabel}>{t('notificationTime') || 'Orario'}</Text>
              <Text style={styles.timeRowValue}>
                {notificationHour.toString().padStart(2, '0')}:{notificationMinute.toString().padStart(2, '0')}
              </Text>
              <Icon name={activeTimePicker === 'verse' ? 'chevron-up' : 'chevron-down'} size={16} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}
          {activeTimePicker === 'verse' && renderTimePicker(notificationHour, notificationMinute)}

          {/* Quiz Reminder */}
          <View style={[styles.switchRow, { borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: SPACING.sm, paddingTop: SPACING.sm }]}>
            <View style={styles.switchContent}>
              <Text style={styles.switchLabel}>{t('quizNotification') || 'Promemoria Quiz'}</Text>
              <Text style={styles.switchDescription}>{t('quizNotificationDesc') || 'Ricorda di fare un quiz biblico'}</Text>
            </View>
            <Switch
              value={quizEnabled}
              onValueChange={handleQuizToggle}
              trackColor={{ false: COLORS.border, true: COLORS.primary }}
              thumbColor="#fff"
            />
          </View>
          {quizEnabled && (
            <TouchableOpacity 
              style={styles.timeRow}
              onPress={() => setActiveTimePicker(activeTimePicker === 'quiz' ? null : 'quiz')}
            >
              <Icon name="time-outline" size={18} color={COLORS.textMuted} />
              <Text style={styles.timeRowLabel}>{t('notificationTime') || 'Orario'}</Text>
              <Text style={styles.timeRowValue}>
                {quizHour.toString().padStart(2, '0')}:{quizMinute.toString().padStart(2, '0')}
              </Text>
              <Icon name={activeTimePicker === 'quiz' ? 'chevron-up' : 'chevron-down'} size={16} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}
          {activeTimePicker === 'quiz' && renderTimePicker(quizHour, quizMinute)}

          {/* Reading Reminder */}
          <View style={[styles.switchRow, { borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: SPACING.sm, paddingTop: SPACING.sm }]}>
            <View style={styles.switchContent}>
              <Text style={styles.switchLabel}>{t('readingNotification') || 'Promemoria Lettura'}</Text>
              <Text style={styles.switchDescription}>{t('readingNotificationDesc') || 'Ricorda di leggere la Bibbia'}</Text>
            </View>
            <Switch
              value={readingEnabled}
              onValueChange={handleReadingToggle}
              trackColor={{ false: COLORS.border, true: COLORS.primary }}
              thumbColor="#fff"
            />
          </View>
          {readingEnabled && (
            <TouchableOpacity 
              style={styles.timeRow}
              onPress={() => setActiveTimePicker(activeTimePicker === 'reading' ? null : 'reading')}
            >
              <Icon name="time-outline" size={18} color={COLORS.textMuted} />
              <Text style={styles.timeRowLabel}>{t('notificationTime') || 'Orario'}</Text>
              <Text style={styles.timeRowValue}>
                {readingHour.toString().padStart(2, '0')}:{readingMinute.toString().padStart(2, '0')}
              </Text>
              <Icon name={activeTimePicker === 'reading' ? 'chevron-up' : 'chevron-down'} size={16} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}
          {activeTimePicker === 'reading' && renderTimePicker(readingHour, readingMinute)}

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

        {/* Offline Mode Section */}
        <Text style={styles.sectionTitle}>{t('offlineMode') || 'Modalità Offline'}</Text>
        <View style={styles.card}>
          <OfflineManager />
        </View>

        {/* Parental Controls Section */}
        <Text style={styles.sectionTitle}>{t('parentalControls') || 'Controllo Genitori'}</Text>
        <View style={styles.card}>
          <View style={styles.parentalHeader}>
            <Icon name="shield-checkmark" size={24} color={COLORS.primary} />
            <View style={styles.parentalHeaderText}>
              <Text style={styles.parentalTitle}>{t('parentalControlsTitle') || 'Gestione Funzionalità Social'}</Text>
              <Text style={styles.parentalSubtitle}>
                {parentalControlsStatus?.is_minor 
                  ? (t('minorAccount') || 'Account minorenne - Protetto')
                  : (t('adultAccount') || 'Account adulto')}
              </Text>
            </View>
          </View>

          {parentalControlsStatus?.is_minor && (
            <>
              {/* PIN Setup / Verify Button */}
              {!parentalControlsStatus?.parent_pin_set ? (
                <TouchableOpacity 
                  style={styles.setupPinButton}
                  onPress={() => setShowPinModal(true)}
                  data-testid="setup-parent-pin-btn"
                >
                  <Icon name="key" size={20} color="#fff" />
                  <Text style={styles.setupPinButtonText}>
                    {t('setupParentPin') || 'Imposta PIN Genitore'}
                  </Text>
                </TouchableOpacity>
              ) : (
                <>
                  {!pinVerified && (
                    <TouchableOpacity 
                      style={styles.verifyPinButton}
                      onPress={() => setShowPinModal(true)}
                      data-testid="verify-parent-pin-btn"
                    >
                      <Icon name="lock-open" size={20} color={COLORS.primary} />
                      <Text style={styles.verifyPinButtonText}>
                        {t('unlockToModify') || 'Sblocca per modificare'}
                      </Text>
                    </TouchableOpacity>
                  )}

                  {pinVerified && (
                    <View style={styles.parentalControlsContent}>
                      {/* Social Features Toggle */}
                      <View style={styles.parentalOption}>
                        <View style={styles.parentalOptionInfo}>
                          <Text style={styles.parentalOptionLabel}>
                            {t('socialFeatures') || 'Funzionalità Social'}
                          </Text>
                          <Text style={styles.parentalOptionDesc}>
                            {t('socialFeaturesDesc') || 'Abilita/disabilita community e chat'}
                          </Text>
                        </View>
                        <Switch
                          value={socialFeaturesEnabled}
                          onValueChange={setSocialFeaturesEnabled}
                          trackColor={{ false: COLORS.border, true: COLORS.primary }}
                          thumbColor="#fff"
                        />
                      </View>

                      {/* Social Level Selection */}
                      {socialFeaturesEnabled && (
                        <View style={styles.socialLevelSection}>
                          <Text style={styles.socialLevelTitle}>
                            {t('socialLevel') || 'Livello Interazione'}
                          </Text>
                          <View style={styles.socialLevelOptions}>
                            <TouchableOpacity
                              style={[
                                styles.socialLevelOption,
                                socialLevel === 'friends_only' && styles.socialLevelOptionSelected
                              ]}
                              onPress={() => setSocialLevel('friends_only')}
                            >
                              <Icon name="people" size={20} color={socialLevel === 'friends_only' ? '#fff' : COLORS.text} />
                              <Text style={[
                                styles.socialLevelOptionText,
                                socialLevel === 'friends_only' && styles.socialLevelOptionTextSelected
                              ]}>
                                {t('friendsOnly') || 'Solo Amici'}
                              </Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                              style={[
                                styles.socialLevelOption,
                                socialLevel === 'disabled' && styles.socialLevelOptionSelected
                              ]}
                              onPress={() => setSocialLevel('disabled')}
                            >
                              <Icon name="close-circle" size={20} color={socialLevel === 'disabled' ? '#fff' : COLORS.text} />
                              <Text style={[
                                styles.socialLevelOptionText,
                                socialLevel === 'disabled' && styles.socialLevelOptionTextSelected
                              ]}>
                                {t('disabled') || 'Disabilitato'}
                              </Text>
                            </TouchableOpacity>
                          </View>
                        </View>
                      )}

                      {/* Media Sharing Toggle */}
                      <View style={styles.parentalOption}>
                        <View style={styles.parentalOptionInfo}>
                          <Text style={styles.parentalOptionLabel}>
                            {t('mediaSharing') || 'Condivisione Media'}
                          </Text>
                          <Text style={styles.parentalOptionDesc}>
                            {t('mediaSharingDesc') || 'Permetti invio/ricezione di immagini'}
                          </Text>
                        </View>
                        <Switch
                          value={mediaSharingEnabled}
                          onValueChange={setMediaSharingEnabled}
                          trackColor={{ false: COLORS.border, true: COLORS.primary }}
                          thumbColor="#fff"
                        />
                      </View>

                      {/* Save Button */}
                      <TouchableOpacity
                        style={styles.saveParentalButton}
                        onPress={handleUpdateParentalControls}
                        disabled={loadingParental}
                        data-testid="save-parental-controls-btn"
                      >
                        {loadingParental ? (
                          <ActivityIndicator size="small" color="#fff" />
                        ) : (
                          <>
                            <Icon name="save" size={20} color="#fff" />
                            <Text style={styles.saveParentalButtonText}>
                              {t('saveSettings') || 'Salva Impostazioni'}
                            </Text>
                          </>
                        )}
                      </TouchableOpacity>
                    </View>
                  )}
                </>
              )}
            </>
          )}

          {!parentalControlsStatus?.is_minor && (
            <Text style={styles.adultMessage}>
              {t('adultNoRestrictions') || 'Le restrizioni del controllo genitori non si applicano agli utenti adulti.'}
            </Text>
          )}
        </View>

        {/* PIN Modal */}
        <Modal
          visible={showPinModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowPinModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.pinModal}>
              <View style={styles.pinModalHeader}>
                <Icon name="shield-checkmark" size={32} color={COLORS.primary} />
                <Text style={styles.pinModalTitle}>
                  {parentalControlsStatus?.parent_pin_set 
                    ? (t('enterParentPin') || 'Inserisci PIN Genitore')
                    : (t('createParentPin') || 'Crea PIN Genitore')}
                </Text>
                <Text style={styles.pinModalSubtitle}>
                  {parentalControlsStatus?.parent_pin_set 
                    ? (t('enterPinToModify') || 'Inserisci il PIN per modificare le impostazioni')
                    : (t('createPinDesc') || 'Crea un PIN di 4-6 cifre per proteggere le impostazioni')}
                </Text>
              </View>

              {parentalControlsStatus?.parent_pin_set ? (
                <View style={styles.pinInputContainer}>
                  <TextInput
                    style={styles.pinInput}
                    value={parentPin}
                    onChangeText={setParentPin}
                    placeholder="****"
                    placeholderTextColor={COLORS.textMuted}
                    keyboardType="numeric"
                    secureTextEntry
                    maxLength={6}
                    autoFocus
                  />
                </View>
              ) : (
                <>
                  <View style={styles.pinInputContainer}>
                    <Text style={styles.pinInputLabel}>{t('newPin') || 'Nuovo PIN'}</Text>
                    <TextInput
                      style={styles.pinInput}
                      value={newPin}
                      onChangeText={setNewPin}
                      placeholder="****"
                      placeholderTextColor={COLORS.textMuted}
                      keyboardType="numeric"
                      secureTextEntry
                      maxLength={6}
                      autoFocus
                    />
                  </View>
                  <View style={styles.pinInputContainer}>
                    <Text style={styles.pinInputLabel}>{t('confirmPin') || 'Conferma PIN'}</Text>
                    <TextInput
                      style={styles.pinInput}
                      value={confirmPin}
                      onChangeText={setConfirmPin}
                      placeholder="****"
                      placeholderTextColor={COLORS.textMuted}
                      keyboardType="numeric"
                      secureTextEntry
                      maxLength={6}
                    />
                  </View>
                </>
              )}

              {pinError ? (
                <Text style={styles.pinError}>{pinError}</Text>
              ) : null}

              <View style={styles.pinModalButtons}>
                <TouchableOpacity
                  style={styles.pinCancelButton}
                  onPress={() => {
                    setShowPinModal(false);
                    setParentPin('');
                    setNewPin('');
                    setConfirmPin('');
                    setPinError('');
                  }}
                >
                  <Text style={styles.pinCancelButtonText}>{t('cancel') || 'Annulla'}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.pinConfirmButton}
                  onPress={parentalControlsStatus?.parent_pin_set ? handleVerifyPin : handleSetPin}
                  disabled={loadingParental}
                >
                  {loadingParental ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <Text style={styles.pinConfirmButtonText}>
                      {parentalControlsStatus?.parent_pin_set 
                        ? (t('verify') || 'Verifica')
                        : (t('create') || 'Crea')}
                    </Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

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

          {Platform.OS !== 'web' && (
            <TouchableOpacity 
              style={styles.legalItem}
              onPress={() => showPrivacyOptionsForm()}
              data-testid="ads-privacy-options-button"
            >
              <Icon name="megaphone" size={22} color="#F39C12" />
              <Text style={styles.legalText}>{t('adsPrivacyOptions') || 'Preferenze annunci'}</Text>
              <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}

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
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
    gap: SPACING.sm,
  },
  timeRowLabel: {
    flex: 1,
    fontSize: 14,
    color: COLORS.textLight,
  },
  timeRowValue: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
    marginRight: 4,
  },
  // Parental Controls Styles
  parentalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
    gap: SPACING.md,
  },
  parentalHeaderText: {
    flex: 1,
  },
  parentalTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  parentalSubtitle: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  setupPinButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
  },
  setupPinButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  verifyPinButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary + '15',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  verifyPinButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  parentalControlsContent: {
    marginTop: SPACING.md,
  },
  parentalOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  parentalOptionInfo: {
    flex: 1,
    marginRight: SPACING.md,
  },
  parentalOptionLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
  },
  parentalOptionDesc: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  socialLevelSection: {
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  socialLevelTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  socialLevelOptions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  socialLevelOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.border,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.xs,
  },
  socialLevelOptionSelected: {
    backgroundColor: COLORS.primary,
  },
  socialLevelOptionText: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.text,
  },
  socialLevelOptionTextSelected: {
    color: '#fff',
  },
  saveParentalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.lg,
    gap: SPACING.sm,
  },
  saveParentalButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  adultMessage: {
    fontSize: 14,
    color: COLORS.textMuted,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.lg,
  },
  pinModal: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.xl,
    width: '100%',
    maxWidth: 400,
  },
  pinModalHeader: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  pinModalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.md,
    textAlign: 'center',
  },
  pinModalSubtitle: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
  pinInputContainer: {
    marginBottom: SPACING.md,
  },
  pinInputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  pinInput: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 24,
    textAlign: 'center',
    letterSpacing: 8,
    color: COLORS.text,
  },
  pinError: {
    color: '#E74C3C',
    fontSize: 13,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  pinModalButtons: {
    flexDirection: 'row',
    gap: SPACING.md,
    marginTop: SPACING.md,
  },
  pinCancelButton: {
    flex: 1,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.border,
    alignItems: 'center',
  },
  pinCancelButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.text,
  },
  pinConfirmButton: {
    flex: 1,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
  },
  pinConfirmButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
