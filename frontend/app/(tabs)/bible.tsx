import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import { api } from '../../src/utils/api';
import { useLanguageStore } from '../../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../../src/utils/theme';

interface Book {
  name: string;
  chapters: number;
  abbrev: string;
}

interface Verse {
  verse: number;
  text: string;
}

interface BibleEdition {
  name: string;
  language: string;
  year: string;
  description: string;
}

export default function BibleScreen() {
  const { currentLanguage, languages, setLanguage } = useLanguageStore();
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null);
  const [verses, setVerses] = useState<Verse[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingBooks, setLoadingBooks] = useState(true);
  const [view, setView] = useState<'books' | 'chapters' | 'reading'>('books');
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // Edition selector
  const [editions, setEditions] = useState<Record<string, BibleEdition>>({});
  const [selectedEdition, setSelectedEdition] = useState<string>('nuova_diodati');
  const [showEditionSelector, setShowEditionSelector] = useState(false);
  const [showLanguageModal, setShowLanguageModal] = useState(false);

  // Load editions
  useEffect(() => {
    loadEditions();
  }, []);

  // Load books when language changes
  useEffect(() => {
    loadBooks();
  }, [currentLanguage]);

  const loadEditions = async () => {
    try {
      const data = await api.getBibleEditions();
      setEditions(data);
    } catch (error) {
      console.log('Error loading editions:', error);
    }
  };

  const loadBooks = useCallback(async () => {
    setLoadingBooks(true);
    try {
      const data = await api.getBibleBooks(currentLanguage);
      setBooks(data || []);
    } catch (error) {
      console.log('Error loading books:', error);
      setBooks([]);
    } finally {
      setLoadingBooks(false);
    }
  }, [currentLanguage]);

  const loadChapter = async (book: string, chapter: number) => {
    setLoading(true);
    try {
      const data = await api.getChapter(book, chapter, currentLanguage);
      setVerses(data.verses || []);
      setView('reading');
      await api.updateReadingProgress().catch(() => {});
    } catch (error) {
      console.log('Error loading chapter:', error);
      setVerses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleBookSelect = (book: Book) => {
    setSelectedBook(book);
    setView('chapters');
  };

  const handleChapterSelect = (chapter: number) => {
    setSelectedChapter(chapter);
    if (selectedBook) {
      loadChapter(selectedBook.name, chapter);
    }
  };

  const handleBack = () => {
    Speech.stop();
    setIsSpeaking(false);
    
    if (view === 'reading') {
      setView('chapters');
      setVerses([]);
    } else if (view === 'chapters') {
      setView('books');
      setSelectedBook(null);
    }
  };

  const handleSpeak = () => {
    if (isSpeaking) {
      Speech.stop();
      setIsSpeaking(false);
    } else {
      const fullText = verses.map(v => v.text).join(' ');
      const ttsCode = languages[currentLanguage]?.tts_code || 'it-IT';
      
      Speech.speak(fullText, {
        language: ttsCode,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
      });
      setIsSpeaking(true);
    }
  };

  const handleEditionSelect = (editionKey: string) => {
    setSelectedEdition(editionKey);
    const edition = editions[editionKey];
    if (edition) {
      setLanguage(edition.language);
    }
    setShowEditionSelector(false);
  };

  const handleLanguageSelect = async (lang: string) => {
    await setLanguage(lang);
    setShowLanguageModal(false);
  };

  const currentEdition = editions[selectedEdition];

  const renderBooks = () => {
    if (loadingBooks) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Caricamento libri...</Text>
        </View>
      );
    }

    if (!books || books.length === 0) {
      return (
        <View style={styles.emptyContainer}>
          <Ionicons name="book-outline" size={64} color={COLORS.textMuted} />
          <Text style={styles.emptyText}>Nessun libro disponibile</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadBooks}>
            <Text style={styles.retryText}>Riprova</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <FlatList
        data={books}
        keyExtractor={(item, index) => `${item.abbrev}-${index}`}
        numColumns={2}
        columnWrapperStyle={styles.bookRow}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.bookCard}
            onPress={() => handleBookSelect(item)}
          >
            <Text style={styles.bookName} numberOfLines={2}>{item.name}</Text>
            <Text style={styles.bookChapters}>{item.chapters} capitoli</Text>
          </TouchableOpacity>
        )}
      />
    );
  };

  const renderChapters = () => {
    if (!selectedBook) return null;
    const chapters = Array.from({ length: selectedBook.chapters }, (_, i) => i + 1);

    return (
      <FlatList
        key="chapters-list"
        data={chapters}
        keyExtractor={(item) => `chapter-${item}`}
        numColumns={5}
        columnWrapperStyle={styles.chapterRow}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.chapterCard}
            onPress={() => handleChapterSelect(item)}
          >
            <Text style={styles.chapterNumber}>{item}</Text>
          </TouchableOpacity>
        )}
      />
    );
  };

  const renderReading = () => (
    <ScrollView contentContainerStyle={styles.readingContent}>
      {verses.map((verse) => (
        <View key={verse.verse} style={styles.verseContainer}>
          <Text style={styles.verseNumber}>{verse.verse}</Text>
          <Text style={styles.verseText}>{verse.text}</Text>
        </View>
      ))}
    </ScrollView>
  );

  // Edition Selector Modal
  const renderEditionSelector = () => (
    <Modal
      visible={showEditionSelector}
      animationType="slide"
      transparent
      onRequestClose={() => setShowEditionSelector(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Seleziona Edizione Biblica</Text>
            <TouchableOpacity onPress={() => setShowEditionSelector(false)}>
              <Ionicons name="close" size={24} color={COLORS.text} />
            </TouchableOpacity>
          </View>
          
          <ScrollView>
            {Object.entries(editions).map(([key, edition]) => (
              <TouchableOpacity
                key={key}
                style={[
                  styles.editionItem,
                  selectedEdition === key && styles.editionItemSelected,
                ]}
                onPress={() => handleEditionSelect(key)}
              >
                <View style={styles.editionInfo}>
                  <Text style={styles.editionFlag}>
                    {languages[edition.language]?.flag || '📖'}
                  </Text>
                  <View style={styles.editionDetails}>
                    <Text style={styles.editionName}>{edition.name}</Text>
                    <Text style={styles.editionYear}>{edition.year}</Text>
                    <Text style={styles.editionDesc} numberOfLines={2}>
                      {edition.description}
                    </Text>
                  </View>
                </View>
                {selectedEdition === key && (
                  <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );

  // Language Selector Modal
  const renderLanguageModal = () => (
    <Modal
      visible={showLanguageModal}
      animationType="slide"
      transparent
      onRequestClose={() => setShowLanguageModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Seleziona Lingua</Text>
            <TouchableOpacity onPress={() => setShowLanguageModal(false)}>
              <Ionicons name="close" size={24} color={COLORS.text} />
            </TouchableOpacity>
          </View>
          
          <ScrollView>
            {Object.entries(languages).map(([code, lang]) => (
              <TouchableOpacity
                key={code}
                style={[
                  styles.languageItem,
                  currentLanguage === code && styles.languageItemSelected,
                ]}
                onPress={() => handleLanguageSelect(code)}
              >
                <Text style={styles.languageFlag}>{lang.flag}</Text>
                <Text style={styles.languageName}>{lang.name}</Text>
                {currentLanguage === code && (
                  <Ionicons name="checkmark-circle" size={24} color={COLORS.primary} />
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        {view !== 'books' && (
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Ionicons name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
        )}
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>
            {view === 'books'
              ? 'La Bibbia'
              : view === 'chapters'
              ? selectedBook?.name
              : `${selectedBook?.name} ${selectedChapter}`}
          </Text>
          <TouchableOpacity 
            style={styles.editionBadge}
            onPress={() => setShowEditionSelector(true)}
          >
            <Text style={styles.editionBadgeText}>
              {currentEdition?.name || 'Seleziona edizione'}
            </Text>
            <Ionicons name="chevron-down" size={14} color={COLORS.primary} />
          </TouchableOpacity>
        </View>
        
        <View style={styles.headerActions}>
          {view === 'reading' && (
            <TouchableOpacity style={styles.headerButton} onPress={handleSpeak}>
              <Ionicons
                name={isSpeaking ? 'stop' : 'volume-high'}
                size={22}
                color={COLORS.primary}
              />
            </TouchableOpacity>
          )}
          <TouchableOpacity 
            style={styles.headerButton} 
            onPress={() => setShowLanguageModal(true)}
          >
            <Text style={styles.langFlag}>
              {languages[currentLanguage]?.flag || '🌐'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : view === 'books' ? (
        renderBooks()
      ) : view === 'chapters' ? (
        renderChapters()
      ) : (
        renderReading()
      )}

      {/* Modals */}
      {renderEditionSelector()}
      {renderLanguageModal()}
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
    marginRight: SPACING.xs,
  },
  headerTitleContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  editionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  editionBadgeText: {
    fontSize: 12,
    color: COLORS.primary,
    marginRight: 4,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerButton: {
    padding: SPACING.sm,
  },
  langFlag: {
    fontSize: 22,
  },
  listContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  bookRow: {
    justifyContent: 'space-between',
    marginBottom: SPACING.sm,
  },
  bookCard: {
    width: '48%',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    minHeight: 80,
    ...SHADOWS.small,
  },
  bookName: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  bookChapters: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  chapterRow: {
    justifyContent: 'flex-start',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  chapterCard: {
    width: 56,
    height: 56,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    justifyContent: 'center',
    alignItems: 'center',
    ...SHADOWS.small,
  },
  chapterNumber: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  readingContent: {
    padding: SPACING.lg,
    paddingBottom: 120,
  },
  verseContainer: {
    flexDirection: 'row',
    marginBottom: SPACING.md,
  },
  verseNumber: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
    marginRight: SPACING.sm,
    marginTop: 2,
    minWidth: 24,
  },
  verseText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 26,
    color: COLORS.text,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: SPACING.md,
    fontSize: 14,
    color: COLORS.textLight,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textLight,
    marginTop: SPACING.md,
    marginBottom: SPACING.lg,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
  },
  retryText: {
    color: '#fff',
    fontWeight: '600',
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  editionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  editionItemSelected: {
    backgroundColor: COLORS.primary + '10',
  },
  editionInfo: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
  },
  editionFlag: {
    fontSize: 28,
    marginRight: SPACING.md,
  },
  editionDetails: {
    flex: 1,
  },
  editionName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  editionYear: {
    fontSize: 12,
    color: COLORS.primary,
    marginTop: 2,
  },
  editionDesc: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 4,
  },
  languageItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  languageItemSelected: {
    backgroundColor: COLORS.primary + '10',
  },
  languageFlag: {
    fontSize: 28,
    marginRight: SPACING.md,
  },
  languageName: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
});
