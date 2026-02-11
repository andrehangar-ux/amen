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
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface QuizTopic {
  id: string;
  title: string;
  description: string;
  questions_count: number;
}

interface Question {
  id: string;
  question: string;
  options: string[];
  correct: number;
  explanation: string;
  verse_ref: string;
}

interface QuizResult {
  score: number;
  correct_count: number;
  total: number;
  results: any[];
  feedback: string;
}

export default function QuizScreen() {
  const [topics, setTopics] = useState<QuizTopic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      const data = await api.getQuizTopics();
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
      const quiz = await api.getQuiz(topicId);
      setSelectedTopic(topicId);
      setQuestions(quiz.questions);
      setCurrentQuestion(0);
      setAnswers({});
      setResult(null);
    } catch (error) {
      Alert.alert('Errore', 'Impossibile caricare il quiz');
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
      Alert.alert('Errore', 'Impossibile inviare il quiz');
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
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Show result
  if (result) {
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
              {result.correct_count} su {result.total} risposte corrette
            </Text>
            <View style={styles.feedbackCard}>
              <Text style={styles.feedbackText}>{result.feedback}</Text>
            </View>
            
            <TouchableOpacity style={styles.primaryButton} onPress={resetQuiz}>
              <Text style={styles.primaryButtonText}>Torna ai Quiz</Text>
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
                <Text style={styles.submitButtonText}>Invia Quiz</Text>
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

  // Show topics
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Quiz Biblici</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.subtitle}>Testa la tua conoscenza della Bibbia</Text>

        {topics.map(topic => (
          <TouchableOpacity
            key={topic.id}
            style={styles.topicCard}
            onPress={() => startQuiz(topic.id)}
          >
            <View style={styles.topicIcon}>
              <Ionicons name="help-circle" size={30} color={COLORS.primary} />
            </View>
            <View style={styles.topicContent}>
              <Text style={styles.topicTitle}>{topic.title}</Text>
              <Text style={styles.topicDescription}>{topic.description}</Text>
              <Text style={styles.topicMeta}>{topic.questions_count} domande</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.textMuted} />
          </TouchableOpacity>
        ))}
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
});
