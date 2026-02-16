import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface SearchResult {
  type: string;
  id?: string;
  name?: string;
  verse_ref?: string;
  content?: string;
  text?: string;
  term?: string;
  meaning?: string;
  color?: string;
  email?: string;
  country?: string;
  url?: string;
}

interface SearchResults {
  notes: SearchResult[];
  bookmarks: SearchResult[];
  highlights: SearchResult[];
  users: SearchResult[];
  dictionary: SearchResult[];
  radios: SearchResult[];
}

export default function SearchScreen() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  const performSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await api.globalSearch(query);
      setResults(response.results);
      setTotalResults(response.total_results);
    } catch (error) {
      console.log('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderResultItem = (item: SearchResult, index: number) => {
    const getIcon = () => {
      switch (item.type) {
        case 'note': return 'document-text';
        case 'bookmark': return 'bookmark';
        case 'highlight': return 'color-fill';
        case 'user': return 'person';
        case 'dictionary': return 'book';
        case 'radio': return 'radio';
        default: return 'search';
      }
    };

    const getColor = () => {
      switch (item.type) {
        case 'note': return '#4CAF50';
        case 'bookmark': return '#2196F3';
        case 'highlight': return item.color || '#FFEB3B';
        case 'user': return '#9C27B0';
        case 'dictionary': return '#FF9800';
        case 'radio': return '#E91E63';
        default: return COLORS.primary;
      }
    };

    const getTitle = () => {
      switch (item.type) {
        case 'note':
        case 'bookmark':
        case 'highlight':
          return item.verse_ref || 'Versetto';
        case 'user':
          return item.name || 'Utente';
        case 'dictionary':
          return item.term || 'Termine';
        case 'radio':
          return item.name || 'Radio';
        default:
          return 'Risultato';
      }
    };

    const getSubtitle = () => {
      switch (item.type) {
        case 'note':
          return item.content;
        case 'bookmark':
        case 'highlight':
          return item.text;
        case 'user':
          return item.email;
        case 'dictionary':
          return item.meaning;
        case 'radio':
          return item.country;
        default:
          return '';
      }
    };

    const handlePress = () => {
      switch (item.type) {
        case 'radio':
          if (item.url) Linking.openURL(item.url);
          break;
        case 'dictionary':
          router.push('/dictionary');
          break;
        default:
          // Navigate to relevant screen
          break;
      }
    };

    return (
      <TouchableOpacity 
        key={`${item.type}-${index}`} 
        style={styles.resultItem}
        onPress={handlePress}
      >
        <View style={[styles.resultIcon, { backgroundColor: getColor() + '20' }]}>
          <Ionicons name={getIcon() as any} size={20} color={getColor()} />
        </View>
        <View style={styles.resultContent}>
          <Text style={styles.resultTitle}>{getTitle()}</Text>
          <Text style={styles.resultSubtitle} numberOfLines={2}>{getSubtitle()}</Text>
          <Text style={styles.resultType}>{item.type.toUpperCase()}</Text>
        </View>
        <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
      </TouchableOpacity>
    );
  };

  const renderSection = (title: string, items: SearchResult[], icon: string) => {
    if (!items || items.length === 0) return null;
    
    return (
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Ionicons name={icon as any} size={20} color={COLORS.primary} />
          <Text style={styles.sectionTitle}>{title} ({items.length})</Text>
        </View>
        {items.map((item, index) => renderResultItem(item, index))}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>🔍 Cerca</Text>
        <View style={{ width: 28 }} />
      </View>

      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Ionicons name="search" size={20} color={COLORS.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Cerca note, segnalibri, amici, radio..."
            placeholderTextColor={COLORS.textMuted}
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={performSearch}
            returnKeyType="search"
          />
          {query.length > 0 && (
            <TouchableOpacity onPress={() => setQuery('')}>
              <Ionicons name="close-circle" size={20} color={COLORS.textMuted} />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity style={styles.searchButton} onPress={performSearch}>
          <Text style={styles.searchButtonText}>Cerca</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Ricerca in corso...</Text>
        </View>
      ) : results ? (
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {totalResults > 0 ? (
            <>
              <Text style={styles.resultsCount}>
                {totalResults} risultati per "{query}"
              </Text>
              {renderSection('Note', results.notes, 'document-text')}
              {renderSection('Segnalibri', results.bookmarks, 'bookmark')}
              {renderSection('Evidenziazioni', results.highlights, 'color-fill')}
              {renderSection('Utenti', results.users, 'people')}
              {renderSection('Dizionario', results.dictionary, 'book')}
              {renderSection('Radio', results.radios, 'radio')}
            </>
          ) : (
            <View style={styles.emptyContainer}>
              <Ionicons name="search-outline" size={64} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>Nessun risultato trovato</Text>
              <Text style={styles.emptySubtext}>Prova con altre parole chiave</Text>
            </View>
          )}
        </ScrollView>
      ) : (
        <View style={styles.emptyContainer}>
          <Ionicons name="search-outline" size={64} color={COLORS.textMuted} />
          <Text style={styles.emptyText}>Cerca nell'app</Text>
          <Text style={styles.emptySubtext}>
            Trova note, segnalibri, evidenziazioni, amici, termini biblici e radio
          </Text>
        </View>
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
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    gap: SPACING.sm,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.lg,
    paddingHorizontal: SPACING.md,
    gap: SPACING.sm,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 16,
    color: COLORS.text,
  },
  searchButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    justifyContent: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: SPACING.md,
    fontSize: 16,
    color: COLORS.textLight,
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  resultsCount: {
    fontSize: 14,
    color: COLORS.textLight,
    marginBottom: SPACING.md,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  resultIcon: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  resultContent: {
    flex: 1,
  },
  resultTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  resultSubtitle: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  resultType: {
    fontSize: 10,
    color: COLORS.primary,
    fontWeight: '600',
    marginTop: 4,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textMuted,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.sm,
    textAlign: 'center',
    paddingHorizontal: SPACING.xl,
  },
});
