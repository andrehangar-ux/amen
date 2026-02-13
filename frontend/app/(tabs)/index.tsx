import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import * as Speech from 'expo-speech';
import { useAuthStore } from '../../src/store/authStore';
import { useLanguageStore, useTranslation } from '../../src/store/languageStore';
import { api } from '../../src/utils/api';
import { DailyVerseCard } from '../../src/components/DailyVerseCard';
import { MoodSelector } from '../../src/components/MoodSelector';
import { LanguageSelector } from '../../src/components/LanguageSelector';
import { Icon } from '../../src/components/Icon';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';

// Cross-platform TTS helper
const speakText = (text: string, langCode: string) => {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode;
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  } else {
    Speech.speak(text, { language: langCode });
  }
};

export default function HomeScreen() {
  const { user } = useAuthStore();
  const { currentLanguage, languages, loadLanguage } = useLanguageStore();
  const { t } = useTranslation();
  const [dailyVerse, setDailyVerse] = useState<{ reference: string; text: string } | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [moodCheckinResult, setMoodCheckinResult] = useState<any>(null);
  const [showLanguageSelector, setShowLanguageSelector] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [verse, prog] = await Promise.all([
        api.getDailyVerse(currentLanguage),
        api.getProgress(),
      ]);
      setDailyVerse(verse);
      setProgress(prog);
    } catch (error) {
      console.log('Error loading data:', error);
    }
  }, [currentLanguage]);

  useEffect(() => {
    loadLanguage();
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleSpeak = () => {
    if (dailyVerse) {
      const ttsCode = languages[currentLanguage]?.tts_code || 'it-IT';
      speakText(dailyVerse.text, ttsCode);
    }
  };

  const handleMoodSelect = async (mood: string) => {
    try {
      const result = await api.moodCheckin(mood, currentLanguage);
      setMoodCheckinResult(result);
    } catch (error: any) {
      Alert.alert(t('error'), error.message);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('goodMorning');
    if (hour < 18) return t('goodAfternoon');
    return t('goodEvening');
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>{getGreeting()},</Text>
            <Text style={styles.userName}>{user?.name || t('brother')}</Text>
          </View>
          <View style={styles.headerActions}>
            <TouchableOpacity
              style={styles.languageButton}
              onPress={() => setShowLanguageSelector(true)}
            >
              <Text style={styles.languageFlag}>{languages[currentLanguage]?.flag || '🇮🇹'}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.notificationButton}>
              <Icon name="notifications-outline" size={24} color={COLORS.text} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Daily Verse */}
        {dailyVerse && (
          <DailyVerseCard
            reference={dailyVerse.reference}
            text={dailyVerse.text}
            onSpeak={handleSpeak}
          />
        )}

        {/* Mood Check-in */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('howAreYou')}</Text>
          <MoodSelector
            selectedMood={moodCheckinResult?.mood || null}
            onSelect={handleMoodSelect}
            horizontal
          />
        </View>

        {/* Mood Result */}
        {moodCheckinResult && (
          <View style={styles.moodResult}>
            <View style={styles.moodVerseContainer}>
              <Text style={styles.moodVerseRef}>{moodCheckinResult.verse?.ref}</Text>
              <Text style={styles.moodVerseText}>"{moodCheckinResult.verse?.text}"</Text>
            </View>
            <Text style={styles.moodReflection}>{moodCheckinResult.reflection}</Text>
          </View>
        )}

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('quickActions')}</Text>
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/(tabs)/bible')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: COLORS.primary + '20' }]}>
                <Icon name="book" size={24} color={COLORS.primary} />
              </View>
              <Text style={styles.quickActionTitle}>{t('read')}</Text>
              <Text style={styles.quickActionSubtitle}>{t('theBible')}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/(tabs)/journal')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: COLORS.accent + '20' }]}>
                <Icon name="create" size={24} color={COLORS.accent} />
              </View>
              <Text style={styles.quickActionTitle}>{t('write')}</Text>
              <Text style={styles.quickActionSubtitle}>{t('inJournal')}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/community')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#74B9FF20' }]}>
                <Icon name="people" size={24} color="#74B9FF" />
              </View>
              <Text style={styles.quickActionTitle}>{t('community')}</Text>
              <Text style={styles.quickActionSubtitle}>{t('worldwide')}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Progress Overview */}
        {progress && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('yourProgress')}</Text>
            <View style={styles.progressCard}>
              <View style={styles.progressItem}>
                <View style={styles.progressIconContainer}>
                  <Icon name="flame" size={24} color={COLORS.error} />
                </View>
                <Text style={styles.progressValue}>{progress.reading_streak || 0}</Text>
                <Text style={styles.progressLabel}>{t('daysInRow')}</Text>
              </View>
              <View style={styles.progressDivider} />
              <View style={styles.progressItem}>
                <View style={styles.progressIconContainer}>
                  <Icon name="book" size={24} color={COLORS.primary} />
                </View>
                <Text style={styles.progressValue}>{progress.total_chapters_read || 0}</Text>
                <Text style={styles.progressLabel}>{t('chaptersRead')}</Text>
              </View>
              <View style={styles.progressDivider} />
              <View style={styles.progressItem}>
                <View style={styles.progressIconContainer}>
                  <Icon name="create" size={24} color={COLORS.accent} />
                </View>
                <Text style={styles.progressValue}>{progress.total_journal_entries || 0}</Text>
                <Text style={styles.progressLabel}>{t('journalEntries')}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Esplora Features */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('explore')}</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.exploreScroll}>
            <TouchableOpacity style={styles.exploreCard} onPress={() => router.push('/quiz')}>
              <View style={[styles.exploreIcon, { backgroundColor: '#FF6B6B20' }]}>
                <Icon name="help-circle" size={26} color="#FF6B6B" />
              </View>
              <Text style={styles.exploreTitle}>{t('quizzes')}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.exploreCard} onPress={() => router.push('/dictionary')}>
              <View style={[styles.exploreIcon, { backgroundColor: '#4ECDC420' }]}>
                <Icon name="language" size={26} color="#4ECDC4" />
              </View>
              <Text style={styles.exploreTitle}>{t('dictionary')}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.exploreCard} onPress={() => router.push('/forum')}>
              <View style={[styles.exploreIcon, { backgroundColor: '#9B59B620' }]}>
                <Icon name="chatbubbles" size={26} color="#9B59B6" />
              </View>
              <Text style={styles.exploreTitle}>{t('forum')}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.exploreCard} onPress={() => router.push('/maps')}>
              <View style={[styles.exploreIcon, { backgroundColor: '#3498DB20' }]}>
                <Icon name="map" size={26} color="#3498DB" />
              </View>
              <Text style={styles.exploreTitle}>{t('maps')}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.exploreCard} onPress={() => router.push('/events')}>
              <View style={[styles.exploreIcon, { backgroundColor: '#E91E6320' }]}>
                <Icon name="videocam" size={26} color="#E91E63" />
              </View>
              <Text style={styles.exploreTitle}>{t('liveEvents')}</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </ScrollView>

      {/* Language Selector Modal */}
      <LanguageSelector
        visible={showLanguageSelector}
        onClose={() => setShowLanguageSelector(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 120,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  greeting: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  languageButton: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
    ...SHADOWS.small,
  },
  languageFlag: {
    fontSize: 22,
  },
  notificationButton: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.card,
    justifyContent: 'center',
    alignItems: 'center',
    ...SHADOWS.small,
  },
  section: {
    marginTop: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: SPACING.sm,
  },
  quickActionCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
    ...SHADOWS.small,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: BORDER_RADIUS.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  quickActionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  quickActionSubtitle: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  progressCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    flexDirection: 'row',
    alignItems: 'center',
    ...SHADOWS.small,
  },
  progressItem: {
    flex: 1,
    alignItems: 'center',
  },
  progressIconContainer: {
    marginBottom: SPACING.xs,
  },
  progressValue: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  progressLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    textAlign: 'center',
  },
  progressDivider: {
    width: 1,
    height: 60,
    backgroundColor: COLORS.border,
  },
  moodResult: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginTop: SPACING.md,
    ...SHADOWS.small,
  },
  moodVerseContainer: {
    marginBottom: SPACING.md,
    paddingBottom: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  moodVerseRef: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  moodVerseText: {
    fontSize: 16,
    fontStyle: 'italic',
    color: COLORS.text,
    lineHeight: 24,
  },
  moodReflection: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 22,
  },
  exploreScroll: {
    marginHorizontal: -SPACING.md,
    paddingHorizontal: SPACING.md,
  },
  exploreCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginRight: SPACING.md,
    alignItems: 'center',
    width: 100,
    ...SHADOWS.small,
  },
  exploreIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  exploreTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
    textAlign: 'center',
  },
});
