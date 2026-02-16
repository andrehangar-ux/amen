import React, { useState, useEffect, useCallback } from 'react';
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
import { Icon } from '../src/components/Icon';
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
  const [selectedTermId, setSelectedTermId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingTerm, setLoadingTerm] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [askingAi, setAskingAi] = useState(false);
  const [aiSearching, setAiSearching] = useState(false);
  const [aiSearchResult, setAiSearchResult] = useState<any>(null);
  
  // Favorites and flashcards state
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [flashcardLoading, setFlashcardLoading] = useState(false);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());

  const translations: Record<string, Record<string, string>> = {
    it: { 
      title: 'Dizionario Biblico', 
      subtitle: 'Esplora i termini originali ebraici e greci della Bibbia', 
      search: 'Cerca termine...', 
      transliteration: 'Traslitterazione', 
      pronunciation: 'Pronuncia', 
      meaning: 'Significato', 
      root: 'Radice', 
      equivalents: 'Equivalenti', 
      description: 'Descrizione', 
      verses: 'Versetti di Riferimento', 
      askAi: 'Chiedi all\'AI', 
      askPlaceholder: 'Fai una domanda su questo termine...', 
      ask: 'Chiedi',
      addFavorite: 'Aggiungi ai Preferiti',
      removeFavorite: 'Rimuovi dai Preferiti',
      addFlashcard: 'Crea Flashcard',
      flashcardCreated: 'Flashcard creata!',
      favorites: 'Preferiti',
      all: 'Tutti',
      goToFlashcards: 'Studia Flashcards'
    },
    en: { 
      title: 'Biblical Dictionary', 
      subtitle: 'Explore the original Hebrew and Greek terms of the Bible', 
      search: 'Search term...', 
      transliteration: 'Transliteration', 
      pronunciation: 'Pronunciation', 
      meaning: 'Meaning', 
      root: 'Root', 
      equivalents: 'Equivalents', 
      description: 'Description', 
      verses: 'Reference Verses', 
      askAi: 'Ask AI', 
      askPlaceholder: 'Ask a question about this term...', 
      ask: 'Ask',
      addFavorite: 'Add to Favorites',
      removeFavorite: 'Remove from Favorites',
      addFlashcard: 'Create Flashcard',
      flashcardCreated: 'Flashcard created!',
      favorites: 'Favorites',
      all: 'All',
      goToFlashcards: 'Study Flashcards'
    },
    es: { 
      title: 'Diccionario Bíblico', 
      subtitle: 'Explora los términos originales hebreos y griegos de la Biblia', 
      search: 'Buscar término...', 
      transliteration: 'Transliteración', 
      pronunciation: 'Pronunciación', 
      meaning: 'Significado', 
      root: 'Raíz', 
      equivalents: 'Equivalentes', 
      description: 'Descripción', 
      verses: 'Versículos de Referencia', 
      askAi: 'Preguntar a la IA', 
      askPlaceholder: 'Haz una pregunta sobre este término...', 
      ask: 'Preguntar',
      addFavorite: 'Añadir a Favoritos',
      removeFavorite: 'Quitar de Favoritos',
      addFlashcard: 'Crear Flashcard',
      flashcardCreated: '¡Flashcard creada!',
      favorites: 'Favoritos',
      all: 'Todos',
      goToFlashcards: 'Estudiar Flashcards'
    },
    de: { 
      title: 'Biblisches Wörterbuch', 
      subtitle: 'Erkunde die ursprünglichen hebräischen und griechischen Begriffe der Bibel', 
      search: 'Begriff suchen...', 
      transliteration: 'Transliteration', 
      pronunciation: 'Aussprache', 
      meaning: 'Bedeutung', 
      root: 'Wurzel', 
      equivalents: 'Äquivalente', 
      description: 'Beschreibung', 
      verses: 'Referenzverse', 
      askAi: 'KI fragen', 
      askPlaceholder: 'Stelle eine Frage zu diesem Begriff...', 
      ask: 'Fragen',
      addFavorite: 'Zu Favoriten hinzufügen',
      removeFavorite: 'Von Favoriten entfernen',
      addFlashcard: 'Karteikarte erstellen',
      flashcardCreated: 'Karteikarte erstellt!',
      favorites: 'Favoriten',
      all: 'Alle',
      goToFlashcards: 'Karteikarten lernen'
    },
    fr: { 
      title: 'Dictionnaire Biblique', 
      subtitle: 'Explorez les termes hébreux et grecs originaux de la Bible', 
      search: 'Rechercher un terme...', 
      transliteration: 'Translittération', 
      pronunciation: 'Prononciation', 
      meaning: 'Signification', 
      root: 'Racine', 
      equivalents: 'Équivalents', 
      description: 'Description', 
      verses: 'Versets de Référence', 
      askAi: 'Demander à l\'IA', 
      askPlaceholder: 'Posez une question sur ce terme...', 
      ask: 'Demander',
      addFavorite: 'Ajouter aux Favoris',
      removeFavorite: 'Retirer des Favoris',
      addFlashcard: 'Créer une Flashcard',
      flashcardCreated: 'Flashcard créée!',
      favorites: 'Favoris',
      all: 'Tous',
      goToFlashcards: 'Étudier les Flashcards'
    },
    pt: { 
      title: 'Dicionário Bíblico', 
      subtitle: 'Explore os termos originais hebraicos e gregos da Bíblia', 
      search: 'Buscar termo...', 
      transliteration: 'Transliteração', 
      pronunciation: 'Pronúncia', 
      meaning: 'Significado', 
      root: 'Raiz', 
      equivalents: 'Equivalentes', 
      description: 'Descrição', 
      verses: 'Versículos de Referência', 
      askAi: 'Perguntar à IA', 
      askPlaceholder: 'Faça uma pergunta sobre este termo...', 
      ask: 'Perguntar',
      addFavorite: 'Adicionar aos Favoritos',
      removeFavorite: 'Remover dos Favoritos',
      addFlashcard: 'Criar Flashcard',
      flashcardCreated: 'Flashcard criado!',
      favorites: 'Favoritos',
      all: 'Todos',
      goToFlashcards: 'Estudar Flashcards'
    },
  };
  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  useEffect(() => {
    loadTerms();
    loadFavoriteIds();
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

  const loadFavoriteIds = async () => {
    try {
      const favorites = await api.getDictionaryFavorites(currentLanguage);
      const ids = new Set(favorites.map((f: any) => f.term_id));
      setFavoriteIds(ids);
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };

  const handleAiSearch = async () => {
    if (!searchQuery.trim()) return;
    setAiSearching(true);
    setAiSearchResult(null);
    try {
      const data = await api.aiSearchDictionary(searchQuery.trim(), currentLanguage);
      setAiSearchResult(data.term);
    } catch (error) {
      console.error('AI search error:', error);
    } finally {
      setAiSearching(false);
    }
  };

  const loadTerm = async (termId: string) => {
    setLoadingTerm(true);
    setAiAnswer('');
    setSelectedTermId(termId);
    try {
      const data = await api.getDictionaryTerm(termId, currentLanguage);
      setSelectedTerm(data);
      
      // Check if favorite
      const favCheck = await api.checkDictionaryFavorite(termId);
      setIsFavorite(favCheck.is_favorite);
    } catch (error) {
      console.error('Error loading term:', error);
    } finally {
      setLoadingTerm(false);
    }
  };

  const toggleFavorite = async () => {
    if (!selectedTermId) return;
    setFavoriteLoading(true);
    try {
      if (isFavorite) {
        await api.removeDictionaryFavorite(selectedTermId);
        setIsFavorite(false);
        setFavoriteIds(prev => {
          const next = new Set(prev);
          next.delete(selectedTermId);
          return next;
        });
      } else {
        await api.addDictionaryFavorite(selectedTermId);
        setIsFavorite(true);
        setFavoriteIds(prev => new Set(prev).add(selectedTermId));
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    } finally {
      setFavoriteLoading(false);
    }
  };

  const createFlashcard = async () => {
    if (!selectedTermId) return;
    setFlashcardLoading(true);
    try {
      await api.createFlashcard(selectedTermId);
      // Show success feedback
      if (typeof window !== 'undefined') {
        window.alert(t('flashcardCreated'));
      }
    } catch (error) {
      console.error('Error creating flashcard:', error);
    } finally {
      setFlashcardLoading(false);
    }
  };

  const askAI = async () => {
    if (!aiQuestion.trim() || !selectedTerm) return;
    
    setAskingAi(true);
    try {
      const result = await api.aiDictionaryStudy(selectedTermId, aiQuestion);
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

  const displayedTerms = showFavoritesOnly 
    ? filteredTerms.filter(t => favoriteIds.has(t.id))
    : filteredTerms;

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
            <Icon name="arrow-back" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title}>{t('title')}</Text>
          <TouchableOpacity onPress={toggleFavorite} disabled={favoriteLoading}>
            {favoriteLoading ? (
              <ActivityIndicator size="small" color={COLORS.primary} />
            ) : (
              <Icon 
                name={isFavorite ? "heart" : "heart-outline"} 
                size={28} 
                color={isFavorite ? COLORS.error : COLORS.text} 
              />
            )}
          </TouchableOpacity>
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

              {/* Action Buttons */}
              <View style={styles.actionButtons}>
                <TouchableOpacity 
                  style={[styles.actionButton, isFavorite && styles.actionButtonActive]}
                  onPress={toggleFavorite}
                  disabled={favoriteLoading}
                >
                  <Icon 
                    name={isFavorite ? "heart" : "heart-outline"} 
                    size={20} 
                    color={isFavorite ? "#fff" : COLORS.primary} 
                  />
                  <Text style={[styles.actionButtonText, isFavorite && styles.actionButtonTextActive]}>
                    {isFavorite ? t('removeFavorite') : t('addFavorite')}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity 
                  style={styles.actionButton}
                  onPress={createFlashcard}
                  disabled={flashcardLoading}
                >
                  {flashcardLoading ? (
                    <ActivityIndicator size="small" color={COLORS.primary} />
                  ) : (
                    <>
                      <Icon name="card-outline" size={20} color={COLORS.primary} />
                      <Text style={styles.actionButtonText}>{t('addFlashcard')}</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>

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
                  <Text style={styles.sectionTitle}>{t('equivalents')}</Text>
                  {selectedTerm.hebrew_equivalent && (
                    <Text style={styles.sectionText}>📜 Ebraico: {selectedTerm.hebrew_equivalent}</Text>
                  )}
                  {selectedTerm.greek_equivalent && (
                    <Text style={styles.sectionText}>🏛️ Greco: {selectedTerm.greek_equivalent}</Text>
                  )}
                </View>
              )}

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>{t('description')}</Text>
                <Text style={styles.descriptionText}>{selectedTerm.description}</Text>
              </View>

              <View style={styles.section}>
                <Text style={styles.sectionTitle}>{t('verses')}</Text>
                {selectedTerm.verses.map((verse, index) => (
                  <View key={index} style={styles.verseCard}>
                    <Text style={styles.verseRef}>{verse.ref}</Text>
                    <Text style={styles.verseText}>{verse.text}</Text>
                  </View>
                ))}
              </View>

              <View style={styles.aiSection}>
                <Text style={styles.sectionTitle}>{t('askAi')}</Text>
                <TextInput
                  style={styles.aiInput}
                  placeholder={t('askPlaceholder')}
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
                    <Text style={styles.aiButtonText}>{t('ask')}</Text>
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
        <TouchableOpacity onPress={() => router.push('/(tabs)/profile')} data-testid="dictionary-back-btn">
          <Icon name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('title')}</Text>
        <TouchableOpacity onPress={() => router.push('/flashcards')}>
          <Icon name="card" size={28} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color={COLORS.textMuted} />
        <TextInput
          style={styles.searchInput}
          placeholder={t('search')}
          placeholderTextColor={COLORS.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery ? (
          <TouchableOpacity onPress={() => { setSearchQuery(''); setAiSearchResult(null); }}>
            <Icon name="close-circle" size={20} color={COLORS.textMuted} />
          </TouchableOpacity>
        ) : null}
        {searchQuery.length >= 2 && (
          <TouchableOpacity
            style={styles.aiSearchBtn}
            onPress={handleAiSearch}
            disabled={aiSearching}
            data-testid="dictionary-ai-search-btn"
          >
            {aiSearching ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Icon name="sparkles" size={16} color="#fff" />
            )}
          </TouchableOpacity>
        )}
      </View>

      {/* AI Search Result */}
      {aiSearchResult && (
        <View style={styles.aiResultCard}>
          <View style={styles.aiResultHeader}>
            <Icon name="sparkles" size={16} color={COLORS.primary} />
            <Text style={styles.aiResultTitle}>{aiSearchResult.term}</Text>
          </View>
          {aiSearchResult.found === false ? (
            <Text style={styles.aiResultText}>{aiSearchResult.suggestion || 'Termine non trovato'}</Text>
          ) : (
            <>
              {aiSearchResult.origin && <Text style={styles.aiResultOrigin}>{aiSearchResult.origin}</Text>}
              {aiSearchResult.meaning && <Text style={styles.aiResultMeaning}>{aiSearchResult.meaning}</Text>}
              {aiSearchResult.description && <Text style={styles.aiResultText}>{aiSearchResult.description}</Text>}
              {aiSearchResult.verses && aiSearchResult.verses.length > 0 && (
                <View style={{ marginTop: 8 }}>
                  {aiSearchResult.verses.slice(0, 3).map((v: any, i: number) => (
                    <Text key={i} style={styles.aiVerse}>{v.ref}: {v.text}</Text>
                  ))}
                </View>
              )}
            </>
          )}
          <TouchableOpacity onPress={() => setAiSearchResult(null)} style={styles.aiCloseBtn}>
            <Text style={styles.aiCloseBtnText}>Chiudi</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Filter Tabs */}
      <View style={styles.filterTabs}>
        <TouchableOpacity 
          style={[styles.filterTab, !showFavoritesOnly && styles.filterTabActive]}
          onPress={() => setShowFavoritesOnly(false)}
        >
          <Text style={[styles.filterTabText, !showFavoritesOnly && styles.filterTabTextActive]}>
            {t('all')} ({terms.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.filterTab, showFavoritesOnly && styles.filterTabActive]}
          onPress={() => setShowFavoritesOnly(true)}
        >
          <Icon 
            name="heart" 
            size={16} 
            color={showFavoritesOnly ? '#fff' : COLORS.primary} 
            style={{ marginRight: 4 }}
          />
          <Text style={[styles.filterTabText, showFavoritesOnly && styles.filterTabTextActive]}>
            {t('favorites')} ({favoriteIds.size})
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.termsContainer}>
        <Text style={styles.subtitle}>
          {t('subtitle')}
        </Text>

        {displayedTerms.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon name="heart-outline" size={48} color={COLORS.textMuted} />
            <Text style={styles.emptyText}>
              {showFavoritesOnly ? 'Nessun preferito salvato' : 'Nessun risultato'}
            </Text>
          </View>
        ) : (
          displayedTerms.map((term) => (
            <TouchableOpacity
              key={term.id}
              style={styles.termCard}
              onPress={() => loadTerm(term.id)}
            >
              <View style={styles.termCardIcon}>
                <Text style={styles.termCardLetter}>
                  {term.origin.includes('Ebraico') || term.origin.includes('Hebrew') ? 'א' : 
                   term.origin.includes('Aramaico') || term.origin.includes('Aramaic') ? 'א' : 'α'}
                </Text>
              </View>
              <View style={styles.termCardContent}>
                <Text style={styles.termCardTitle}>{term.term}</Text>
                <Text style={styles.termCardMeaning} numberOfLines={1}>{term.meaning}</Text>
                <Text style={styles.termCardOrigin}>{term.origin}</Text>
              </View>
              {favoriteIds.has(term.id) && (
                <Icon name="heart" size={16} color={COLORS.error} style={{ marginRight: 8 }} />
              )}
              <Icon name="chevron-forward" size={20} color={COLORS.textMuted} />
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
  // AI Search
  aiSearchBtn: {
    width: 32, height: 32, borderRadius: 16, backgroundColor: COLORS.primary,
    justifyContent: 'center', alignItems: 'center', marginLeft: 6,
  },
  aiResultCard: {
    marginHorizontal: SPACING.md, marginBottom: SPACING.sm, padding: SPACING.md,
    backgroundColor: COLORS.primary + '08', borderRadius: BORDER_RADIUS.md,
    borderWidth: 1, borderColor: COLORS.primary + '30',
  },
  aiResultHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  aiResultTitle: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginLeft: 6 },
  aiResultOrigin: { fontSize: 12, color: COLORS.textLight, marginBottom: 4, fontStyle: 'italic' },
  aiResultMeaning: { fontSize: 15, fontWeight: '600', color: COLORS.text, marginBottom: 6 },
  aiResultText: { fontSize: 14, color: COLORS.text, lineHeight: 20 },
  aiVerse: { fontSize: 13, color: COLORS.textLight, marginTop: 4, fontStyle: 'italic' },
  aiCloseBtn: { alignSelf: 'flex-end', marginTop: 8 },
  aiCloseBtnText: { color: COLORS.primary, fontSize: 13, fontWeight: '600' },
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
    marginBottom: 0,
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
  filterTabs: {
    flexDirection: 'row',
    margin: SPACING.md,
    gap: SPACING.sm,
  },
  filterTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.card,
  },
  filterTabActive: {
    backgroundColor: COLORS.primary,
  },
  filterTabText: {
    fontSize: 14,
    color: COLORS.text,
  },
  filterTabTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  termsContainer: {
    padding: SPACING.md,
    paddingTop: 0,
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
  actionButtons: {
    flexDirection: 'row',
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.xs,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  actionButtonActive: {
    backgroundColor: COLORS.primary,
  },
  actionButtonText: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '500',
  },
  actionButtonTextActive: {
    color: '#fff',
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
  emptyState: {
    alignItems: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    marginTop: SPACING.md,
    fontSize: 16,
    color: COLORS.textMuted,
  },
});
