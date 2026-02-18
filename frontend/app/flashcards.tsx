import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface Flashcard {
  flashcard_id: string;
  term_id: string;
  term: string;
  meaning: string;
  description?: string;
  origin: string;
  mastery_level: number;
  note?: string;
}

interface FlashcardStats {
  total_flashcards: number;
  due_for_review: number;
  mastered: number;
  mastery_distribution: Record<number, number>;
}

export default function FlashcardsScreen() {
  const { currentLanguage } = useLanguageStore();
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [dueCards, setDueCards] = useState<Flashcard[]>([]);
  const [stats, setStats] = useState<FlashcardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [studyMode, setStudyMode] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [flipAnim] = useState(new Animated.Value(0));
  const [reviewLoading, setReviewLoading] = useState(false);

  const translations: Record<string, Record<string, string>> = {
    it: {
      title: 'Flashcards',
      subtitle: 'Studia i termini biblici con la ripetizione spaziata',
      startStudy: 'Inizia a Studiare',
      allCards: 'Tutte le Card',
      dueForReview: 'Da Rivedere',
      mastered: 'Padroneggiati',
      noCards: 'Nessuna flashcard',
      noCardsDesc: 'Aggiungi termini dal dizionario per iniziare a studiare',
      goToDictionary: 'Vai al Dizionario',
      tapToFlip: 'Tocca per girare',
      howWellDidYouKnow: 'Quanto bene conoscevi questo termine?',
      again: 'Ripeti',
      hard: 'Difficile',
      good: 'Bene',
      easy: 'Facile',
      perfect: 'Perfetto',
      studyComplete: 'Studio Completato!',
      studyCompleteDesc: 'Hai completato tutte le card in coda.',
      back: 'Torna Indietro',
      cardsToReview: 'card da rivedere',
      totalCards: 'card totali',
      level: 'Livello',
      delete: 'Elimina',
    },
    en: {
      title: 'Flashcards',
      subtitle: 'Study biblical terms with spaced repetition',
      startStudy: 'Start Studying',
      allCards: 'All Cards',
      dueForReview: 'Due for Review',
      mastered: 'Mastered',
      noCards: 'No flashcards',
      noCardsDesc: 'Add terms from the dictionary to start studying',
      goToDictionary: 'Go to Dictionary',
      tapToFlip: 'Tap to flip',
      howWellDidYouKnow: 'How well did you know this term?',
      again: 'Again',
      hard: 'Hard',
      good: 'Good',
      easy: 'Easy',
      perfect: 'Perfect',
      studyComplete: 'Study Complete!',
      studyCompleteDesc: 'You have completed all due cards.',
      back: 'Go Back',
      cardsToReview: 'cards to review',
      totalCards: 'total cards',
      level: 'Level',
      delete: 'Delete',
    },
    es: {
      title: 'Flashcards',
      subtitle: 'Estudia los términos bíblicos con repetición espaciada',
      startStudy: 'Empezar a Estudiar',
      allCards: 'Todas las Tarjetas',
      dueForReview: 'Por Revisar',
      mastered: 'Dominados',
      noCards: 'Sin flashcards',
      noCardsDesc: 'Añade términos del diccionario para empezar a estudiar',
      goToDictionary: 'Ir al Diccionario',
      tapToFlip: 'Toca para voltear',
      howWellDidYouKnow: '¿Qué tan bien conocías este término?',
      again: 'Otra vez',
      hard: 'Difícil',
      good: 'Bien',
      easy: 'Fácil',
      perfect: 'Perfecto',
      studyComplete: '¡Estudio Completado!',
      studyCompleteDesc: 'Has completado todas las tarjetas pendientes.',
      back: 'Volver',
      cardsToReview: 'tarjetas por revisar',
      totalCards: 'tarjetas totales',
      level: 'Nivel',
      delete: 'Eliminar',
    },
    de: {
      title: 'Karteikarten',
      subtitle: 'Biblische Begriffe mit Abstandswiederholung lernen',
      startStudy: 'Lernen Starten',
      allCards: 'Alle Karten',
      dueForReview: 'Zur Überprüfung',
      mastered: 'Gemeistert',
      noCards: 'Keine Karteikarten',
      noCardsDesc: 'Füge Begriffe aus dem Wörterbuch hinzu, um zu lernen',
      goToDictionary: 'Zum Wörterbuch',
      tapToFlip: 'Tippen zum Umdrehen',
      howWellDidYouKnow: 'Wie gut kanntest du diesen Begriff?',
      again: 'Nochmal',
      hard: 'Schwer',
      good: 'Gut',
      easy: 'Einfach',
      perfect: 'Perfekt',
      studyComplete: 'Lernen Abgeschlossen!',
      studyCompleteDesc: 'Du hast alle fälligen Karten bearbeitet.',
      back: 'Zurück',
      cardsToReview: 'Karten zur Überprüfung',
      totalCards: 'Karten insgesamt',
      level: 'Stufe',
      delete: 'Löschen',
    },
    fr: {
      title: 'Flashcards',
      subtitle: 'Étudiez les termes bibliques avec la répétition espacée',
      startStudy: 'Commencer à Étudier',
      allCards: 'Toutes les Cartes',
      dueForReview: 'À Réviser',
      mastered: 'Maîtrisés',
      noCards: 'Pas de flashcards',
      noCardsDesc: 'Ajoutez des termes du dictionnaire pour commencer',
      goToDictionary: 'Aller au Dictionnaire',
      tapToFlip: 'Touchez pour retourner',
      howWellDidYouKnow: 'Quelle était votre connaissance de ce terme?',
      again: 'Encore',
      hard: 'Difficile',
      good: 'Bien',
      easy: 'Facile',
      perfect: 'Parfait',
      studyComplete: 'Étude Terminée!',
      studyCompleteDesc: 'Vous avez terminé toutes les cartes en attente.',
      back: 'Retour',
      cardsToReview: 'cartes à réviser',
      totalCards: 'cartes au total',
      level: 'Niveau',
      delete: 'Supprimer',
    },
    pt: {
      title: 'Flashcards',
      subtitle: 'Estude termos bíblicos com repetição espaçada',
      startStudy: 'Começar a Estudar',
      allCards: 'Todos os Cartões',
      dueForReview: 'Para Revisar',
      mastered: 'Dominados',
      noCards: 'Sem flashcards',
      noCardsDesc: 'Adicione termos do dicionário para começar a estudar',
      goToDictionary: 'Ir ao Dicionário',
      tapToFlip: 'Toque para virar',
      howWellDidYouKnow: 'Quão bem você conhecia este termo?',
      again: 'De Novo',
      hard: 'Difícil',
      good: 'Bom',
      easy: 'Fácil',
      perfect: 'Perfeito',
      studyComplete: 'Estudo Completo!',
      studyCompleteDesc: 'Você completou todos os cartões pendentes.',
      back: 'Voltar',
      cardsToReview: 'cartões para revisar',
      totalCards: 'cartões no total',
      level: 'Nível',
      delete: 'Excluir',
    },
  };
  const t = (key: string) => translations[currentLanguage]?.[key] || translations['en'][key] || key;

  useEffect(() => {
    loadData();
  }, [currentLanguage]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [allCards, due, statsData] = await Promise.all([
        api.getFlashcards(currentLanguage),
        api.getDueFlashcards(currentLanguage),
        api.getFlashcardStats(),
      ]);
      setFlashcards(allCards);
      setDueCards(due);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading flashcards:', error);
    } finally {
      setLoading(false);
    }
  };

  const startStudy = () => {
    if (dueCards.length === 0) return;
    setStudyMode(true);
    setCurrentCardIndex(0);
    setShowAnswer(false);
  };

  const flipCard = () => {
    setShowAnswer(!showAnswer);
    Animated.spring(flipAnim, {
      toValue: showAnswer ? 0 : 1,
      friction: 8,
      tension: 10,
      useNativeDriver: true,
    }).start();
  };

  const handleReview = async (quality: number) => {
    if (!dueCards[currentCardIndex]) return;
    
    setReviewLoading(true);
    try {
      await api.reviewFlashcard(dueCards[currentCardIndex].flashcard_id, quality);
      
      // Move to next card
      if (currentCardIndex < dueCards.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1);
        setShowAnswer(false);
        flipAnim.setValue(0);
      } else {
        // End of deck
        setStudyMode(false);
        loadData(); // Refresh stats
      }
    } catch (error) {
      console.error('Error reviewing flashcard:', error);
    } finally {
      setReviewLoading(false);
    }
  };

  const deleteFlashcard = async (flashcardId: string) => {
    if (typeof window !== 'undefined' && !window.confirm('Eliminare questa flashcard?')) {
      return;
    }
    try {
      await api.deleteFlashcard(flashcardId);
      loadData();
    } catch (error) {
      console.error('Error deleting flashcard:', error);
    }
  };

  const getMasteryColor = (level: number) => {
    const colors = ['#EF4444', '#F97316', '#EAB308', '#22C55E', '#10B981', '#059669'];
    return colors[level] || colors[0];
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Study Mode
  if (studyMode && dueCards.length > 0) {
    const currentCard = dueCards[currentCardIndex];
    
    if (!currentCard) {
      return (
        <SafeAreaView style={styles.container}>
          <View style={styles.completeContainer}>
            <Icon name="checkmark-circle" size={80} color={COLORS.success} />
            <Text style={styles.completeTitle}>{t('studyComplete')}</Text>
            <Text style={styles.completeDesc}>{t('studyCompleteDesc')}</Text>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={() => { setStudyMode(false); loadData(); }}
            >
              <Text style={styles.primaryButtonText}>{t('back')}</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      );
    }

    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.studyHeader}>
          <TouchableOpacity onPress={() => setStudyMode(false)}>
            <Icon name="close" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.studyProgress}>
            {currentCardIndex + 1} / {dueCards.length}
          </Text>
          <View style={{ width: 28 }} />
        </View>

        <View style={styles.cardContainer}>
          <TouchableOpacity 
            style={styles.flashcard} 
            onPress={flipCard}
            activeOpacity={0.9}
          >
            {!showAnswer ? (
              <View style={styles.cardFront}>
                <Text style={styles.cardTerm}>{currentCard.term}</Text>
                <View style={styles.cardOriginBadge}>
                  <Text style={styles.cardOriginText}>{currentCard.origin}</Text>
                </View>
                <Text style={styles.tapHint}>{t('tapToFlip')}</Text>
              </View>
            ) : (
              <View style={styles.cardBack}>
                <Text style={styles.cardMeaning}>{currentCard.meaning}</Text>
                {currentCard.description && (
                  <Text style={styles.cardDescription}>{currentCard.description}</Text>
                )}
              </View>
            )}
          </TouchableOpacity>
        </View>

        {showAnswer && (
          <View style={styles.reviewButtons}>
            <Text style={styles.reviewQuestion}>{t('howWellDidYouKnow')}</Text>
            <View style={styles.qualityButtons}>
              <TouchableOpacity 
                style={[styles.qualityButton, { backgroundColor: '#EF4444' }]}
                onPress={() => handleReview(0)}
                disabled={reviewLoading}
              >
                <Text style={styles.qualityButtonText}>{t('again')}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.qualityButton, { backgroundColor: '#F97316' }]}
                onPress={() => handleReview(2)}
                disabled={reviewLoading}
              >
                <Text style={styles.qualityButtonText}>{t('hard')}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.qualityButton, { backgroundColor: '#22C55E' }]}
                onPress={() => handleReview(3)}
                disabled={reviewLoading}
              >
                <Text style={styles.qualityButtonText}>{t('good')}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.qualityButton, { backgroundColor: '#10B981' }]}
                onPress={() => handleReview(4)}
                disabled={reviewLoading}
              >
                <Text style={styles.qualityButtonText}>{t('easy')}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.qualityButton, { backgroundColor: '#059669' }]}
                onPress={() => handleReview(5)}
                disabled={reviewLoading}
              >
                <Text style={styles.qualityButtonText}>{t('perfect')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </SafeAreaView>
    );
  }

  // Main View
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Icon name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('title')}</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.subtitle}>{t('subtitle')}</Text>

        {/* Stats Cards */}
        {stats && (
          <View style={styles.statsRow}>
            <View style={[styles.statCard, { backgroundColor: COLORS.primary + '15' }]}>
              <Icon name="layers" size={24} color={COLORS.primary} />
              <Text style={styles.statNumber}>{stats.total_flashcards}</Text>
              <Text style={styles.statLabel}>{t('totalCards')}</Text>
            </View>
            <View style={[styles.statCard, { backgroundColor: '#F97316' + '15' }]}>
              <Icon name="time" size={24} color="#F97316" />
              <Text style={styles.statNumber}>{stats.due_for_review}</Text>
              <Text style={styles.statLabel}>{t('cardsToReview')}</Text>
            </View>
            <View style={[styles.statCard, { backgroundColor: '#22C55E' + '15' }]}>
              <Icon name="checkmark-circle" size={24} color="#22C55E" />
              <Text style={styles.statNumber}>{stats.mastered}</Text>
              <Text style={styles.statLabel}>{t('mastered')}</Text>
            </View>
          </View>
        )}

        {/* Start Study Button */}
        {dueCards.length > 0 && (
          <TouchableOpacity style={styles.studyButton} onPress={startStudy}>
            <Icon name="play" size={24} color="#fff" />
            <Text style={styles.studyButtonText}>
              {t('startStudy')} ({dueCards.length} {t('dueForReview').toLowerCase()})
            </Text>
          </TouchableOpacity>
        )}

        {/* Empty State */}
        {flashcards.length === 0 && (
          <View style={styles.emptyState}>
            <Icon name="card-outline" size={64} color={COLORS.textMuted} />
            <Text style={styles.emptyTitle}>{t('noCards')}</Text>
            <Text style={styles.emptyDesc}>{t('noCardsDesc')}</Text>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={() => router.push('/dictionary')}
            >
              <Icon name="book" size={20} color="#fff" />
              <Text style={styles.primaryButtonText}>{t('goToDictionary')}</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Flashcards List */}
        {flashcards.length > 0 && (
          <View style={styles.cardsSection}>
            <Text style={styles.sectionTitle}>{t('allCards')}</Text>
            {flashcards.map((card) => (
              <View key={card.flashcard_id} style={styles.cardItem}>
                <View style={styles.cardItemContent}>
                  <Text style={styles.cardItemTerm}>{card.term}</Text>
                  <Text style={styles.cardItemMeaning} numberOfLines={1}>{card.meaning}</Text>
                  <View style={styles.cardItemMeta}>
                    <View style={[styles.masteryBadge, { backgroundColor: getMasteryColor(card.mastery_level) }]}>
                      <Text style={styles.masteryText}>{t('level')} {card.mastery_level}</Text>
                    </View>
                    <Text style={styles.cardItemOrigin}>{card.origin}</Text>
                  </View>
                </View>
                <TouchableOpacity 
                  onPress={() => deleteFlashcard(card.flashcard_id)}
                  style={styles.deleteButton}
                >
                  <Icon name="trash-outline" size={20} color={COLORS.error} />
                </TouchableOpacity>
              </View>
            ))}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  content: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  statsRow: {
    flexDirection: 'row',
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.xs,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: 2,
  },
  studyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.lg,
  },
  studyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.md,
  },
  emptyDesc: {
    fontSize: 14,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  cardsSection: {
    marginTop: SPACING.md,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  cardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  cardItemContent: {
    flex: 1,
  },
  cardItemTerm: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  cardItemMeaning: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  cardItemMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginTop: SPACING.xs,
  },
  masteryBadge: {
    paddingVertical: 2,
    paddingHorizontal: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
  },
  masteryText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
  },
  cardItemOrigin: {
    fontSize: 11,
    color: COLORS.textMuted,
  },
  deleteButton: {
    padding: SPACING.sm,
  },
  // Study mode styles
  studyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
  },
  studyProgress: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.lg,
  },
  flashcard: {
    width: '100%',
    aspectRatio: 3/4,
    maxHeight: 400,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.xl,
    ...SHADOWS.medium,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  cardFront: {
    alignItems: 'center',
  },
  cardBack: {
    alignItems: 'center',
  },
  cardTerm: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  cardOriginBadge: {
    backgroundColor: COLORS.primary + '20',
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.full,
  },
  cardOriginText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  tapHint: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: SPACING.xl,
  },
  cardMeaning: {
    fontSize: 22,
    fontWeight: '600',
    color: COLORS.primary,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  cardDescription: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 22,
  },
  reviewButtons: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xl,
  },
  reviewQuestion: {
    fontSize: 14,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  qualityButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    justifyContent: 'center',
  },
  qualityButton: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    minWidth: 60,
    alignItems: 'center',
  },
  qualityButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#fff',
  },
  completeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  completeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.lg,
  },
  completeDesc: {
    fontSize: 14,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: SPACING.sm,
    marginBottom: SPACING.xl,
  },
});
