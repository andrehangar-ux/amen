import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import { api } from '../../src/utils/api';
import { useLanguageStore, useTranslation } from '../../src/store/languageStore';
import { LanguageSelector } from '../../src/components/LanguageSelector';
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

export default function BibleScreen() {
  const { currentLanguage, languages } = useLanguageStore();
  const { t } = useTranslation();
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null);
  const [verses, setVerses] = useState<Verse[]>([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'books' | 'chapters' | 'reading'>('books');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showLanguageSelector, setShowLanguageSelector] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [translatedVerses, setTranslatedVerses] = useState<Verse[]>([]);
  const [showTranslation, setShowTranslation] = useState(false);
  const [targetLang, setTargetLang] = useState('en');

  useEffect(() => {
    loadBooks();
  }, [currentLanguage]);

  const loadBooks = async () => {
    try {
      const data = await api.getBibleBooks(currentLanguage);
      setBooks(data);
    } catch (error) {
      console.log('Error loading books:', error);
    }
  };

  const loadChapter = async (book: string, chapter: number) => {
    setLoading(true);
    try {
      const data = await api.getChapter(book, chapter, currentLanguage);
      setVerses(data.verses);
      setTranslatedVerses([]);
      setShowTranslation(false);
      setView('reading');
      await api.updateReadingProgress();
    } catch (error) {
      console.log('Error loading chapter:', error);
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
    if (view === 'reading') {
      setView('chapters');
      setVerses([]);
      setTranslatedVerses([]);
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
      const textToSpeak = showTranslation && translatedVerses.length > 0
        ? translatedVerses.map(v => v.text).join(' ')
        : verses.map(v => v.text).join(' ');
      
      const ttsCode = showTranslation
        ? languages[targetLang]?.tts_code || 'en-US'
        : languages[currentLanguage]?.tts_code || 'it-IT';
      
      Speech.speak(textToSpeak, {
        language: ttsCode,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
      });
      setIsSpeaking(true);
    }
  };

  const handleTranslate = async () => {
    if (translatedVerses.length > 0) {
      setShowTranslation(!showTranslation);
      return;
    }

    setTranslating(true);
    try {
      const translated = await Promise.all(
        verses.map(async (v) => {
          const result = await api.translateVerse(v.text, currentLanguage, targetLang);
          return { verse: v.verse, text: result.translated };
        })
      );
      setTranslatedVerses(translated);
      setShowTranslation(true);
    } catch (error) {
      Alert.alert('Errore', 'Traduzione non disponibile');
    } finally {
      setTranslating(false);
    }
  };

  const renderBooks = () => (
    <FlatList
      data={books}
      keyExtractor={(item) => item.abbrev}
      numColumns={2}
      columnWrapperStyle={styles.bookRow}
      contentContainerStyle={styles.listContent}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.bookCard}
          onPress={() => handleBookSelect(item)}
        >
          <Text style={styles.bookName}>{item.name}</Text>
          <Text style={styles.bookChapters}>{item.chapters} capitoli</Text>
        </TouchableOpacity>
      )}
    />
  );

  const renderChapters = () => {
    if (!selectedBook) return null;
    const chapters = Array.from({ length: selectedBook.chapters }, (_, i) => i + 1);

    return (
      <FlatList
        data={chapters}
        keyExtractor={(item) => item.toString()}
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

  const displayVerses = showTranslation && translatedVerses.length > 0 ? translatedVerses : verses;

  const renderReading = () => (
    <ScrollView contentContainerStyle={styles.readingContent}>
      {/* Translation toggle */}
      <View style={styles.translationBar}>
        <TouchableOpacity
          style={styles.translateButton}
          onPress={handleTranslate}
          disabled={translating}
        >
          {translating ? (
            <ActivityIndicator size="small" color={COLORS.primary} />
          ) : (
            <>
              <Ionicons name="language" size={20} color={COLORS.primary} />
              <Text style={styles.translateText}>
                {showTranslation ? `Mostra ${languages[currentLanguage]?.name}` : `Traduci in ${languages[targetLang]?.name}`}
              </Text>
            </>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.langSelectButton}
          onPress={() => setShowLanguageSelector(true)}
        >
          <Text style={styles.langFlag}>{languages[targetLang]?.flag}</Text>
        </TouchableOpacity>
      </View>

      {displayVerses.map((verse) => (
        <View key={verse.verse} style={styles.verseContainer}>
          <Text style={styles.verseNumber}>{verse.verse}</Text>
          <Text style={styles.verseText}>{verse.text}</Text>
        </View>
      ))}
    </ScrollView>
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
              ? t('bible')
              : view === 'chapters'
              ? selectedBook?.name
              : `${selectedBook?.name} ${selectedChapter}`}
          </Text>
          <Text style={styles.headerSubtitle}>{languages[currentLanguage]?.flag} {languages[currentLanguage]?.name}</Text>
        </View>
        {view === 'reading' && (
          <TouchableOpacity style={styles.speakButton} onPress={handleSpeak}>
            <Ionicons
              name={isSpeaking ? 'stop' : 'volume-high'}
              size={24}
              color={COLORS.primary}
            />
          </TouchableOpacity>
        )}
        {view === 'books' && (
          <TouchableOpacity
            style={styles.langButton}
            onPress={() => setShowLanguageSelector(true)}
          >
            <Text style={styles.langButtonText}>{languages[currentLanguage]?.flag}</Text>
          </TouchableOpacity>
        )}
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

      {/* Language Selector for Translation Target */}
      <LanguageSelector
        visible={showLanguageSelector}
        onClose={() => {
          setShowLanguageSelector(false);
          if (view === 'books') {
            loadBooks();
          }
        }}
      />
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
  },
  backButton: {
    padding: SPACING.sm,
    marginRight: SPACING.sm,
  },
  headerTitleContainer: {
    flex: 1,
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
  speakButton: {
    padding: SPACING.sm,
  },
  langButton: {
    padding: SPACING.sm,
  },
  langButtonText: {
    fontSize: 24,
  },
  listContent: {
    padding: SPACING.md,
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
  translationBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.card,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.lg,
  },
  translateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    padding: SPACING.sm,
  },
  translateText: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '500',
  },
  langSelectButton: {
    padding: SPACING.sm,
  },
  langFlag: {
    fontSize: 24,
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
    minWidth: 20,
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
});
