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
import { router } from 'expo-router';
import { useAuthStore } from '../../src/store/authStore';
import { api } from '../../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';

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

export default function ProfileScreen() {
  const { user, logout, setUser, setSessionToken } = useAuthStore();
  const [progress, setProgress] = useState<any>(null);
  const [readingHistory, setReadingHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

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
      'Disconnetti',
      'Vuoi uscire dal tuo account?',
      async () => {
        try {
          await logout();
          // Clear auth state explicitly
          setUser(null);
          setSessionToken(null);
          // Force navigation to login
          router.replace('/(auth)/login');
        } catch (error) {
          console.error('Logout error:', error);
          // Force logout anyway
          setUser(null);
          setSessionToken(null);
          router.replace('/(auth)/login');
        }
      }
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
              <Text style={styles.statLabel}>Giorni</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{progress.total_chapters_read || 0}</Text>
              <Text style={styles.statLabel}>Capitoli</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{progress.total_journal_entries || 0}</Text>
              <Text style={styles.statLabel}>Voci</Text>
            </View>
          </View>
        )}

        {/* Reading History Section */}
        <View style={styles.section}>
          <TouchableOpacity 
            style={styles.sectionHeaderRow}
            onPress={() => setShowHistory(!showHistory)}
          >
            <Text style={styles.sectionTitle}>Cronologia Lettura</Text>
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
                    Nessun capitolo letto. Inizia a leggere la Bibbia!
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
                  >
                    <View style={styles.historyIcon}>
                      <Icon name="book" size={20} color={COLORS.primary} />
                    </View>
                    <View style={styles.historyContent}>
                      <Text style={styles.historyTitle}>
                        {item.book} {item.chapter}
                      </Text>
                      <Text style={styles.historyMeta}>
                        Letto {item.read_count || 1}x • {new Date(item.last_read).toLocaleDateString('it-IT')}
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
          <Text style={styles.sectionTitle}>Funzionalità</Text>
          <View style={styles.menuCard}>
            <MenuItem
              icon="radio"
              title="Radio Evangeliche"
              subtitle="Ascolta radio da tutto il mondo"
              onPress={() => router.push('/radio')}
              color={COLORS.primary}
            />
            <MenuItem
              icon="people"
              title="Community"
              subtitle="Forum e condivisione"
              onPress={() => router.push('/community')}
              color={COLORS.secondary}
            />
            <MenuItem
              icon="school"
              title="Quiz Biblici"
              subtitle="Metti alla prova le tue conoscenze"
              onPress={() => router.push('/quiz')}
              color="#4CAF50"
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Supporta il Ministero</Text>
          <View style={styles.menuCard}>
            <MenuItem
              icon="heart"
              title="Fai una Donazione"
              subtitle="Supporta Amen!"
              onPress={() => router.push('/donate')}
              color={COLORS.error}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>
          <View style={styles.menuCard}>
            <MenuItem
              icon="settings"
              title="Impostazioni"
              subtitle="Preferenze, lingua, notifiche"
              onPress={() => router.push('/settings')}
              color={COLORS.textLight}
            />
            <MenuItem
              icon="help-circle"
              title="Aiuto"
              subtitle="FAQ, contattaci"
              onPress={() => router.push('/faq')}
              color={COLORS.primary}
            />
            <MenuItem
              icon="log-out"
              title="Esci"
              subtitle="Disconnetti il tuo account"
              onPress={handleLogout}
              color={COLORS.error}
              data-testid="profile-logout-button"
            />
          </View>
        </View>

        <Text style={styles.version}>Amen! v1.0.0</Text>
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
  scrollContent: {
    paddingBottom: 120,
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
});
