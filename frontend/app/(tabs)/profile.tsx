import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../../src/components/Icon';
import { HamburgerMenu } from '../../src/components/HamburgerMenu';
import { router } from 'expo-router';
import { useAuthStore } from '../../src/store/authStore';
import { useLanguageStore } from '../../src/store/languageStore';
import { api } from '../../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';

// Translations for profile page
const translations: Record<string, Record<string, string>> = {
  it: {
    profile: 'Profilo',
    progress: 'Il Tuo Progresso',
    streak: 'Serie',
    chapters: 'Capitoli',
    entries: 'Voci',
    readingHistory: 'Cronologia Lettura',
    noHistory: 'Nessun capitolo letto. Inizia a leggere la Bibbia!',
    readCount: 'Letto',
    times: 'volte',
    appFeatures: 'Funzionalità App',
    myContentSection: 'I Miei Contenuti',
    myContentDesc: 'Segnalibri, note ed evidenziazioni',
    quizSection: 'Sezione Quiz',
    quizDesc: 'Metti alla prova le tue conoscenze',
    dictionarySection: 'Dizionario Biblico',
    dictionaryDesc: 'Esplora i termini biblici',
    journalSection: 'Diario Spirituale',
    journalDesc: 'Registra il tuo cammino',
    groupsSection: 'Gruppi',
    groupsDesc: 'Comunità di studio',
    account: 'Account',
    privacy: 'Privacy e Termini',
    privacyDesc: 'GDPR, T&C, consensi',
    logout: 'Disconnetti',
    logoutTitle: 'Disconnetti',
    logoutMsg: 'Vuoi uscire dal tuo account?',
    deleteAccount: 'Elimina Account',
    deleteTitle: 'Elimina Account',
    deleteMsg: 'Questa azione è irreversibile. Tutti i tuoi dati saranno eliminati.',
    cancel: 'Annulla',
    confirm: 'Conferma',
    version: 'Versione',
    friendsSection: 'I Miei Amici',
    friendsDesc: 'Utenti preferiti',
  },
  en: {
    profile: 'Profile',
    progress: 'Your Progress',
    streak: 'Streak',
    chapters: 'Chapters',
    entries: 'Entries',
    readingHistory: 'Reading History',
    noHistory: 'No chapters read. Start reading the Bible!',
    readCount: 'Read',
    times: 'times',
    appFeatures: 'App Features',
    myContentSection: 'My Content',
    myContentDesc: 'Bookmarks, notes and highlights',
    quizSection: 'Quiz Section',
    quizDesc: 'Test your knowledge',
    dictionarySection: 'Bible Dictionary',
    dictionaryDesc: 'Explore biblical terms',
    journalSection: 'Spiritual Journal',
    journalDesc: 'Record your journey',
    groupsSection: 'Groups',
    groupsDesc: 'Study community',
    account: 'Account',
    privacy: 'Privacy & Terms',
    privacyDesc: 'GDPR, T&C, consents',
    logout: 'Log Out',
    logoutTitle: 'Log Out',
    logoutMsg: 'Do you want to log out?',
    deleteAccount: 'Delete Account',
    deleteTitle: 'Delete Account',
    deleteMsg: 'This action is irreversible. All your data will be deleted.',
    cancel: 'Cancel',
    confirm: 'Confirm',
    version: 'Version',
    friendsSection: 'My Friends',
    friendsDesc: 'Favorite users',
  },
  es: {
    progress: 'Tu Progreso',
    streak: 'Racha',
    chapters: 'Capítulos',
    entries: 'Entradas',
    readingHistory: 'Historial de Lectura',
    noHistory: 'Sin capítulos leídos. ¡Empieza a leer la Biblia!',
    readCount: 'Leído',
    times: 'veces',
    appFeatures: 'Funciones de la App',
    myContentSection: 'Mi Contenido',
    myContentDesc: 'Marcadores, notas y resaltados',
    quizSection: 'Sección Quiz',
    quizDesc: 'Pon a prueba tus conocimientos',
    dictionarySection: 'Diccionario Bíblico',
    dictionaryDesc: 'Explora términos bíblicos',
    journalSection: 'Diario Espiritual',
    journalDesc: 'Registra tu camino',
    groupsSection: 'Grupos',
    groupsDesc: 'Comunidad de estudio',
    account: 'Cuenta',
    privacy: 'Privacidad y Términos',
    privacyDesc: 'RGPD, T&C, consentimientos',
    logout: 'Cerrar Sesión',
    logoutTitle: 'Cerrar Sesión',
    logoutMsg: '¿Quieres cerrar sesión?',
    deleteAccount: 'Eliminar Cuenta',
    deleteTitle: 'Eliminar Cuenta',
    deleteMsg: 'Esta acción es irreversible. Todos tus datos serán eliminados.',
    cancel: 'Cancelar',
    confirm: 'Confirmar',
    version: 'Versión',
  },
  de: {
    progress: 'Dein Fortschritt',
    streak: 'Serie',
    chapters: 'Kapitel',
    entries: 'Einträge',
    readingHistory: 'Leseverlauf',
    noHistory: 'Keine Kapitel gelesen. Beginne mit dem Bibellesen!',
    readCount: 'Gelesen',
    times: 'mal',
    appFeatures: 'App-Funktionen',
    myContentSection: 'Meine Inhalte',
    myContentDesc: 'Lesezeichen, Notizen und Markierungen',
    quizSection: 'Quiz-Bereich',
    quizDesc: 'Teste dein Wissen',
    dictionarySection: 'Bibel-Wörterbuch',
    dictionaryDesc: 'Erkunde biblische Begriffe',
    journalSection: 'Spirituelles Tagebuch',
    journalDesc: 'Dokumentiere deinen Weg',
    groupsSection: 'Gruppen',
    groupsDesc: 'Studiengemeinschaft',
    account: 'Konto',
    privacy: 'Datenschutz & AGB',
    privacyDesc: 'DSGVO, AGB, Einwilligungen',
    logout: 'Abmelden',
    logoutTitle: 'Abmelden',
    logoutMsg: 'Möchtest du dich abmelden?',
    deleteAccount: 'Konto löschen',
    deleteTitle: 'Konto löschen',
    deleteMsg: 'Diese Aktion ist irreversibel. Alle deine Daten werden gelöscht.',
    cancel: 'Abbrechen',
    confirm: 'Bestätigen',
    version: 'Version',
  },
  fr: {
    progress: 'Votre Progression',
    streak: 'Série',
    chapters: 'Chapitres',
    entries: 'Entrées',
    readingHistory: 'Historique de Lecture',
    noHistory: 'Aucun chapitre lu. Commencez à lire la Bible!',
    readCount: 'Lu',
    times: 'fois',
    appFeatures: 'Fonctionnalités',
    myContentSection: 'Mon Contenu',
    myContentDesc: 'Signets, notes et surlignages',
    quizSection: 'Section Quiz',
    quizDesc: 'Testez vos connaissances',
    dictionarySection: 'Dictionnaire Biblique',
    dictionaryDesc: 'Explorez les termes bibliques',
    journalSection: 'Journal Spirituel',
    journalDesc: 'Enregistrez votre parcours',
    groupsSection: 'Groupes',
    groupsDesc: 'Communauté d\'étude',
    account: 'Compte',
    privacy: 'Confidentialité et Conditions',
    privacyDesc: 'RGPD, CGU, consentements',
    logout: 'Déconnexion',
    logoutTitle: 'Déconnexion',
    logoutMsg: 'Voulez-vous vous déconnecter?',
    deleteAccount: 'Supprimer le Compte',
    deleteTitle: 'Supprimer le Compte',
    deleteMsg: 'Cette action est irréversible. Toutes vos données seront supprimées.',
    cancel: 'Annuler',
    confirm: 'Confirmer',
    version: 'Version',
  },
  pt: {
    progress: 'Seu Progresso',
    streak: 'Sequência',
    chapters: 'Capítulos',
    entries: 'Entradas',
    readingHistory: 'Histórico de Leitura',
    noHistory: 'Nenhum capítulo lido. Comece a ler a Bíblia!',
    readCount: 'Lido',
    times: 'vezes',
    appFeatures: 'Recursos do App',
    myContentSection: 'Meu Conteúdo',
    myContentDesc: 'Marcadores, notas e destaques',
    quizSection: 'Seção Quiz',
    quizDesc: 'Teste seus conhecimentos',
    dictionarySection: 'Dicionário Bíblico',
    dictionaryDesc: 'Explore termos bíblicos',
    journalSection: 'Diário Espiritual',
    journalDesc: 'Registre sua jornada',
    groupsSection: 'Grupos',
    groupsDesc: 'Comunidade de estudo',
    account: 'Conta',
    privacy: 'Privacidade e Termos',
    privacyDesc: 'LGPD, T&C, consentimentos',
    logout: 'Sair',
    logoutTitle: 'Sair',
    logoutMsg: 'Deseja sair da sua conta?',
    deleteAccount: 'Excluir Conta',
    deleteTitle: 'Excluir Conta',
    deleteMsg: 'Esta ação é irreversível. Todos os seus dados serão excluídos.',
    cancel: 'Cancelar',
    confirm: 'Confirmar',
    version: 'Versão',
  },
};

