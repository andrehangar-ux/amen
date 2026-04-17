import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface SearchResults {
  verses: any[];
  books: any[];
  notes: any[];
  bookmarks: any[];
  dictionary: any[];
}

const CATEGORY_CONFIG: Record<string, { icon: string; color: string; labelIt: string; labelEn: string }> = {
  verses:     { icon: 'book-outline',     color: '#6B7F5B', labelIt: 'Versetti',    labelEn: 'Verses' },
  books:      { icon: 'library-outline',  color: '#D4A574', labelIt: 'Libri',       labelEn: 'Books' },
  notes:      { icon: 'document-text',    color: '#5B8FA8', labelIt: 'Note',        labelEn: 'Notes' },
  bookmarks:  { icon: 'bookmark',         color: '#A67F6B', labelIt: 'Segnalibri',  labelEn: 'Bookmarks' },
  dictionary: { icon: 'language',         color: '#7B6BA0', labelIt: 'Dizionario',  labelEn: 'Dictionary' },
};

const translations: Record<string, Record<string, string>> = {
  it: {
    title: 'Ricerca',
    placeholder: 'Cerca versetti, libri, parole...',
    searching: 'Ricerca in corso...',
    results: 'risultati',
    noResults: 'Nessun risultato',
    noResultsHint: 'Prova con parole diverse o piu brevi',
    searchHint: 'Cerca nella Bibbia',
    searchDesc: 'Trova versetti, libri, capitoli, termini del dizionario e le tue note personali',
    chapters: 'capitoli',
    openBook: 'Apri',
    recentSearches: 'Suggerimenti',
    suggestions: ['amore', 'fede', 'speranza', 'Genesi', 'Salmi', 'Giovanni', 'grazia', 'pace'],
  },
  en: {
    title: 'Search',
    placeholder: 'Search verses, books, words...',
    searching: 'Searching...',
    results: 'results',
    noResults: 'No results',
    noResultsHint: 'Try different or shorter words',
    searchHint: 'Search the Bible',
    searchDesc: 'Find verses, books, chapters, dictionary terms and your personal notes',
    chapters: 'chapters',
    openBook: 'Open',
    recentSearches: 'Suggestions',
    suggestions: ['love', 'faith', 'hope', 'Genesis', 'Psalms', 'John', 'grace', 'peace'],
  },
  es: {
    title: 'Buscar',
    placeholder: 'Buscar versiculos, libros, palabras...',
    searching: 'Buscando...',
    results: 'resultados',
    noResults: 'Sin resultados',
    noResultsHint: 'Intenta con palabras diferentes',
    searchHint: 'Buscar en la Biblia',
    searchDesc: 'Encuentra versiculos, libros, capitulos, terminos del diccionario y tus notas',
    chapters: 'capitulos',
    openBook: 'Abrir',
    recentSearches: 'Sugerencias',
    suggestions: ['amor', 'fe', 'esperanza', 'Genesis', 'Salmos', 'Juan', 'gracia', 'paz'],
  },
  pt: {
    title: 'Pesquisar',
    placeholder: 'Pesquisar versiculos, livros...',
    searching: 'Pesquisando...',
    results: 'resultados',
    noResults: 'Sem resultados',
    noResultsHint: 'Tente palavras diferentes',
    searchHint: 'Pesquisar na Biblia',
    searchDesc: 'Encontre versiculos, livros, capitulos, termos do dicionario e suas notas',
    chapters: 'capitulos',
    openBook: 'Abrir',
    recentSearches: 'Sugestoes',
    suggestions: ['amor', 'fe', 'esperanca', 'Genesis', 'Salmos', 'Joao', 'graca', 'paz'],
  },
  fr: {
    title: 'Rechercher',
    placeholder: 'Chercher versets, livres, mots...',
    searching: 'Recherche en cours...',
    results: 'resultats',
    noResults: 'Aucun resultat',
    noResultsHint: 'Essayez des mots differents',
    searchHint: 'Rechercher dans la Bible',
    searchDesc: 'Trouvez des versets, livres, chapitres, termes du dictionnaire et vos notes',
    chapters: 'chapitres',
    openBook: 'Ouvrir',
    recentSearches: 'Suggestions',
    suggestions: ['amour', 'foi', 'esperance', 'Genese', 'Psaumes', 'Jean', 'grace', 'paix'],
  },
  de: {
    title: 'Suche',
    placeholder: 'Verse, Bucher, Worter suchen...',
    searching: 'Suche lauft...',
    results: 'Ergebnisse',
    noResults: 'Keine Ergebnisse',
    noResultsHint: 'Versuchen Sie andere Worter',
    searchHint: 'In der Bibel suchen',
    searchDesc: 'Finden Sie Verse, Bucher, Kapitel, Worterbuchbegriffe und Ihre Notizen',
    chapters: 'Kapitel',
    openBook: 'Offnen',
    recentSearches: 'Vorschlage',
    suggestions: ['Liebe', 'Glaube', 'Hoffnung', 'Genesis', 'Psalmen', 'Johannes', 'Gnade', 'Frieden'],
  },
};

