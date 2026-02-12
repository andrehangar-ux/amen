import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Speech from 'expo-speech';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

// Cross-platform TTS helpers
const speakTextWithCallback = (text: string, langCode: string, onStart: () => void, onEnd: () => void) => {
  onStart();
  if (Platform.OS === 'web' && typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode;
    utterance.rate = 0.9;
    utterance.onend = onEnd;
    utterance.onerror = onEnd;
    window.speechSynthesis.speak(utterance);
  } else {
    Speech.speak(text, {
      language: langCode,
      onDone: onEnd,
      onStopped: onEnd,
    });
  }
};

const stopSpeakingHelper = () => {
  if (Platform.OS === 'web' && typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  } else {
    Speech.stop();
  }
};

export default function FeelingsScreen() {
  const { currentLanguage, languages } = useLanguageStore();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await api.getFeelingsHistory();
      setHistory(data);
    } catch (error) {
      console.log('Error loading history:', error);
    }
  };

  const handleSubmit = async () => {
    if (!text.trim()) return;

    setLoading(true);
    setResponse(null);

    try {
      const result = await api.analyzeFeeling(text, currentLanguage);
      setResponse(result.response);
      setText('');
      loadHistory();
    } catch (error: any) {
      setResponse('Mi dispiace, si \u00e8 verificato un errore. Riprova.');
    } finally {
      setLoading(false);
    }
  };

  const handleSpeak = () => {
    if (!response) return;
    
    if (isSpeaking) {
      Speech.stop();
      setIsSpeaking(false);
    } else {
      const ttsCode = languages[currentLanguage]?.tts_code || 'it-IT';
      Speech.speak(response, {
        language: ttsCode,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
      });
      setIsSpeaking(true);
    }
  };

  const PROMPTS = [
    "Mi sento solo e triste oggi...",
    "Ho paura del futuro...",
    "Sono arrabbiato con qualcuno...",
    "Mi sento grato per...",
    "Sto attraversando un momento difficile...",
    "Ho bisogno di forza e coraggio...",
  ];

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Come Ti Senti?</Text>
          <Text style={styles.headerSubtitle}>Condividi il tuo cuore con Dio</Text>
        </View>
        <TouchableOpacity
          style={styles.historyButton}
          onPress={() => setShowHistory(!showHistory)}
        >
          <Ionicons name="time-outline" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {showHistory ? (
          <ScrollView style={styles.historyContainer}>
            <Text style={styles.sectionTitle}>Le Tue Riflessioni Passate</Text>
            {history.map((item, index) => (
              <View key={index} style={styles.historyItem}>
                <Text style={styles.historyText} numberOfLines={2}>{item.text}</Text>
                <Text style={styles.historyDate}>
                  {new Date(item.created_at).toLocaleDateString('it-IT')}
                </Text>
              </View>
            ))}
          </ScrollView>
        ) : (
          <ScrollView contentContainerStyle={styles.scrollContent}>
            {/* Input Section */}
            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>
                Scrivi liberamente come ti senti. Riceverai versetti biblici e guida spirituale personalizzata.
              </Text>
              <TextInput
                style={styles.textInput}
                placeholder="Scrivi qui i tuoi pensieri, le tue emozioni, le tue preoccupazioni..."
                placeholderTextColor={COLORS.textMuted}
                value={text}
                onChangeText={setText}
                multiline
                numberOfLines={6}
                textAlignVertical="top"
              />

              <TouchableOpacity
                style={[styles.submitButton, loading && styles.submitButtonDisabled]}
                onPress={handleSubmit}
                disabled={loading || !text.trim()}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <>
                    <Ionicons name="heart" size={20} color="#fff" />
                    <Text style={styles.submitButtonText}>Ricevi Guida Spirituale</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>

            {/* Quick Prompts */}
            {!response && (
              <View style={styles.promptsSection}>
                <Text style={styles.sectionTitle}>Suggerimenti</Text>
                <View style={styles.prompts}>
                  {PROMPTS.map((prompt, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.promptButton}
                      onPress={() => setText(prompt)}
                    >
                      <Text style={styles.promptText}>{prompt}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}

            {/* Response */}
            {response && (
              <View style={styles.responseSection}>
                <View style={styles.responseHeader}>
                  <View style={styles.responseIcon}>
                    <Ionicons name="book" size={24} color={COLORS.primary} />
                  </View>
                  <Text style={styles.responseTitle}>La Parola per Te</Text>
                  <TouchableOpacity onPress={handleSpeak}>
                    <Ionicons
                      name={isSpeaking ? 'stop' : 'volume-high'}
                      size={24}
                      color={COLORS.primary}
                    />
                  </TouchableOpacity>
                </View>
                <Text style={styles.responseText}>{response}</Text>
              </View>
            )}
          </ScrollView>
        )}
      </KeyboardAvoidingView>
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
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  backButton: {
    padding: SPACING.sm,
  },
  headerContent: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  headerSubtitle: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  historyButton: {
    padding: SPACING.sm,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  inputSection: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    ...SHADOWS.small,
  },
  inputLabel: {
    fontSize: 14,
    color: COLORS.textLight,
    marginBottom: SPACING.md,
    lineHeight: 22,
  },
  textInput: {
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
    minHeight: 150,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  submitButton: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SPACING.md,
    gap: SPACING.sm,
  },
  submitButtonDisabled: {
    opacity: 0.7,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  promptsSection: {
    marginTop: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  prompts: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  promptButton: {
    backgroundColor: COLORS.card,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  promptText: {
    fontSize: 13,
    color: COLORS.textLight,
  },
  responseSection: {
    marginTop: SPACING.lg,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    ...SHADOWS.medium,
  },
  responseHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
    gap: SPACING.sm,
  },
  responseIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  responseTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.primary,
  },
  responseText: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 26,
  },
  historyContainer: {
    padding: SPACING.md,
  },
  historyItem: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
  },
  historyText: {
    fontSize: 14,
    color: COLORS.text,
  },
  historyDate: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
});