// Cross-platform confirm dialog
const showConfirm = (title: string, message: string, onConfirm: () => void, cancelText: string = 'Annulla', confirmText: string = 'Conferma') => {
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

export default function ProfileScreen() {
  const { user, logout, setUser, setSessionToken } = useAuthStore();
  const { currentLanguage } = useLanguageStore();
  const [progress, setProgress] = useState<any>(null);
  const [readingHistory, setReadingHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [progressData, historyData] = await Promise.all([
        api.getProgress(),
        api.getReadingHistory(20)
      ]);
      setProgress(progressData);
      setReadingHistory(historyData?.history || []);
    } catch (error) {
      console.log('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const goToChapter = (book: string, chapter: number) => {
    router.push(`/bible?book=${encodeURIComponent(book)}&chapter=${chapter}`);
  };

  const handleLogout = () => {
    showConfirm(
      t('logoutTitle'),
      t('logoutMsg'),
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
      t('deleteTitle'),
      t('deleteMsg'),
      async () => {
        try {
          await api.deleteAccount();
          setUser(null);
          setSessionToken(null);
          router.replace('/(auth)/login');
        } catch (error) {
          console.error('Delete account error:', error);
        }
      },
      t('cancel'),
      t('confirm')
    );
  };

  const MenuItem = ({ icon, title, subtitle, onPress, color = COLORS.text }: any) => (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <View style={[styles.menuIcon, { backgroundColor: color + '15' }]}>
        <Icon name={icon} size={22} color={color} />
      </View>
      <View style={styles.menuContent}>
        <Text style={styles.menuTitle}>{title}</Text>
        {subtitle && <Text style={styles.menuSubtitle}>{subtitle}</Text>}
      </View>
      <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Navigation Header */}
      <View style={styles.topHeader}>
        <Text style={styles.topHeaderTitle}>{t('profile')}</Text>
        <HamburgerMenu currentScreen="profile" />
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </Text>
          </View>
          <Text style={styles.userName}>{user?.name}</Text>
          <Text style={styles.userEmail}>{user?.email}</Text>
        </View>

        {/* Stats */}
        {progress && (
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{progress.reading_streak || 0}</Text>
              <Text style={styles.statLabel}>{t('streak')}</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{progress.total_chapters_read || 0}</Text>
              <Text style={styles.statLabel}>{t('chapters')}</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{progress.total_journal_entries || 0}</Text>
              <Text style={styles.statLabel}>{t('entries')}</Text>
            </View>
          </View>
        )}

        {/* Reading History Section */}
        <View style={styles.section}>
          <TouchableOpacity 
            style={styles.sectionHeaderRow}
            onPress={() => setShowHistory(!showHistory)}
            data-testid="reading-history-toggle"
          >
            <Text style={styles.sectionTitle}>{t('readingHistory')}</Text>
            <Icon 
              name={showHistory ? "chevron-up" : "chevron-down"} 
              size={20} 
              color={COLORS.textLight} 
            />
          </TouchableOpacity>
          
          {showHistory && (
            <View style={styles.menuCard}>
              {readingHistory.length === 0 ? (
                <View style={styles.emptyHistory}>
                  <Icon name="book-outline" size={40} color={COLORS.textMuted} />
                  <Text style={styles.emptyHistoryText}>
                    {t('noHistory')}
                  </Text>
                </View>
              ) : (
                readingHistory.map((item, index) => (
                  <TouchableOpacity
                    key={`${item.book}-${item.chapter}-${index}`}
                    style={[
                      styles.historyItem,
                      index < readingHistory.length - 1 && styles.historyItemBorder
                    ]}
                    onPress={() => goToChapter(item.book, item.chapter)}
                    data-testid={`history-item-${item.book}-${item.chapter}`}
                  >
                    <View style={styles.historyIcon}>
                      <Icon name="book" size={20} color={COLORS.primary} />
                    </View>
                    <View style={styles.historyContent}>
                      <Text style={styles.historyTitle}>
                        {item.book} {item.chapter}
                      </Text>
                      <Text style={styles.historyMeta}>
                        {t('readCount')} {item.read_count || 1}x • {new Date(item.last_read).toLocaleDateString(currentLanguage)}
                      </Text>
                    </View>
                    <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
                  </TouchableOpacity>
                ))
              )}
            </View>
          )}
        </View>

        {/* App Features */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('appFeatures')}</Text>
          <View style={styles.menuCard}>
            <MenuItem
              icon="bookmark"
              title={t('myContentSection') || 'I Miei Contenuti'}
              subtitle={t('myContentDesc') || 'Segnalibri, note ed evidenziazioni'}
              onPress={() => router.push('/my-content')}
              color="#E91E63"
            />
            <MenuItem
              icon="school"
              title={t('quizSection')}
              subtitle={t('quizDesc')}
              onPress={() => router.push('/quiz')}
              color="#4CAF50"
            />
            <MenuItem
              icon="book"
              title={t('dictionarySection')}
              subtitle={t('dictionaryDesc')}
              onPress={() => router.push('/dictionary')}
              color={COLORS.primary}
            />
            <MenuItem
              icon="journal"
              title={t('journalSection')}
              subtitle={t('journalDesc')}
              onPress={() => router.push('/journal')}
              color={COLORS.secondary}
            />
            <MenuItem
              icon="people"
              title={t('groupsSection')}
              subtitle={t('groupsDesc')}
              onPress={() => router.push('/groups')}
              color="#9C27B0"
            />
            <MenuItem
              icon="heart"
              title={t('friendsSection') || 'I Miei Amici'}
              subtitle={t('friendsDesc') || 'Utenti preferiti'}
              onPress={() => router.push('/friends')}
              color="#E91E63"
            />
          </View>
        </View>

        {/* Account Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('account')}</Text>
          <View style={styles.menuCard}>
            <MenuItem
              icon="shield-checkmark"
              title={t('privacy')}
              subtitle={t('privacyDesc')}
              onPress={() => router.push('/privacy')}
              color={COLORS.primary}
            />
            <MenuItem
              icon="log-out"
              title={t('logout')}
              onPress={handleLogout}
              color={COLORS.error}
            />
            <MenuItem
              icon="trash"
              title={t('deleteAccount')}
              onPress={handleDeleteAccount}
              color={COLORS.error}
            />
          </View>
        </View>

        <Text style={styles.version}>{t('version')}: Amen! v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  topHeaderTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  profileHeader: {
    alignItems: 'center',
    paddingVertical: SPACING.xl,
    backgroundColor: COLORS.card,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
  },
  userName: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
  },
  userEmail: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: SPACING.xs,
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    marginHorizontal: SPACING.md,
    marginTop: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.small,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.primary,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: SPACING.xs,
  },
  statDivider: {
    width: 1,
    backgroundColor: COLORS.border,
  },
  section: {
    marginTop: SPACING.lg,
    paddingHorizontal: SPACING.md,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textLight,
    marginBottom: SPACING.sm,
    marginLeft: SPACING.xs,
  },
  menuCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    ...SHADOWS.small,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  menuContent: {
    flex: 1,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.text,
  },
  menuSubtitle: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  radioItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
  },
  radioItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  radioIcon: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  radioContent: {
    flex: 1,
  },
  radioName: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
  },
  radioMeta: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
  version: {
    textAlign: 'center',
    color: COLORS.textMuted,
    fontSize: 12,
    marginTop: SPACING.xl,
  },
  // Reading History Styles
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
    marginLeft: SPACING.xs,
    paddingRight: SPACING.xs,
  },
  emptyHistory: {
    alignItems: 'center',
    padding: SPACING.xl,
  },
  emptyHistoryText: {
    fontSize: 14,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: SPACING.md,
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
  },
  historyItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  historyIcon: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  historyContent: {
    flex: 1,
  },
  historyTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
  },
  historyMeta: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
});
