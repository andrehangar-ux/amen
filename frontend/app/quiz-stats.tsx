import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, FONT_SIZES } from '../src/utils/theme';
import Icon from '../src/components/Icon';

interface QuizStats {
  total_quizzes: number;
  total_questions: number;
  total_correct: number;
  average_score: number;
  best_score: number;
  categories_completed: Record<string, {
    attempts: number;
    best_score: number;
    total_correct: number;
    total_questions: number;
  }>;
  recent_quizzes: any[];
  streak: number;
}

const TRANSLATIONS = {
  it: {
    title: 'Statistiche Quiz',
    totalQuizzes: 'Quiz Completati',
    totalQuestions: 'Domande Totali',
    correctAnswers: 'Risposte Corrette',
    averageScore: 'Media Punteggio',
    bestScore: 'Miglior Punteggio',
    streak: 'Giorni Consecutivi',
    categoryStats: 'Statistiche per Categoria',
    recentActivity: 'Attività Recente',
    attempts: 'tentativi',
    noData: 'Nessun quiz completato ancora',
    startQuiz: 'Inizia un Quiz',
    accuracy: 'Precisione',
    loading: 'Caricamento...',
  },
  es: {
    title: 'Estadísticas del Quiz',
    totalQuizzes: 'Quizzes Completados',
    totalQuestions: 'Preguntas Totales',
    correctAnswers: 'Respuestas Correctas',
    averageScore: 'Puntuación Media',
    bestScore: 'Mejor Puntuación',
    streak: 'Días Consecutivos',
    categoryStats: 'Estadísticas por Categoría',
    recentActivity: 'Actividad Reciente',
    attempts: 'intentos',
    noData: 'Ningún quiz completado todavía',
    startQuiz: 'Iniciar Quiz',
    accuracy: 'Precisión',
    loading: 'Cargando...',
  },
  en: {
    title: 'Quiz Statistics',
    totalQuizzes: 'Quizzes Completed',
    totalQuestions: 'Total Questions',
    correctAnswers: 'Correct Answers',
    averageScore: 'Average Score',
    bestScore: 'Best Score',
    streak: 'Day Streak',
    categoryStats: 'Statistics by Category',
    recentActivity: 'Recent Activity',
    attempts: 'attempts',
    noData: 'No quizzes completed yet',
    startQuiz: 'Start a Quiz',
    accuracy: 'Accuracy',
    loading: 'Loading...',
  },
  de: {
    title: 'Quiz-Statistiken',
    totalQuizzes: 'Abgeschlossene Quizze',
    totalQuestions: 'Gesamtfragen',
    correctAnswers: 'Richtige Antworten',
    averageScore: 'Durchschnittspunktzahl',
    bestScore: 'Beste Punktzahl',
    streak: 'Tage in Folge',
    categoryStats: 'Statistiken nach Kategorie',
    recentActivity: 'Letzte Aktivität',
    attempts: 'Versuche',
    noData: 'Noch keine Quizze abgeschlossen',
    startQuiz: 'Quiz starten',
    accuracy: 'Genauigkeit',
    loading: 'Laden...',
  },
  fr: {
    title: 'Statistiques Quiz',
    totalQuizzes: 'Quiz Complétés',
    totalQuestions: 'Questions Totales',
    correctAnswers: 'Réponses Correctes',
    averageScore: 'Score Moyen',
    bestScore: 'Meilleur Score',
    streak: 'Jours Consécutifs',
    categoryStats: 'Statistiques par Catégorie',
    recentActivity: 'Activité Récente',
    attempts: 'tentatives',
    noData: 'Aucun quiz complété encore',
    startQuiz: 'Commencer un Quiz',
    accuracy: 'Précision',
    loading: 'Chargement...',
  },
  pt: {
    title: 'Estatísticas do Quiz',
    totalQuizzes: 'Quizzes Completados',
    totalQuestions: 'Perguntas Totais',
    correctAnswers: 'Respostas Corretas',
    averageScore: 'Pontuação Média',
    bestScore: 'Melhor Pontuação',
    streak: 'Dias Consecutivos',
    categoryStats: 'Estatísticas por Categoria',
    recentActivity: 'Atividade Recente',
    attempts: 'tentativas',
    noData: 'Nenhum quiz completado ainda',
    startQuiz: 'Iniciar Quiz',
    accuracy: 'Precisão',
    loading: 'Carregando...',
  },
};

