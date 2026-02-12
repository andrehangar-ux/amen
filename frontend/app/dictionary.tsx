import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface DictionaryTerm {
  id: string;
  term: string;
  origin: string;
  meaning: string;
}

interface FullTerm {
  term: string;
  transliteration: string;
  origin: string;
  pronunciation: string;
  meaning: string;
  root: string;
  hebrew_equivalent?: string;
  greek_equivalent?: string;
  description: string;
  verses: Array<{ ref: string; text: string }>;
  image_url?: string;
}

export default function DictionaryScreen() {
  const { currentLanguage } = useLanguageStore();
  const [terms, setTerms] = useState<DictionaryTerm[]>([]);
  const [selectedTerm, setSelectedTerm] = useState<FullTerm | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingTerm, setLoadingTerm] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [askingAi, setAskingAi] = useState(false);

  const translations: Record<string, Record<string, string>> = {
    it: { title: 'Dizionario Biblico', subtitle: 'Esplora i termini originali ebraici e greci della Bibbia', search: 'Cerca termine...', transliteration: 'Traslitterazione', pronunciation: 'Pronuncia', meaning: 'Significato', root: 'Radice', equivalents: 'Equivalenti', description: 'Descrizione', verses: 'Versetti di Riferimento', askAi: 'Chiedi all\'AI', askPlaceholder: 'Fai una domanda su questo termine...', ask: 'Chiedi' },
    en: { title: 'Biblical Dictionary', subtitle: 'Explore the original Hebrew and Greek terms of the Bible', search: 'Search term...', transliteration: 'Transliteration', pronunciation: 'Pronunciation', meaning: 'Meaning', root: 'Root', equivalents: 'Equivalents', description: 'Description', verses: 'Reference Verses', askAi: 'Ask AI', askPlaceholder: 'Ask a question about this term...', ask: 'Ask' },
    es: { title: 'Diccionario Bíblico', subtitle: 'Explora los términos originales hebreos y griegos de la Biblia', search: 'Buscar término...', transliteration: 'Transliteración', pronunciation: 'Pronunciación', meaning: 'Significado', root: 'Raíz', equivalents: 'Equivalentes', description: 'Descripción', verses: 'Versículos de Referencia', askAi: 'Preguntar a la IA', askPlaceholder: 'Haz una pregunta sobre este término...', ask: 'Preguntar' },
    de: { title: 'Biblisches Wörterbuch', subtitle: 'Erkunde die ursprünglichen hebräischen und griechischen Begriffe der Bibel', search: 'Begriff suchen...', transliteration: 'Transliteration', pronunciation: 'Aussprache', meaning: 'Bedeutung', root: 'Wurzel', equivalents: 'Äquivalente', description: 'Beschreibung', verses: 'Referenzverse', askAi: 'KI fragen', askPlaceholder: 'Stelle eine Frage zu diesem Begriff...', ask: 'Fragen' },
    fr: { title: 'Dictionnaire Biblique', subtitle: 'Explorez les termes hébreux et grecs originaux de la Bible', search: 'Rechercher un terme...', transliteration: 'Translittération', pronunciation: 'Prononciation', meaning: 'Signification', root: 'Racine', equivalents: 'Équivalents', description: 'Description', verses: 'Versets de Référence', askAi: 'Demander à l\'IA', askPlaceholder: 'Posez une question sur ce terme...', ask: 'Demander' },
    pt: { title: 'Dicionário Bíblico', subtitle: 'Explore os termos originais hebraicos e gregos da Bíblia', search: 'Buscar termo...', transliteration: 'Transliteração', pronunciation: 'Pronúncia', meaning: 'Significado', root: 'Raiz', equivalents: 'Equivalentes', description: 'Descrição', verses: 'Versículos de Referência', askAi: 'Perguntar à IA', askPlaceholder: 'Faça uma pergunta sobre este termo...', ask: 'Perguntar' },
  };
  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  useEffect(() => {
    loadTerms();
  }, [currentLanguage]);

  const loadTerms = async () => {
    try {
      const data = await api.getDictionaryTerms(currentLanguage);
      setTerms(data);
    } catch (error) {
      console.error('Error loading dictionary:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTerm = async (termId: string) => {
    setLoadingTerm(true);
    setAiAnswer('');
    try {
      const data = await api.getDictionaryTerm(termId, currentLanguage);
      setSelectedTerm(data);
    } catch (error) {
      console.error('Error loading term:', error);
    } finally {
      setLoadingTerm(false);
    }
  };

  const askAI = async () => {
    if (!aiQuestion.trim() || !selectedTerm) return;
    
    setAskingAi(true);
    try {
      const result = await api.aiDictionaryStudy(
        terms.find(t => t.term === selectedTerm.term)?.id || '',
        aiQuestion
      );
      setAiAnswer(result.answer);
    } catch (error) {
      console.error('Error asking AI:', error);
    } finally {
      setAskingAi(false);
    }
  };

  const filteredTerms = searchQuery
    ? terms.filter(t => 
        t.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.meaning.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : terms;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Term Detail View
  if (selectedTerm) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => setSelectedTerm(null)}>
            <Ionicons name="arrow-back" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title}>{t('title')}</Text>
          <View style={{ width: 28 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          {loadingTerm ? (
            <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: SPACING.xl }} />
          ) : (
            <>
              <View style={styles.termHeader}>
                <Text style={styles.termTitle}>{selectedTerm.term}</Text>
                <View style={styles.termBadge}>
                  <Text style={styles.termBadgeText}>{selectedTerm.origin}</Text>
                </View>
              </View>

              {selectedTerm.image_url && (
                <Image source={{ uri: selectedTerm.image_url }} style={styles.termImage} />
              )}

              <View style={styles.infoCard}>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>{t('transliteration')}</Text>
                  <Text style={styles.infoValue}>{selectedTerm.transliteration}</Text>
                </View>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>{t('pronunciation')}</Text>
                  <Text style={styles.infoValue}>{selectedTerm.pronunciation}</Text>
                </View>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>{t('meaning')}</Text>
                  <Text style={styles.infoValue}>{selectedTerm.meaning}</Text>
                </View>
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>{t('root')}</Text>
                <Text style={styles.sectionText}>{selectedTerm.root}</Text>
              </View>

              {(selectedTerm.hebrew_equivalent || selectedTerm.greek_equivalent) && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Equivalenti</Text>
                  {selectedTerm.hebrew_equivalent && (
                    <Text style={styles.sectionText}>📜 Ebraico: {selectedTerm.hebrew_equivalent}</Text>
                  )}
                  {selectedTerm.greek_equivalent && (
                    <Text style={styles.sectionText}>🏛️ Greco: {selectedTerm.greek_equivalent}</Text>
                  )}
                </View>
              )}

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Descrizione</Text>
                <Text style={styles.descriptionText}>{selectedTerm.description}</Text>
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Versetti di Riferimento</Text>
                {selectedTerm.verses.map((verse, index) => (
                  <View key={index} style={styles.verseCard}>
                    <Text style={styles.verseRef}>{verse.ref}</Text>
                    <Text style={styles.verseText}>{verse.text}</Text>
                  </View>
                ))}
              </View>

              <View style={styles.aiSection}>
                <Text style={styles.sectionTitle}>🤖 Chiedi all'AI</Text>
                <TextInput
                  style={styles.aiInput}
                  placeholder="Fai una domanda su questo termine..."
                  placeholderTextColor={COLORS.textMuted}
                  value={aiQuestion}
                  onChangeText={setAiQuestion}
                />
                <TouchableOpacity
                  style={[styles.aiButton, (askingAi || !aiQuestion.trim()) && styles.aiButtonDisabled]}
                  onPress={askAI}
                  disabled={askingAi || !aiQuestion.trim()}
                >
                  {askingAi ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={styles.aiButtonText}>Chiedi</Text>
                  )}
                </TouchableOpacity>

                {aiAnswer ? (
                  <View style={styles.aiAnswerCard}>
                    <Text style={styles.aiAnswerText}>{aiAnswer}</Text>
                  </View>
                ) : null}
              </View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Terms List View
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Dizionario Biblico</Text>
        <View style={{ width: 28 }} />
      </View>

      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={COLORS.textMuted} />
        <TextInput
          style={styles.searchInput}
          placeholder="Cerca termine..."
          placeholderTextColor={COLORS.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery ? (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>
        ) : null}
      </View>

      <ScrollView contentContainerStyle={styles.termsContainer}>
        <Text style={styles.subtitle}>
          Esplora i termini originali ebraici e greci della Bibbia
        </Text>

        {filteredTerms.map((term) => (
          <TouchableOpacity
            key={term.id}
            style={styles.termCard}
            onPress={() => loadTerm(term.id)}
          >
            <View style={styles.termCardIcon}>
              <Text style={styles.termCardLetter}>
                {term.origin === 'Ebraico' ? 'א' : 'α'}
              </Text>
            </View>
            <View style={styles.termCardContent}>
              <Text style={styles.termCardTitle}>{term.term}</Text>
              <Text style={styles.termCardMeaning} numberOfLines={1}>{term.meaning}</Text>
              <Text style={styles.termCardOrigin}>{term.origin}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    margin: SPACING.md,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
    paddingVertical: SPACING.md,
    marginLeft: SPACING.sm,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  termsContainer: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  termCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  termCardIcon: {
    width: 50,
    height: 50,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  termCardLetter: {
    fontSize: 24,
    fontWeight: '600',
    color: COLORS.primary,
  },
  termCardContent: {
    flex: 1,
  },
  termCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  termCardMeaning: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  termCardOrigin: {
    fontSize: 11,
    color: COLORS.primary,
    marginTop: 4,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  termHeader: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  termTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
  },
  termBadge: {
    backgroundColor: COLORS.primary + '20',
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.full,
    marginTop: SPACING.sm,
  },
  termBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  termImage: {
    width: '100%',
    height: 180,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.lg,
  },
  infoCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.small,
  },
  infoRow: {
    flexDirection: 'row',
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  infoLabel: {
    width: 120,
    fontSize: 13,
    color: COLORS.textMuted,
  },
  infoValue: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    fontWeight: '500',
  },
  section: {
    marginTop: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  sectionText: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 22,
  },
  descriptionText: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 24,
  },
  verseCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  verseRef: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  verseText: {
    fontSize: 14,
    color: COLORS.text,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  aiSection: {
    marginTop: SPACING.xl,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.small,
  },
  aiInput: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 15,
    color: COLORS.text,
    marginTop: SPACING.sm,
  },
  aiButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.sm,
    alignItems: 'center',
    marginTop: SPACING.sm,
  },
  aiButtonDisabled: {
    opacity: 0.5,
  },
  aiButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  aiAnswerCard: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.md,
  },
  aiAnswerText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
  },
});
