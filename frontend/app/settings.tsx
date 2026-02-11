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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

const LANGUAGES = [
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
];

const BIBLE_EDITIONS = [
  { id: 'nuova_diodati', name: 'Nuova Diodati', language: 'it' },
  { id: 'reina_valera', name: 'Reina Valera 1960', language: 'es' },
];

export default function SettingsScreen() {
  const { user, setUser } = useAuthStore();
  const [name, setName] = useState(user?.name || '');
  const [language, setLanguage] = useState(user?.language || 'it');
  const [preferredBible, setPreferredBible] = useState(user?.preferred_bible || 'nuova_diodati');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [dailyVerseEnabled, setDailyVerseEnabled] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showLanguages, setShowLanguages] = useState(false);
  const [showBibles, setShowBibles] = useState(false);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const updatedUser = await api.updateSettings({
        name,
        language,
        preferred_bible: preferredBible,
      });
      setUser(updatedUser);
      Alert.alert('Salvato!', 'Le tue impostazioni sono state aggiornate.');
    } catch (error) {
      Alert.alert('Errore', 'Impossibile salvare le impostazioni');
    } finally {
      setSaving(false);
    }
  };

  const selectedLanguage = LANGUAGES.find(l => l.code === language);
  const selectedBible = BIBLE_EDITIONS.find(b => b.id === preferredBible);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Impostazioni</Text>
        <TouchableOpacity onPress={saveSettings} disabled={saving}>
          {saving ? (
            <ActivityIndicator size="small" color={COLORS.primary} />
          ) : (
            <Text style={styles.saveButton}>Salva</Text>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.sectionTitle}>Profilo</Text>
        <View style={styles.card}>
          <Text style={styles.fieldLabel}>Nome</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Il tuo nome"
            placeholderTextColor={COLORS.textMuted}
          />
        </View>

        <Text style={styles.sectionTitle}>Lingua</Text>
        <TouchableOpacity
          style={styles.card}
          onPress={() => setShowLanguages(!showLanguages)}
        >
          <View style={styles.selectRow}>
            <Text style={styles.selectLabel}>Lingua dell'app</Text>
            <View style={styles.selectValue}>
              <Text style={styles.selectFlag}>{selectedLanguage?.flag}</Text>
              <Text style={styles.selectText}>{selectedLanguage?.name}</Text>
              <Ionicons
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
                    setLanguage(lang.code);
                    setShowLanguages(false);
                  }}
                >
                  <Text style={styles.optionFlag}>{lang.flag}</Text>
                  <Text style={styles.optionText}>{lang.name}</Text>
                  {language === lang.code && (
                    <Ionicons name="checkmark" size={20} color={COLORS.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </TouchableOpacity>

        <Text style={styles.sectionTitle}>Bibbia</Text>
        <TouchableOpacity
          style={styles.card}
          onPress={() => setShowBibles(!showBibles)}
        >
          <View style={styles.selectRow}>
            <Text style={styles.selectLabel}>Edizione preferita</Text>
            <View style={styles.selectValue}>
              <Text style={styles.selectText}>{selectedBible?.name}</Text>
              <Ionicons
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
                    <Ionicons name="checkmark" size={20} color={COLORS.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          )}
        </TouchableOpacity>

        <Text style={styles.sectionTitle}>Notifiche</Text>
        <View style={styles.card}>
          <View style={styles.switchRow}>
            <View style={styles.switchContent}>
              <Text style={styles.switchLabel}>Notifiche Push</Text>
              <Text style={styles.switchDescription}>Ricevi notifiche dalla community</Text>
            </View>
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: COLORS.border, true: COLORS.primary }}
              thumbColor="#fff"
            />
          </View>

          <View style={[styles.switchRow, { borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: SPACING.md, paddingTop: SPACING.md }]}>
            <View style={styles.switchContent}>
              <Text style={styles.switchLabel}>Versetto del Giorno</Text>
              <Text style={styles.switchDescription}>Ricevi un versetto ogni mattina</Text>
            </View>
            <Switch
              value={dailyVerseEnabled}
              onValueChange={setDailyVerseEnabled}
              trackColor={{ false: COLORS.border, true: COLORS.primary }}
              thumbColor="#fff"
            />
          </View>
        </View>

        <Text style={styles.sectionTitle}>Informazioni</Text>
        <View style={styles.card}>
          <Text style={styles.infoText}>Email: {user?.email}</Text>
          <Text style={styles.infoText}>Versione app: 1.0.0</Text>
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
});
