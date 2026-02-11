import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Speech from 'expo-speech';
import { useAuthStore } from '../../src/store/authStore';
import { api } from '../../src/utils/api';
import { DailyVerseCard } from '../../src/components/DailyVerseCard';
import { MoodSelector } from '../../src/components/MoodSelector';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';

export default function HomeScreen() {
  const { user } = useAuthStore();
  const [dailyVerse, setDailyVerse] = useState<{ reference: string; text: string } | null>(null);
  const [progress, setProgress] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [moodCheckinResult, setMoodCheckinResult] = useState<any>(null);

  const loadData = useCallback(async () => {
    try {
      const [verse, prog] = await Promise.all([
        api.getDailyVerse(),
        api.getProgress(),
      ]);
      setDailyVerse(verse);
      setProgress(prog);
    } catch (error) {
      console.log('Error loading data:', error);
    }
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
      Speech.speak(dailyVerse.text, { language: 'it-IT' });
    }
  };

  const handleMoodSelect = async (mood: string) => {
    try {
      const result = await api.moodCheckin(mood);
      setMoodCheckinResult(result);
    } catch (error: any) {
      Alert.alert('Errore', error.message);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buongiorno';
    if (hour < 18) return 'Buon pomeriggio';
    return 'Buonasera';
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
            <Text style={styles.userName}>{user?.name || 'Fratello'}</Text>
          </View>
          <TouchableOpacity style={styles.notificationButton}>
            <Ionicons name="notifications-outline" size={24} color={COLORS.text} />
          </TouchableOpacity>
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
          <Text style={styles.sectionTitle}>Come ti senti oggi?</Text>
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
          <Text style={styles.sectionTitle}>Azioni Rapide</Text>
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/(tabs)/bible')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: COLORS.primary + '20' }]}>
                <Ionicons name="book" size={24} color={COLORS.primary} />
              </View>
              <Text style={styles.quickActionTitle}>Leggi</Text>
              <Text style={styles.quickActionSubtitle}>La Bibbia</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/(tabs)/journal')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: COLORS.accent + '20' }]}>
                <Ionicons name="create" size={24} color={COLORS.accent} />
              </View>
              <Text style={styles.quickActionTitle}>Scrivi</Text>
              <Text style={styles.quickActionSubtitle}>Nel Diario</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickActionCard}
              onPress={() => router.push('/assistant')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#A29BFE20' }]}>
                <Ionicons name="chatbubble-ellipses" size={24} color="#A29BFE" />
              </View>
              <Text style={styles.quickActionTitle}>Chiedi</Text>
              <Text style={styles.quickActionSubtitle}>All'Assistente</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Progress Overview */}
        {progress && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Il Tuo Progresso</Text>
            <View style={styles.progressCard}>
              <View style={styles.progressItem}>
                <View style={styles.progressIconContainer}>
                  <Ionicons name="flame" size={24} color={COLORS.error} />
                </View>
                <Text style={styles.progressValue}>{progress.reading_streak || 0}</Text>
                <Text style={styles.progressLabel}>Giorni di fila</Text>
              </View>
              <View style={styles.progressDivider} />
              <View style={styles.progressItem}>
                <View style={styles.progressIconContainer}>
                  <Ionicons name="book" size={24} color={COLORS.primary} />
                </View>
                <Text style={styles.progressValue}>{progress.total_chapters_read || 0}</Text>
                <Text style={styles.progressLabel}>Capitoli letti</Text>
              </View>
              <View style={styles.progressDivider} />
              <View style={styles.progressItem}>
                <View style={styles.progressIconContainer}>
                  <Ionicons name="create" size={24} color={COLORS.accent} />
                </View>
                <Text style={styles.progressValue}>{progress.total_journal_entries || 0}</Text>
                <Text style={styles.progressLabel}>Voci diario</Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
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
});
