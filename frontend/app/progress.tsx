import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useTranslation } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';
import { format } from 'date-fns';

interface BookProgress {
  book: string;
  chapters_read: number;
  total_reads: number;
  last_read: string | null;
}

interface ChapterRead {
  book: string;
  chapter: number;
}

interface ReadingStats {
  basic_stats: {
    reading_streak: number;
    total_chapters_read: number;
    total_journal_entries: number;
  };
  total_unique_chapters: number;
  total_read_count: number;
  books_progress: BookProgress[];
  recent_activity_count: number;
  chapters_read: ChapterRead[];
}

export default function ProgressScreen() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<ReadingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedBook, setExpandedBook] = useState<string | null>(null);
  const [bookChapters, setBookChapters] = useState<{[key: string]: number[]}>({});

  const loadStats = useCallback(async () => {
    try {
      const data = await api.getReadingStats();
      setStats(data);
      
      // Group chapters by book
      const grouped: {[key: string]: number[]} = {};
      data.chapters_read?.forEach((ch: ChapterRead) => {
        if (!grouped[ch.book]) grouped[ch.book] = [];
        if (!grouped[ch.book].includes(ch.chapter)) {
          grouped[ch.book].push(ch.chapter);
        }
      });
      // Sort chapters
      Object.keys(grouped).forEach(book => {
        grouped[book].sort((a, b) => a - b);
      });
      setBookChapters(grouped);
    } catch (error) {
      console.log('Error loading stats:', error);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadStats().finally(() => setLoading(false));
  }, [loadStats]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadStats();
    setRefreshing(false);
  };

  const navigateToChapter = (book: string, chapter: number) => {
    router.push({
      pathname: '/(tabs)/bible',
      params: { book, chapter: chapter.toString() }
    });
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
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('myProgress') || 'I Miei Progressi'}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Main Stats Card */}
        <View style={styles.mainStatsCard}>
          <View style={styles.mainStatRow}>
            <View style={styles.mainStatItem}>
              <View style={[styles.statIconContainer, { backgroundColor: COLORS.primary + '20' }]}>
                <Icon name="flame" size={24} color={COLORS.primary} />
              </View>
              <Text style={styles.mainStatValue}>{stats?.basic_stats?.reading_streak || 0}</Text>
              <Text style={styles.mainStatLabel}>{t('streak') || 'Serie'}</Text>
            </View>
            
            <View style={styles.statDivider} />
            
            <View style={styles.mainStatItem}>
              <View style={[styles.statIconContainer, { backgroundColor: '#4CAF50' + '20' }]}>
                <Icon name="book" size={24} color="#4CAF50" />
              </View>
              <Text style={styles.mainStatValue}>{stats?.total_unique_chapters || 0}</Text>
              <Text style={styles.mainStatLabel}>{t('chaptersRead') || 'Capitoli Letti'}</Text>
            </View>
            
            <View style={styles.statDivider} />
            
            <View style={styles.mainStatItem}>
              <View style={[styles.statIconContainer, { backgroundColor: '#2196F3' + '20' }]}>
                <Icon name="repeat" size={24} color="#2196F3" />
              </View>
              <Text style={styles.mainStatValue}>{stats?.total_read_count || 0}</Text>
              <Text style={styles.mainStatLabel}>{t('totalReads') || 'Letture Totali'}</Text>
            </View>
          </View>
        </View>

        {/* Recent Activity */}
        <View style={styles.activityCard}>
          <View style={styles.activityHeader}>
            <Icon name="time" size={20} color={COLORS.primary} />
            <Text style={styles.activityTitle}>{t('recentActivity') || 'Attività Recente'}</Text>
          </View>
          <Text style={styles.activityText}>
            {stats?.recent_activity_count || 0} {t('chaptersLast7Days') || 'capitoli letti negli ultimi 7 giorni'}
          </Text>
        </View>

        {/* Books Progress */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('progressByBook') || 'Progressi per Libro'}</Text>
          
          {stats?.books_progress && stats.books_progress.length > 0 ? (
            stats.books_progress.map((bookProg) => (
              <View key={bookProg.book} style={styles.bookCard}>
                <TouchableOpacity
                  style={styles.bookHeader}
                  onPress={() => setExpandedBook(expandedBook === bookProg.book ? null : bookProg.book)}
                >
                  <View style={styles.bookInfo}>
                    <Text style={styles.bookName}>{bookProg.book}</Text>
                    <Text style={styles.bookStats}>
                      {bookProg.chapters_read} {t('chapters') || 'capitoli'} • {bookProg.total_reads} {t('reads') || 'letture'}
                    </Text>
                  </View>
                  <View style={styles.bookRight}>
                    <View style={styles.chaptersBadge}>
                      <Text style={styles.chaptersBadgeText}>{bookProg.chapters_read}</Text>
                    </View>
                    <Icon 
                      name={expandedBook === bookProg.book ? "chevron-up" : "chevron-down"} 
                      size={20} 
                      color={COLORS.textLight} 
                    />
                  </View>
                </TouchableOpacity>
                
                {expandedBook === bookProg.book && bookChapters[bookProg.book] && (
                  <View style={styles.chaptersGrid}>
                    <Text style={styles.chaptersGridTitle}>{t('chaptersRead') || 'Capitoli Letti'}:</Text>
                    <View style={styles.chaptersContainer}>
                      {bookChapters[bookProg.book].map((chapter) => (
                        <TouchableOpacity
                          key={chapter}
                          style={styles.chapterChip}
                          onPress={() => navigateToChapter(bookProg.book, chapter)}
                        >
                          <Text style={styles.chapterChipText}>{chapter}</Text>
                          <Icon name="checkmark" size={12} color="#fff" />
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>
                )}
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Icon name="book-outline" size={48} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>{t('noReadingProgress') || 'Nessun progresso di lettura'}</Text>
              <Text style={styles.emptySubtext}>{t('startReadingBible') || 'Inizia a leggere la Bibbia per tracciare i tuoi progressi'}</Text>
              <TouchableOpacity 
                style={styles.startButton}
                onPress={() => router.push('/(tabs)/bible')}
              >
                <Icon name="book" size={18} color="#fff" />
                <Text style={styles.startButtonText}>{t('startReading') || 'Inizia a Leggere'}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* All Chapters Read Summary */}
        {stats?.chapters_read && stats.chapters_read.length > 0 && (
          <View style={styles.summaryCard}>
            <View style={styles.summaryHeader}>
              <Icon name="trophy" size={20} color="#FFD700" />
              <Text style={styles.summaryTitle}>{t('yourAchievement') || 'Il Tuo Traguardo'}</Text>
            </View>
            <Text style={styles.summaryText}>
              {t('youHaveRead') || 'Hai letto'} <Text style={styles.highlightText}>{stats.total_unique_chapters}</Text> {t('uniqueChaptersFrom') || 'capitoli unici da'} <Text style={styles.highlightText}>{Object.keys(bookChapters).length}</Text> {t('differentBooks') || 'libri diversi'}!
            </Text>
          </View>
        )}

        <View style={{ height: 40 }} />
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
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  content: {
    flex: 1,
    padding: SPACING.md,
  },
  mainStatsCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    ...SHADOWS.sm,
  },
  mainStatRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  mainStatItem: {
    alignItems: 'center',
    flex: 1,
  },
  statIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  mainStatValue: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
  },
  mainStatLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 4,
    textAlign: 'center',
  },
  statDivider: {
    width: 1,
    height: 60,
    backgroundColor: COLORS.border,
  },
  activityCard: {
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  activityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.xs,
  },
  activityTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  activityText: {
    fontSize: 13,
    color: COLORS.textLight,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  bookCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    overflow: 'hidden',
    ...SHADOWS.sm,
  },
  bookHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: SPACING.md,
  },
  bookInfo: {
    flex: 1,
  },
  bookName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  bookStats: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
  bookRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  chaptersBadge: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
    minWidth: 28,
    alignItems: 'center',
  },
  chaptersBadgeText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 12,
  },
  chaptersGrid: {
    padding: SPACING.md,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  chaptersGridTitle: {
    fontSize: 12,
    color: COLORS.textLight,
    marginBottom: SPACING.sm,
    marginTop: SPACING.sm,
  },
  chaptersContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.xs,
  },
  chapterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4CAF50',
    paddingHorizontal: SPACING.sm,
    paddingVertical: 6,
    borderRadius: BORDER_RADIUS.md,
    gap: 4,
  },
  chapterChipText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 13,
  },
  emptyState: {
    alignItems: 'center',
    padding: SPACING.xl,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textLight,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 13,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: SPACING.xs,
    marginBottom: SPACING.md,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
    gap: SPACING.sm,
  },
  startButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  summaryCard: {
    backgroundColor: '#FFD700' + '15',
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: '#FFD700' + '30',
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  summaryTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.text,
  },
  summaryText: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 22,
  },
  highlightText: {
    fontWeight: '700',
    color: COLORS.primary,
  },
});
