import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface ReadingEntry {
  book: string;
  chapter: number;
  last_read: string;
  read_count?: number;
}

interface Progress {
  reading_streak: number;
  total_chapters_read: number;
  total_journal_entries: number;
  books_completed?: number;
}

export default function ReadingProgressScreen() {
  const { currentLanguage } = useLanguageStore();
  const [progress, setProgress] = useState<Progress | null>(null);
  const [history, setHistory] = useState<ReadingEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const translations: Record<string, Record<string, string>> = {
    it: {
      title: 'I Miei Progressi',
      subtitle: 'Monitora la tua lettura biblica',
      streak: 'Giorni consecutivi',
      chaptersRead: 'Capitoli letti',
      journalEntries: 'Voci diario',
      recentReading: 'Letture Recenti',
      noHistory: 'Nessun capitolo letto',
      startReading: 'Inizia a leggere la Bibbia!',
      readOn: 'Letto il',
      goToChapter: 'Vai al capitolo',
      continueReading: 'Continua a Leggere',
      times: 'volte',
    },
    en: {
      title: 'My Progress',
      subtitle: 'Track your Bible reading',
      streak: 'Day streak',
      chaptersRead: 'Chapters read',
      journalEntries: 'Journal entries',
      recentReading: 'Recent Reading',
      noHistory: 'No chapters read',
      startReading: 'Start reading the Bible!',
      readOn: 'Read on',
      goToChapter: 'Go to chapter',
      continueReading: 'Continue Reading',
      times: 'times',
    },
    es: {
      title: 'Mi Progreso',
      subtitle: 'Sigue tu lectura bíblica',
      streak: 'Racha de días',
      chaptersRead: 'Capítulos leídos',
      journalEntries: 'Entradas del diario',
      recentReading: 'Lecturas Recientes',
      noHistory: 'Sin capítulos leídos',
      startReading: '¡Empieza a leer la Biblia!',
      readOn: 'Leído el',
      goToChapter: 'Ir al capítulo',
      continueReading: 'Continuar Leyendo',
      times: 'veces',
    },
    pt: {
      title: 'Meu Progresso',
      subtitle: 'Acompanhe sua leitura bíblica',
      streak: 'Sequência de dias',
      chaptersRead: 'Capítulos lidos',
      journalEntries: 'Entradas do diário',
      recentReading: 'Leituras Recentes',
      noHistory: 'Nenhum capítulo lido',
      startReading: 'Comece a ler a Bíblia!',
      readOn: 'Lido em',
      goToChapter: 'Ir ao capítulo',
      continueReading: 'Continuar Lendo',
      times: 'vezes',
    },
    fr: {
      title: 'Ma Progression',
      subtitle: 'Suivez votre lecture biblique',
      streak: 'Jours consécutifs',
      chaptersRead: 'Chapitres lus',
      journalEntries: 'Entrées du journal',
      recentReading: 'Lectures Récentes',
      noHistory: 'Aucun chapitre lu',
      startReading: 'Commencez à lire la Bible!',
      readOn: 'Lu le',
      goToChapter: 'Aller au chapitre',
      continueReading: 'Continuer la Lecture',
      times: 'fois',
    },
    de: {
      title: 'Mein Fortschritt',
      subtitle: 'Verfolge dein Bibellesen',
      streak: 'Tage in Folge',
      chaptersRead: 'Kapitel gelesen',
      journalEntries: 'Tagebucheinträge',
      recentReading: 'Kürzlich Gelesen',
      noHistory: 'Keine Kapitel gelesen',
      startReading: 'Beginne mit dem Bibellesen!',
      readOn: 'Gelesen am',
      goToChapter: 'Zum Kapitel gehen',
      continueReading: 'Weiterlesen',
      times: 'mal',
    },
  };

  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  const loadData = useCallback(async () => {
    try {
      const [progressData, historyData] = await Promise.all([
        api.getProgress(),
        api.getReadingHistory(50),
      ]);
      setProgress(progressData);
      setHistory(historyData?.history || []);
    } catch (error) {
      console.error('Error loading progress:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const goToChapter = (book: string, chapter: number) => {
    router.push({
      pathname: '/(tabs)/bible',
      params: { book, chapter: chapter.toString() }
    });
  };

  const goToBible = () => {
    router.push('/(tabs)/bible');
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    
    try {
      const date = new Date(dateString);
      // Check if date is valid
      if (isNaN(date.getTime())) return '-';
      
      const locale = currentLanguage === 'en' ? 'en-US' : `${currentLanguage}-${currentLanguage.toUpperCase()}`;
      return date.toLocaleDateString(locale, { 
        day: 'numeric', 
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '-';
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} data-testid="reading-progress-screen">
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          onPress={() => router.back()} 
          style={styles.backBtn}
          data-testid="progress-back-btn"
        >
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.title}>{t('title')}</Text>
          <Text style={styles.subtitle}>{t('subtitle')}</Text>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Stats Cards */}
        {progress && (
          <View style={styles.statsContainer}>
            <View style={[styles.statCard, { backgroundColor: '#FFE4B5' }]}>
              <Icon name="flame" size={28} color="#FF6B35" />
              <Text style={styles.statValue}>{progress.reading_streak || 0}</Text>
              <Text style={styles.statLabel}>{t('streak')}</Text>
            </View>
            <View style={[styles.statCard, { backgroundColor: '#E8F5E9' }]}>
              <Icon name="book" size={28} color="#4CAF50" />
              <Text style={styles.statValue}>{progress.total_chapters_read || 0}</Text>
              <Text style={styles.statLabel}>{t('chaptersRead')}</Text>
            </View>
            <View style={[styles.statCard, { backgroundColor: '#E3F2FD' }]}>
              <Icon name="journal" size={28} color="#2196F3" />
              <Text style={styles.statValue}>{progress.total_journal_entries || 0}</Text>
              <Text style={styles.statLabel}>{t('journalEntries')}</Text>
            </View>
          </View>
        )}

        {/* Continue Reading Button */}
        <TouchableOpacity 
          style={styles.continueBtn}
          onPress={goToBible}
          data-testid="continue-reading-btn"
        >
          <Icon name="book-outline" size={24} color="#fff" />
          <Text style={styles.continueBtnText}>{t('continueReading')}</Text>
          <Icon name="arrow-forward" size={20} color="#fff" />
        </TouchableOpacity>

        {/* Recent Reading */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('recentReading')}</Text>
          
          {history.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="book-outline" size={64} color={COLORS.textSecondary} />
              <Text style={styles.emptyText}>{t('noHistory')}</Text>
              <Text style={styles.emptyHint}>{t('startReading')}</Text>
            </View>
          ) : (
            history.map((item, index) => (
              <TouchableOpacity
                key={`${item.book}-${item.chapter}-${index}`}
                style={styles.historyCard}
                onPress={() => goToChapter(item.book, item.chapter)}
                data-testid={`history-${item.book}-${item.chapter}`}
              >
                <View style={styles.historyIcon}>
                  <Icon name="book" size={24} color={COLORS.primary} />
                </View>
                <View style={styles.historyContent}>
                  <Text style={styles.historyTitle}>{item.book} {item.chapter}</Text>
                  <Text style={styles.historyDate}>
                    {t('readOn')} {formatDate(item.read_at)}
                    {item.read_count && item.read_count > 1 && (
                      <Text style={styles.readCount}> • {item.read_count}x {t('times')}</Text>
                    )}
                  </Text>
                </View>
                <Icon name="chevron-forward" size={20} color={COLORS.textSecondary} />
              </TouchableOpacity>
            ))
          )}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backBtn: {
    padding: SPACING.sm,
    marginRight: SPACING.md,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: SPACING.md,
    paddingBottom: SPACING.xl * 2,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: SPACING.lg,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    marginHorizontal: 4,
    ...SHADOWS.small,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.xs,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
    textAlign: 'center',
  },
  continueBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.lg,
    gap: SPACING.sm,
    ...SHADOWS.medium,
  },
  continueBtnText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
    textAlign: 'center',
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  historyCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  historyIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  historyContent: {
    flex: 1,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  historyDate: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  readCount: {
    color: COLORS.primary,
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xl * 2,
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.lg,
  },
  emptyHint: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
  },
});
