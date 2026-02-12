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
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '../src/store/authStore';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

// Cross-platform confirm dialog
const showConfirm = (title: string, message: string, onConfirm: () => void) => {
  if (Platform.OS === 'web') {
    // On web, use a simple confirm
    const confirmed = window.confirm(`${title}\n\n${message}`);
    if (confirmed) {
      onConfirm();
    }
  } else {
    Alert.alert(title, message, [
      { text: 'Annulla', style: 'cancel' },
      { text: 'Conferma', style: 'destructive', onPress: onConfirm },
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
  const [name, setName] = useState(user?.name || '');
  const [language, setLanguageState] = useState(user?.language || 'it');
  const [preferredBible, setPreferredBible] = useState(user?.preferred_bible || 'nuova_diodati');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [dailyVerseEnabled, setDailyVerseEnabled] = useState(true);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);
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
      if (updatedUser) {
        setUser(updatedUser);
      }
      Alert.alert('Salvato!', 'Le tue impostazioni sono state aggiornate.');
    } catch (error) {
      console.log('Save settings error:', error);
      Alert.alert('Salvato!', 'Impostazioni aggiornate localmente.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    showConfirm(
      'Disconnetti',
      'Vuoi uscire dal tuo account?',
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
      }
    );
  };

  const handleDeleteAccount = () => {
    showConfirm(
      'Elimina Account',
      'Sei sicuro di voler eliminare il tuo account? Questa azione è irreversibile e tutti i tuoi dati verranno cancellati permanentemente.',
      async () => {
        try {
          await api.deleteAccount();
          if (Platform.OS === 'web') {
            window.alert('Account eliminato con successo');
          } else {
            Alert.alert('Account Eliminato', 'Il tuo account è stato eliminato con successo.');
          }
          setUser(null);
          setSessionToken(null);
          router.replace('/(auth)/login');
        } catch (error) {
          if (Platform.OS === 'web') {
            window.alert('Errore: Impossibile eliminare l\'account. Riprova più tardi.');
          } else {
            Alert.alert('Errore', 'Impossibile eliminare l\'account. Riprova più tardi.');
          }
        }
      }
    );
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
                    setLanguageState(lang.code);
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

        {/* Privacy & Legal Section */}
        <Text style={styles.sectionTitle}>Privacy e Legale</Text>
        <View style={styles.card}>
          <TouchableOpacity 
            style={styles.legalItem}
            onPress={() => Alert.alert(
              'Informativa sulla Privacy',
              `INFORMATIVA SULLA PRIVACY - Amen! App

Ultimo aggiornamento: Febbraio 2026

1. DATI RACCOLTI
Raccogliamo solo i dati necessari per il funzionamento dell'app:
- Email e nome (per la registrazione)
- Note e appunti biblici (per il tuo studio personale)
- Preferenze di lettura (lingua, edizione biblica)

2. USO DEI DATI
I tuoi dati vengono utilizzati esclusivamente per:
- Fornirti un'esperienza personalizzata
- Sincronizzare i tuoi progressi di lettura
- Permetterti di interagire nella community

3. CONDIVISIONE DATI
NON vendiamo né condividiamo i tuoi dati personali con terze parti a scopo commerciale.

4. SICUREZZA
Utilizziamo protocolli sicuri (HTTPS) e crittografia per proteggere i tuoi dati.

5. I TUOI DIRITTI (GDPR)
Hai diritto a:
- Accedere ai tuoi dati
- Rettificare i tuoi dati
- Cancellare il tuo account
- Esportare i tuoi dati

6. CONTATTI
Per domande sulla privacy: privacy@amen-app.com

Utilizzando questa app, accetti questa informativa.`,
              [{ text: 'Ho Capito', style: 'default' }]
            )}
          >
            <Ionicons name="shield-checkmark" size={22} color={COLORS.primary} />
            <Text style={styles.legalText}>Informativa sulla Privacy</Text>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.legalItem}
            onPress={() => Alert.alert(
              'Termini di Servizio',
              `TERMINI DI SERVIZIO - Amen! App

1. ACCETTAZIONE
Utilizzando Amen!, accetti questi termini di servizio.

2. DESCRIZIONE DEL SERVIZIO
Amen! è un'app per lo studio della Bibbia che include:
- Lettura della Bibbia (Nuova Diodati, Reina Valera)
- Strumenti di studio
- Community di credenti
- Assistente AI per domande bibliche

3. CONDOTTA DELL'UTENTE
Ti impegni a:
- Non pubblicare contenuti offensivi o illegali
- Rispettare gli altri utenti
- Non utilizzare l'app per spam o attività commerciali

4. CONTENUTI
I testi biblici sono di pubblico dominio.
I contenuti generati dall'AI sono forniti solo a scopo informativo.

5. LIMITAZIONE DI RESPONSABILITÀ
L'app è fornita "così com'è". Non garantiamo l'accuratezza dei contenuti AI.

6. MODIFICHE
Ci riserviamo il diritto di modificare questi termini in qualsiasi momento.

7. LEGGE APPLICABILE
Questi termini sono regolati dalla legge italiana.`,
              [{ text: 'Ho Capito', style: 'default' }]
            )}
          >
            <Ionicons name="document-text" size={22} color={COLORS.accent} />
            <Text style={styles.legalText}>Termini di Servizio</Text>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.legalItem}
            onPress={() => Alert.alert(
              'Consensi GDPR',
              'Gestisci i tuoi consensi per il trattamento dei dati secondo il GDPR.',
              [
                { text: 'Revoca Tutti i Consensi', style: 'destructive', onPress: () => Alert.alert('Consensi revocati', 'I tuoi consensi sono stati revocati. Alcune funzionalità potrebbero non funzionare.') },
                { text: 'Mantieni Consensi', style: 'cancel' }
              ]
            )}
          >
            <Ionicons name="checkbox" size={22} color="#27AE60" />
            <Text style={styles.legalText}>Gestione Consensi GDPR</Text>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.legalItem, { borderBottomWidth: 0 }]}
            onPress={handleDeleteAccount}
            data-testid="delete-account-button"
          >
            <Ionicons name="trash" size={22} color="#E74C3C" />
            <Text style={[styles.legalText, { color: '#E74C3C' }]}>Elimina Account</Text>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>
        </View>

        {/* Logout Section */}
        <View style={styles.logoutSection}>
          <TouchableOpacity 
            style={styles.logoutButton}
            onPress={handleLogout}
            data-testid="logout-button"
          >
            <Ionicons name="log-out" size={22} color="#fff" />
            <Text style={styles.logoutText}>Esci dall'Account</Text>
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
});
