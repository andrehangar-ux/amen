import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface QuizTopic {
  id: string;
  title: string;
  description: string;
  questions_count: number;
  difficulty?: string;
}

interface Question {
  id: string;
  question: string;
  options: string[];
  correct: number;
  explanation: string;
  verse_ref: string;
}

interface QuestionResult {
  question_id: string;
  is_correct: boolean;
  correct_answer: number;
  user_answer: number;
  explanation: string;
  verse_ref: string;
}

interface QuizResult {
  score: number;
  correct_count: number;
  total: number;
  results: QuestionResult[];
  feedback: string;
}

export default function QuizScreen() {
  const { currentLanguage } = useLanguageStore();
  const [topics, setTopics] = useState<QuizTopic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showCorrections, setShowCorrections] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<'base' | 'avanzato'>('base');

  // Translations for UI
  const translations: Record<string, Record<string, string>> = {
    it: { title: 'Quiz Biblici', subtitle: 'Testa la tua conoscenza della Bibbia', questions: 'domande', back: 'Torna ai Quiz', submit: 'Invia Quiz', showErrors: 'Mostra Correzioni', hideErrors: 'Nascondi Correzioni', correct: 'Corretta', wrong: 'Sbagliata', yourAnswer: 'Tua risposta', correctAnswer: 'Risposta corretta', explanation: 'Spiegazione', verse: 'Versetto', base: 'Quiz Base', advanced: 'Studio Avanzato', error: 'Errore', loadError: 'Impossibile caricare il quiz', noQuizzes: 'Nessun quiz disponibile', advancedComingSoon: 'Quiz avanzati disponibili prossimamente', noAnswer: '(nessuna)' },
    es: { title: 'Cuestionarios Bíblicos', subtitle: 'Pon a prueba tu conocimiento de la Biblia', questions: 'preguntas', back: 'Volver', submit: 'Enviar', showErrors: 'Ver Correcciones', hideErrors: 'Ocultar', correct: 'Correcta', wrong: 'Incorrecta', yourAnswer: 'Tu respuesta', correctAnswer: 'Respuesta correcta', explanation: 'Explicación', verse: 'Versículo', base: 'Quiz Base', advanced: 'Estudio Avanzado', error: 'Error', loadError: 'No se puede cargar el quiz', noQuizzes: 'No hay quiz disponibles', advancedComingSoon: 'Quiz avanzados próximamente', noAnswer: '(ninguna)' },
    en: { title: 'Bible Quizzes', subtitle: 'Test your knowledge of the Bible', questions: 'questions', back: 'Back to Quizzes', submit: 'Submit', showErrors: 'Show Corrections', hideErrors: 'Hide Corrections', correct: 'Correct', wrong: 'Wrong', yourAnswer: 'Your answer', correctAnswer: 'Correct answer', explanation: 'Explanation', verse: 'Verse', base: 'Base Quiz', advanced: 'Advanced Study', error: 'Error', loadError: 'Unable to load quiz', noQuizzes: 'No quizzes available', advancedComingSoon: 'Advanced quizzes coming soon', noAnswer: '(none)' },
    de: { title: 'Bibel-Quiz', subtitle: 'Teste dein Bibelwissen', questions: 'Fragen', back: 'Zurück', submit: 'Absenden', showErrors: 'Korrekturen anzeigen', hideErrors: 'Ausblenden', correct: 'Richtig', wrong: 'Falsch', yourAnswer: 'Deine Antwort', correctAnswer: 'Richtige Antwort', explanation: 'Erklärung', verse: 'Vers', base: 'Basis Quiz', advanced: 'Fortgeschrittenes Studium', error: 'Fehler', loadError: 'Quiz konnte nicht geladen werden', noQuizzes: 'Keine Quiz verfügbar', advancedComingSoon: 'Erweiterte Quiz bald verfügbar', noAnswer: '(keine)' },
    fr: { title: 'Quiz Bibliques', subtitle: 'Testez vos connaissances de la Bible', questions: 'questions', back: 'Retour', submit: 'Soumettre', showErrors: 'Voir Corrections', hideErrors: 'Masquer', correct: 'Correct', wrong: 'Incorrect', yourAnswer: 'Votre réponse', correctAnswer: 'Bonne réponse', explanation: 'Explication', verse: 'Verset', base: 'Quiz de Base', advanced: 'Étude Avancée', error: 'Erreur', loadError: 'Impossible de charger le quiz', noQuizzes: 'Aucun quiz disponible', advancedComingSoon: 'Quiz avancés bientôt disponibles', noAnswer: '(aucune)' },
    pt: { title: 'Quiz Bíblicos', subtitle: 'Teste seu conhecimento da Bíblia', questions: 'perguntas', back: 'Voltar', submit: 'Enviar', showErrors: 'Ver Correções', hideErrors: 'Ocultar', correct: 'Correta', wrong: 'Errada', yourAnswer: 'Sua resposta', correctAnswer: 'Resposta correta', explanation: 'Explicação', verse: 'Versículo', base: 'Quiz Base', advanced: 'Estudo Avançado', error: 'Erro', loadError: 'Não foi possível carregar o quiz', noQuizzes: 'Nenhum quiz disponível', advancedComingSoon: 'Quiz avançados em breve', noAnswer: '(nenhuma)' },
  };
  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  useEffect(() => {
    loadTopics();
  }, [currentLanguage]);

  const loadTopics = async () => {
    try {
      const data = await api.getQuizTopics(currentLanguage);
      setTopics(data);
    } catch (error) {
      console.error('Error loading topics:', error);
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = async (topicId: string) => {
    setLoading(true);
    try {
      const quiz = await api.getQuiz(topicId, currentLanguage);
      setSelectedTopic(topicId);
      setQuestions(quiz.questions);
      setCurrentQuestion(0);
      setAnswers({});
      setResult(null);
      setShowCorrections(false);
    } catch (error) {
      Alert.alert(t('error'), t('loadError'));
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (questionId: string, optionIndex: number) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionIndex }));
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  const submitQuiz = async () => {
    if (!selectedTopic) return;
    setSubmitting(true);
    try {
      const data = await api.submitQuiz(selectedTopic, answers);
      setResult(data);
    } catch (error) {
      Alert.alert(t('error'), t('submitError'));
    } finally {
      setSubmitting(false);
    }
  };

  const resetQuiz = () => {
    setSelectedTopic(null);
    setQuestions([]);
    setCurrentQuestion(0);
    setAnswers({});
    setResult(null);
    setShowCorrections(false);
  };

  // Filter topics by category (base vs advanced)
  const baseTopics = topics.filter(t => t.id !== 'studio_avanzato');
  const advancedTopics = topics.filter(t => t.id === 'studio_avanzato');
  const filteredTopics = selectedCategory === 'base' ? baseTopics : advancedTopics;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Show result with detailed corrections
  if (result) {
    const wrongAnswers = result.results.filter(r => !r.is_correct);
    
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.resultContainer}>
            <View style={styles.resultIcon}>
              <Ionicons
                name={result.score >= 70 ? 'trophy' : result.score >= 50 ? 'ribbon' : 'refresh'}
                size={60}
                color={result.score >= 70 ? COLORS.accent : result.score >= 50 ? COLORS.primary : COLORS.textMuted}
              />
            </View>
            <Text style={styles.resultScore}>{result.score.toFixed(0)}%</Text>
            <Text style={styles.resultText}>
              {result.correct_count} / {result.total} {t('correct')}
            </Text>
            <View style={styles.feedbackCard}>
              <Text style={styles.feedbackText}>{result.feedback}</Text>
            </View>
            
            {/* Corrections Section */}
            {wrongAnswers.length > 0 && (
              <TouchableOpacity 
                style={styles.showCorrectionsBtn}
                onPress={() => setShowCorrections(!showCorrections)}
              >
                <Ionicons 
                  name={showCorrections ? "chevron-up" : "chevron-down"} 
                  size={20} 
                  color={COLORS.error} 
                />
                <Text style={styles.showCorrectionsBtnText}>
                  {showCorrections ? t('hideErrors') : `${t('showErrors')} (${wrongAnswers.length})`}
                </Text>
              </TouchableOpacity>
            )}
            
            {showCorrections && wrongAnswers.length > 0 && (
              <View style={styles.correctionsContainer}>
                {wrongAnswers.map((r, idx) => {
                  const question = questions.find(q => q.id === r.question_id);
                  if (!question) return null;
                  
                  return (
                    <View key={idx} style={styles.correctionCard}>
                      <Text style={styles.correctionQuestion}>
                        {idx + 1}. {question.question}
                      </Text>
                      
                      {/* User's wrong answer */}
                      <View style={styles.answerRow}>
                        <Ionicons name="close-circle" size={18} color={COLORS.error} />
                        <Text style={styles.wrongAnswerLabel}>{t('yourAnswer')}: </Text>
                        <Text style={styles.wrongAnswerText}>
                          {r.user_answer >= 0 ? question.options[r.user_answer] : t('noAnswer')}
                        </Text>
                      </View>
                      
                      {/* Correct answer */}
                      <View style={styles.answerRow}>
                        <Ionicons name="checkmark-circle" size={18} color={COLORS.success} />
                        <Text style={styles.correctAnswerLabel}>{t('correctAnswer')}: </Text>
                        <Text style={styles.correctAnswerText}>
                          {question.options[r.correct_answer]}
                        </Text>
                      </View>
                      
                      {/* Explanation */}
                      {r.explanation && (
                        <View style={styles.explanationBox}>
                          <Text style={styles.explanationLabel}>💡 {t('explanation')}:</Text>
                          <Text style={styles.explanationText}>{r.explanation}</Text>
                        </View>
                      )}
                      
                      {/* Verse reference */}
                      {r.verse_ref && (
                        <Text style={styles.verseRef}>📖 {r.verse_ref}</Text>
                      )}
                    </View>
                  );
                })}
              </View>
            )}
            
            <TouchableOpacity style={styles.primaryButton} onPress={resetQuiz}>
              <Text style={styles.primaryButtonText}>{t('back')}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Show quiz questions
  if (selectedTopic && questions.length > 0) {
    const question = questions[currentQuestion];
    const selectedAnswer = answers[question.id];

    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={resetQuiz}>
            <Ionicons name="close" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.progressText}>
            {currentQuestion + 1} / {questions.length}
          </Text>
        </View>

        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              { width: `${((currentQuestion + 1) / questions.length) * 100}%` },
            ]}
          />
        </View>

        <ScrollView contentContainerStyle={styles.questionContainer}>
          <Text style={styles.questionText}>{question.question}</Text>

          {question.options.map((option, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.optionCard,
                selectedAnswer === index && styles.optionSelected,
              ]}
              onPress={() => selectAnswer(question.id, index)}
            >
              <View style={[
                styles.optionIndicator,
                selectedAnswer === index && styles.optionIndicatorSelected,
              ]}>
                <Text style={[
                  styles.optionLetter,
                  selectedAnswer === index && styles.optionLetterSelected,
                ]}>
                  {String.fromCharCode(65 + index)}
                </Text>
              </View>
              <Text style={[
                styles.optionText,
                selectedAnswer === index && styles.optionTextSelected,
              ]}>
                {option}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.navigationButtons}>
          <TouchableOpacity
            style={[styles.navButton, currentQuestion === 0 && styles.navButtonDisabled]}
            onPress={prevQuestion}
            disabled={currentQuestion === 0}
          >
            <Ionicons name="chevron-back" size={24} color={currentQuestion === 0 ? COLORS.textMuted : COLORS.primary} />
          </TouchableOpacity>

          {currentQuestion === questions.length - 1 ? (
            <TouchableOpacity
              style={[styles.submitButton, submitting && styles.buttonDisabled]}
              onPress={submitQuiz}
              disabled={submitting || Object.keys(answers).length !== questions.length}
            >
              {submitting ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>{t('submit')}</Text>
              )}
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={styles.navButton}
              onPress={nextQuestion}
            >
              <Ionicons name="chevron-forward" size={24} color={COLORS.primary} />
            </TouchableOpacity>
          )}
        </View>
      </SafeAreaView>
    );
  }

  // Show topics with category selector
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('title')}</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.subtitle}>{t('subtitle')}</Text>

        {/* Category Selector */}
        <View style={styles.categorySelector}>
          <TouchableOpacity 
            style={[styles.categoryBtn, selectedCategory === 'base' && styles.categoryBtnActive]}
            onPress={() => setSelectedCategory('base')}
          >
            <Ionicons name="book" size={20} color={selectedCategory === 'base' ? '#fff' : COLORS.primary} />
            <Text style={[styles.categoryBtnText, selectedCategory === 'base' && styles.categoryBtnTextActive]}>
              {t('base')} ({baseTopics.length})
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.categoryBtn, selectedCategory === 'avanzato' && styles.categoryBtnActive]}
            onPress={() => setSelectedCategory('avanzato')}
          >
            <Ionicons name="school" size={20} color={selectedCategory === 'avanzato' ? '#fff' : COLORS.accent} />
            <Text style={[styles.categoryBtnText, selectedCategory === 'avanzato' && styles.categoryBtnTextActive]}>
              {t('advanced')} ({advancedTopics.length})
            </Text>
          </TouchableOpacity>
        </View>

        {filteredTopics.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="help-circle-outline" size={48} color={COLORS.textMuted} />
            <Text style={styles.emptyText}>
              {selectedCategory === 'avanzato' 
                ? t('advancedComingSoon')
                : t('noQuizzes')}
            </Text>
          </View>
        ) : (
          filteredTopics.map(topic => (
            <TouchableOpacity
              key={topic.id}
              style={styles.topicCard}
              onPress={() => startQuiz(topic.id)}
            >
              <View style={[
                styles.topicIcon,
                selectedCategory === 'avanzato' && { backgroundColor: COLORS.accent + '15' }
              ]}>
                <Ionicons 
                  name={selectedCategory === 'avanzato' ? "school" : "help-circle"} 
                  size={30} 
                  color={selectedCategory === 'avanzato' ? COLORS.accent : COLORS.primary} 
                />
              </View>
              <View style={styles.topicContent}>
                <Text style={styles.topicTitle}>{topic.title}</Text>
                <Text style={styles.topicDescription}>{topic.description}</Text>
                <Text style={styles.topicMeta}>{topic.questions_count} {t('questions')}</Text>
              </View>
              <Ionicons name="chevron-forward" size={24} color={COLORS.textMuted} />
            </TouchableOpacity>
          ))
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
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textLight,
    marginBottom: SPACING.lg,
    textAlign: 'center',
  },
  topicCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  topicIcon: {
    width: 56,
    height: 56,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  topicContent: {
    flex: 1,
  },
  topicTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
  },
  topicDescription: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 2,
  },
  topicMeta: {
    fontSize: 12,
    color: COLORS.primary,
    marginTop: 4,
  },
  progressBar: {
    height: 4,
    backgroundColor: COLORS.border,
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
  },
  progressText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  questionContainer: {
    padding: SPACING.lg,
    paddingBottom: 100,
  },
  questionText: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xl,
    lineHeight: 28,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 2,
    borderColor: COLORS.border,
  },
  optionSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  optionIndicator: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  optionIndicatorSelected: {
    backgroundColor: COLORS.primary,
  },
  optionLetter: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textMuted,
  },
  optionLetterSelected: {
    color: '#fff',
  },
  optionText: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  optionTextSelected: {
    color: COLORS.primary,
    fontWeight: '500',
  },
  navigationButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  navButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  navButtonDisabled: {
    opacity: 0.5,
  },
  submitButton: {
    flex: 1,
    marginLeft: SPACING.md,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  resultContainer: {
    alignItems: 'center',
    paddingTop: SPACING.xl,
  },
  resultIcon: {
    marginBottom: SPACING.lg,
  },
  resultScore: {
    fontSize: 56,
    fontWeight: '700',
    color: COLORS.primary,
  },
  resultText: {
    fontSize: 18,
    color: COLORS.textLight,
    marginTop: SPACING.sm,
  },
  feedbackCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginTop: SPACING.xl,
    marginHorizontal: SPACING.md,
    ...SHADOWS.small,
  },
  feedbackText: {
    fontSize: 16,
    color: COLORS.text,
    lineHeight: 24,
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xl,
    marginTop: SPACING.xl,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Category Selector Styles
  categorySelector: {
    flexDirection: 'row',
    marginBottom: SPACING.lg,
    gap: SPACING.sm,
  },
  categoryBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 2,
    borderColor: COLORS.border,
    gap: SPACING.xs,
  },
  categoryBtnActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  categoryBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.text,
  },
  categoryBtnTextActive: {
    color: '#fff',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textMuted,
    marginTop: SPACING.md,
    textAlign: 'center',
  },
  // Corrections Styles
  showCorrectionsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.md,
    marginTop: SPACING.lg,
    gap: SPACING.xs,
  },
  showCorrectionsBtnText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.error,
  },
  correctionsContainer: {
    marginTop: SPACING.md,
    width: '100%',
  },
  correctionCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.error,
  },
  correctionQuestion: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
    lineHeight: 22,
  },
  answerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
    flexWrap: 'wrap',
  },
  wrongAnswerLabel: {
    fontSize: 13,
    color: COLORS.error,
    fontWeight: '600',
    marginLeft: SPACING.xs,
  },
  wrongAnswerText: {
    fontSize: 13,
    color: COLORS.error,
    flex: 1,
  },
  correctAnswerLabel: {
    fontSize: 13,
    color: COLORS.success,
    fontWeight: '600',
    marginLeft: SPACING.xs,
  },
  correctAnswerText: {
    fontSize: 13,
    color: COLORS.success,
    flex: 1,
  },
  explanationBox: {
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.sm,
    marginTop: SPACING.sm,
  },
  explanationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 4,
  },
  explanationText: {
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 20,
  },
  verseRef: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: SPACING.sm,
    fontStyle: 'italic',
  },
  success: {
    color: '#27AE60',
  },
});