export default function SearchScreen() {
  const { currentLanguage } = useLanguageStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [searched, setSearched] = useState(false);
  const inputRef = useRef<TextInput>(null);

  const t = (key: string) => {
    const langData = translations[currentLanguage] || translations['it'];
    return (langData as any)[key] || (translations['it'] as any)[key] || key;
  };
  const suggestions: string[] = (translations[currentLanguage] || translations['it']).suggestions as any || translations['it'].suggestions as any;

  const performSearch = async (searchQuery?: string) => {
    const q = (searchQuery || query).trim();
    if (!q) return;
    if (searchQuery) setQuery(searchQuery);
    
    setLoading(true);
    setSearched(true);
    try {
      const response = await api.globalSearch(q, currentLanguage);
      setResults(response.results);
      setTotalResults(response.total_results);
    } catch (error) {
      console.log('Search error:', error);
      setResults({ verses: [], books: [], notes: [], bookmarks: [], dictionary: [] });
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const navigateToBook = (bookName: string) => {
    router.push('/(tabs)/bible');
  };

  const navigateToVerse = (book: string, chapter: number) => {
    router.push('/(tabs)/bible');
  };

  const renderSection = (key: string, items: any[]) => {
    if (!items || items.length === 0) return null;
    const config = CATEGORY_CONFIG[key];
    const label = currentLanguage === 'en' ? config.labelEn : config.labelIt;

    return (
      <View style={styles.section} key={key}>
        <View style={styles.sectionHeader}>
          <View style={[styles.sectionIcon, { backgroundColor: config.color + '18' }]}>
            <Icon name={config.icon as any} size={16} color={config.color} />
          </View>
          <Text style={styles.sectionTitle}>{label}</Text>
          <View style={styles.sectionBadge}>
            <Text style={styles.sectionBadgeText}>{items.length}</Text>
          </View>
        </View>
        {items.map((item, idx) => renderItem(key, item, idx))}
      </View>
    );
  };

  const renderItem = (category: string, item: any, idx: number) => {
    const config = CATEGORY_CONFIG[category];

    if (category === 'books') {
      return (
        <TouchableOpacity
          key={`book-${idx}`}
          style={styles.bookCard}
          onPress={() => navigateToBook(item.name)}
          data-testid={`search-book-${item.abbrev}`}
        >
          <View style={[styles.bookIcon, { backgroundColor: config.color }]}>
            <Text style={styles.bookIconText}>{item.abbrev}</Text>
          </View>
          <View style={styles.bookInfo}>
            <Text style={styles.bookName}>{item.name}</Text>
            <Text style={styles.bookChapters}>{item.chapters} {t('chapters')}</Text>
          </View>
          <Icon name="chevron-forward" size={18} color={COLORS.textMuted} />
        </TouchableOpacity>
      );
    }

    if (category === 'verses') {
      return (
        <TouchableOpacity
          key={`verse-${idx}`}
          style={styles.resultCard}
          onPress={() => navigateToVerse(item.book, item.chapter)}
          data-testid={`search-verse-${idx}`}
        >
          <View style={styles.verseRef}>
            <Text style={styles.verseRefText}>{item.ref}</Text>
          </View>
          <Text style={styles.verseText} numberOfLines={2}>{item.text}</Text>
        </TouchableOpacity>
      );
    }

    if (category === 'dictionary') {
      return (
        <TouchableOpacity
          key={`dict-${idx}`}
          style={styles.resultCard}
          onPress={() => router.push('/dictionary')}
          data-testid={`search-dict-${idx}`}
        >
          <Text style={[styles.dictTerm, { color: config.color }]}>{item.term}</Text>
          <Text style={styles.dictMeaning} numberOfLines={2}>{item.meaning}</Text>
        </TouchableOpacity>
      );
    }

    // Notes & Bookmarks
    return (
      <TouchableOpacity
        key={`${category}-${idx}`}
        style={styles.resultCard}
        onPress={() => router.push('/my-content')}
        data-testid={`search-${category}-${idx}`}
      >
        <Text style={styles.noteRef}>{item.verse_ref || ''}</Text>
        <Text style={styles.noteContent} numberOfLines={2}>{item.content || item.text || ''}</Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} data-testid="search-screen">
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn} data-testid="search-back-btn">
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>{t('title')}</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Search Bar */}
      <View style={styles.searchBar}>
        <View style={styles.searchInputWrap}>
          <Icon name="search" size={20} color={COLORS.textMuted} />
          <TextInput
            ref={inputRef}
            style={styles.searchInput}
            placeholder={t('placeholder')}
            placeholderTextColor={COLORS.textMuted}
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={() => performSearch()}
            returnKeyType="search"
            autoFocus
            data-testid="search-input"
          />
          {query.length > 0 && (
            <TouchableOpacity onPress={() => { setQuery(''); setResults(null); setSearched(false); }}>
              <Icon name="close-circle" size={20} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>{t('searching')}</Text>
        </View>
      ) : searched && results ? (
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {totalResults > 0 ? (
            <>
              <Text style={styles.resultsCount}>
                {totalResults} {t('results')} — "{query}"
              </Text>
              {renderSection('books', results.books)}
              {renderSection('verses', results.verses)}
              {renderSection('dictionary', results.dictionary)}
              {renderSection('notes', results.notes)}
              {renderSection('bookmarks', results.bookmarks)}
            </>
          ) : (
            <View style={styles.centerContainer}>
              <Icon name="search-outline" size={56} color={COLORS.textMuted} />
              <Text style={styles.emptyTitle}>{t('noResults')}</Text>
              <Text style={styles.emptyDesc}>{t('noResultsHint')}</Text>
            </View>
          )}
        </ScrollView>
      ) : (
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.hintContainer}>
            <View style={styles.hintIconWrap}>
              <Icon name="search" size={40} color={COLORS.primary} />
            </View>
            <Text style={styles.hintTitle}>{t('searchHint')}</Text>
            <Text style={styles.hintDesc}>{t('searchDesc')}</Text>
          </View>

          {/* Suggestion chips */}
          <Text style={styles.suggestionsLabel}>{t('recentSearches')}</Text>
          <View style={styles.chipsContainer}>
            {suggestions.map((s, i) => (
              <TouchableOpacity
                key={i}
                style={styles.chip}
                onPress={() => performSearch(s)}
                data-testid={`suggestion-${i}`}
              >
                <Text style={styles.chipText}>{s}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      )}
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
    paddingVertical: SPACING.md,
    backgroundColor: COLORS.card,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backBtn: {
    padding: SPACING.sm,
    marginRight: SPACING.sm,
  },
  title: {
    flex: 1,
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    letterSpacing: -0.3,
  },
  // Search Bar
  searchBar: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.card,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  searchInputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    height: 48,
    gap: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  // Center states
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  loadingText: {
    marginTop: SPACING.md,
    fontSize: 15,
    color: COLORS.textLight,
  },
  // Results
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 120,
  },
  resultsCount: {
    fontSize: 13,
    color: COLORS.textLight,
    marginBottom: SPACING.md,
  },
  // Sections
  section: {
    marginBottom: SPACING.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
    gap: SPACING.sm,
  },
  sectionIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  sectionBadge: {
    backgroundColor: COLORS.primary + '15',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  sectionBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  // Book card
  bookCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  bookIcon: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bookIconText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#fff',
  },
  bookInfo: {
    flex: 1,
    marginLeft: SPACING.md,
  },
  bookName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  bookChapters: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  // Result card (verses, notes, bookmarks)
  resultCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  verseRef: {
    backgroundColor: COLORS.primary + '12',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: 6,
  },
  verseRefText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  verseText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 21,
  },
  dictTerm: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 4,
  },
  dictMeaning: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 20,
  },
  noteRef: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 4,
  },
  noteContent: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  // Empty / Hint
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textMuted,
    marginTop: SPACING.md,
  },
  emptyDesc: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
  hintContainer: {
    alignItems: 'center',
    paddingVertical: SPACING.xl,
  },
  hintIconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primary + '12',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  hintTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  hintDesc: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    lineHeight: 21,
    maxWidth: 300,
  },
  // Suggestions
  suggestionsLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.textLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: SPACING.lg,
    marginBottom: SPACING.sm,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  chip: {
    backgroundColor: COLORS.card,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.full,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
  },
  chipText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '500',
  },
});