export default function QuizStatsScreen() {
  const router = useRouter();
  const { currentLanguage } = useLanguageStore();
  const [stats, setStats] = useState<QuizStats | null>(null);
  const [loading, setLoading] = useState(true);

  const t = (key: keyof typeof TRANSLATIONS.it) => {
    return TRANSLATIONS[currentLanguage as keyof typeof TRANSLATIONS]?.[key] || TRANSLATIONS.it[key];
  };

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.getQuizStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    return date.toLocaleDateString(currentLanguage === 'en' ? 'en-US' : `${currentLanguage}-${currentLanguage.toUpperCase()}`, {
      day: 'numeric',
      month: 'short',
    });
  };

  const getCategoryName = (categoryId: string) => {
    // Remove "cat_" prefix if present
    return categoryId.replace('cat_', '').replace(/_/g, ' ');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Icon name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title}>{t('title')}</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>{t('loading')}</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!stats || stats.total_quizzes === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Icon name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title}>{t('title')}</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.emptyContainer}>
          <Icon name="stats-chart" size={64} color={COLORS.textMuted} />
          <Text style={styles.emptyText}>{t('noData')}</Text>
          <TouchableOpacity 
            style={styles.startButton}
            onPress={() => router.push('/quiz')}
          >
            <Text style={styles.startButtonText}>{t('startQuiz')}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const accuracy = stats.total_questions > 0 
    ? Math.round((stats.total_correct / stats.total_questions) * 100) 
    : 0;

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('title')}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Main Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={[styles.statCard, styles.statCardPrimary]}>
            <Icon name="trophy" size={28} color={COLORS.warning} />
            <Text style={styles.statValue}>{stats.best_score}%</Text>
            <Text style={styles.statLabel}>{t('bestScore')}</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="analytics" size={28} color={COLORS.primary} />
            <Text style={styles.statValue}>{stats.average_score}%</Text>
            <Text style={styles.statLabel}>{t('averageScore')}</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="flame" size={28} color={COLORS.error} />
            <Text style={styles.statValue}>{stats.streak}</Text>
            <Text style={styles.statLabel}>{t('streak')}</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="checkmark-circle" size={28} color={COLORS.success} />
            <Text style={styles.statValue}>{accuracy}%</Text>
            <Text style={styles.statLabel}>{t('accuracy')}</Text>
          </View>
        </View>

        {/* Summary Stats */}
        <View style={styles.summarySection}>
          <View style={styles.summaryRow}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>{stats.total_quizzes}</Text>
              <Text style={styles.summaryLabel}>{t('totalQuizzes')}</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>{stats.total_questions}</Text>
              <Text style={styles.summaryLabel}>{t('totalQuestions')}</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>{stats.total_correct}</Text>
              <Text style={styles.summaryLabel}>{t('correctAnswers')}</Text>
            </View>
          </View>
        </View>

        {/* Category Stats */}
        {Object.keys(stats.categories_completed).length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('categoryStats')}</Text>
            {Object.entries(stats.categories_completed).map(([catId, catStats]) => {
              const catAccuracy = catStats.total_questions > 0 
                ? Math.round((catStats.total_correct / catStats.total_questions) * 100) 
                : 0;
              return (
                <View key={catId} style={styles.categoryCard}>
                  <View style={styles.categoryHeader}>
                    <Text style={styles.categoryName}>{getCategoryName(catId)}</Text>
                    <View style={styles.categoryBadge}>
                      <Text style={styles.categoryBadgeText}>{catStats.best_score}%</Text>
                    </View>
                  </View>
                  <View style={styles.categoryStats}>
                    <Text style={styles.categoryStatText}>
                      {catStats.attempts} {t('attempts')} • {catAccuracy}% {t('accuracy')}
                    </Text>
                  </View>
                  <View style={styles.progressBar}>
                    <View style={[styles.progressFill, { width: `${catAccuracy}%` }]} />
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Recent Activity */}
        {stats.recent_quizzes.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t('recentActivity')}</Text>
            {stats.recent_quizzes.slice(0, 5).map((quiz, index) => (
              <View key={index} style={styles.activityItem}>
                <View style={styles.activityIcon}>
                  <Icon 
                    name={quiz.score >= 70 ? "checkmark-circle" : "close-circle"} 
                    size={24} 
                    color={quiz.score >= 70 ? COLORS.success : COLORS.error} 
                  />
                </View>
                <View style={styles.activityContent}>
                  <Text style={styles.activityTitle}>{getCategoryName(quiz.topic || '')}</Text>
                  <Text style={styles.activityDate}>{formatDate(quiz.created_at)}</Text>
                </View>
                <View style={styles.activityScore}>
                  <Text style={[
                    styles.activityScoreText,
                    quiz.score >= 70 ? styles.scoreGood : styles.scoreBad
                  ]}>
                    {quiz.score}%
                  </Text>
                  <Text style={styles.activityScoreDetail}>
                    {quiz.correct_count}/{quiz.total}
                  </Text>
                </View>
              </View>
            ))}
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: SPACING.xs,
  },
  title: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.text,
  },
  content: {
    flex: 1,
    padding: SPACING.md,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  emptyText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
    marginBottom: SPACING.lg,
  },
  startButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.xl,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
  },
  startButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: FONT_SIZES.md,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
  },
  statCardPrimary: {
    backgroundColor: COLORS.primary + '15',
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.xs,
  },
  statLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
    textAlign: 'center',
  },
  summarySection: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  summaryItem: {
    alignItems: 'center',
    flex: 1,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.primary,
  },
  summaryLabel: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
    textAlign: 'center',
  },
  summaryDivider: {
    width: 1,
    height: 40,
    backgroundColor: COLORS.border,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.md,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  categoryCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  categoryName: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '600',
    color: COLORS.text,
    textTransform: 'capitalize',
  },
  categoryBadge: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 2,
    borderRadius: BORDER_RADIUS.sm,
  },
  categoryBadgeText: {
    color: '#fff',
    fontSize: FONT_SIZES.xs,
    fontWeight: '600',
  },
  categoryStats: {
    marginBottom: SPACING.sm,
  },
  categoryStatText: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textSecondary,
  },
  progressBar: {
    height: 6,
    backgroundColor: COLORS.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 3,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  activityIcon: {
    marginRight: SPACING.md,
  },
  activityContent: {
    flex: 1,
  },
  activityTitle: {
    fontSize: FONT_SIZES.sm,
    fontWeight: '500',
    color: COLORS.text,
    textTransform: 'capitalize',
  },
  activityDate: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  activityScore: {
    alignItems: 'flex-end',
  },
  activityScoreText: {
    fontSize: FONT_SIZES.md,
    fontWeight: '700',
  },
  scoreGood: {
    color: COLORS.success,
  },
  scoreBad: {
    color: COLORS.error,
  },
  activityScoreDetail: {
    fontSize: FONT_SIZES.xs,
    color: COLORS.textSecondary,
  },
});
