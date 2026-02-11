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
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import { router } from 'expo-router';
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

interface CrossRef {
  ref: string;
  text: string;
}

interface StudyData {
  cross_references: Record<string, CrossRef[]>;
  dictionary_links: Record<string, string[]>;
  study_context: {
    historical_context: string;
    literary_structure: string;
    key_themes: string[];
    application: string;
  } | null;
  user_notes: any[];
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

  // Study Tools State
  const [showStudyTools, setShowStudyTools] = useState(false);
  const [studyData, setStudyData] = useState<StudyData | null>(null);
  const [loadingStudy, setLoadingStudy] = useState(false);
  const [selectedVerse, setSelectedVerse] = useState<Verse | null>(null);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [loadingAI, setLoadingAI] = useState(false);

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
      // Load study data
      loadStudyData(book, chapter);
    } catch (error) {
      console.log('Error loading chapter:', error);
      setVerses([]);
    } finally {
      setLoading(false);
    }
  };

  const loadStudyData = async (book: string, chapter: number) => {
    setLoadingStudy(true);
    try {
      const data = await api.getStudyData(book, chapter);
      setStudyData(data);
    } catch (error) {
      console.log('Error loading study data:', error);
      setStudyData(null);
    } finally {
      setLoadingStudy(false);
    }
  };

  const handleVersePress = (verse: Verse) => {
    setSelectedVerse(verse);
    setShowStudyTools(true);
  };

  const saveNote = async () => {
    if (!selectedBook || !selectedChapter || !noteText.trim()) return;
    
    try {
      await api.createStudyNote(
        selectedBook.name,
        selectedChapter,
        selectedVerse?.verse || null,
        noteText,
        null,
        []
      );
      Alert.alert('Salvato!', 'Nota aggiunta con successo');
      setNoteText('');
      setShowNoteModal(false);
      // Reload study data
      loadStudyData(selectedBook.name, selectedChapter);
    } catch (error) {
      Alert.alert('Errore', 'Impossibile salvare la nota');
    }
  };

  const askAIAboutVerse = async () => {
    if (!selectedVerse || !selectedBook) return;
    
    setLoadingAI(true);
    try {
      const response = await api.aiExplainVerse(
        `${selectedBook.name} ${selectedChapter}:${selectedVerse.verse}`,
        selectedVerse.text,
        aiQuestion || 'Spiega questo versetto'
      );
      setAiAnswer(response.explanation);
    } catch (error) {
      Alert.alert('Errore', 'Impossibile ottenere la spiegazione');
    } finally {
      setLoadingAI(false);
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
        key="books-list"
        data={books}
        keyExtractor={(item, index) => `book-${item.abbrev}-${index}`}
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

  const renderReading = () => {
    const verseKey = selectedBook && selectedChapter ? `${selectedBook.name}:${selectedChapter}` : '';
    const crossRefs = studyData?.cross_references || {};
    const dictLinks = studyData?.dictionary_links || {};
    
    return (
      <ScrollView contentContainerStyle={styles.readingContent}>
        {/* Study Context Banner */}
        {studyData?.study_context && (
          <TouchableOpacity 
            style={styles.studyContextBanner}
            onPress={() => setShowStudyTools(true)}
          >
            <Ionicons name="school" size={20} color={COLORS.primary} />
            <Text style={styles.studyContextText}>Contesto di studio disponibile</Text>
            <Ionicons name="chevron-forward" size={20} color={COLORS.primary} />
          </TouchableOpacity>
        )}

        {/* Verses */}
        {verses.map((verse) => {
          const fullVerseKey = `${verseKey}:${verse.verse}`;
          const hasRefs = crossRefs[fullVerseKey];
          const hasDict = dictLinks[fullVerseKey];
          const hasStudyData = hasRefs || hasDict;
          
          return (
            <TouchableOpacity 
              key={verse.verse} 
              style={[styles.verseContainer, hasStudyData && styles.verseWithStudy]}
              onPress={() => handleVersePress(verse)}
              activeOpacity={0.7}
            >
              <Text style={styles.verseNumber}>{verse.verse}</Text>
              <View style={styles.verseContent}>
                <Text style={styles.verseText}>{verse.text}</Text>
                {hasStudyData && (
                  <View style={styles.verseIndicators}>
                    {hasRefs && (
                      <View style={styles.indicator}>
                        <Ionicons name="link" size={14} color={COLORS.primary} />
                        <Text style={styles.indicatorText}>{hasRefs.length}</Text>
                      </View>
                    )}
                    {hasDict && (
                      <View style={styles.indicator}>
                        <Ionicons name="language" size={14} color={COLORS.accent} />
                      </View>
                    )}
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {/* User Notes Section */}
        {studyData?.user_notes && studyData.user_notes.length > 0 && (
          <View style={styles.notesSection}>
            <Text style={styles.notesSectionTitle}>I tuoi appunti</Text>
            {studyData.user_notes.map((note: any, idx: number) => (
              <View key={idx} style={styles.noteCard}>
                {note.verse && <Text style={styles.noteVerse}>v. {note.verse}</Text>}
                <Text style={styles.noteText}>{note.note}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Add Note Button */}
        <TouchableOpacity 
          style={styles.addNoteButton}
          onPress={() => { setSelectedVerse(null); setShowNoteModal(true); }}
        >
          <Ionicons name="add-circle" size={20} color={COLORS.primary} />
          <Text style={styles.addNoteText}>Aggiungi nota al capitolo</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  };

  // Study Tools Modal
  const renderStudyToolsModal = () => {
    if (!selectedBook || !selectedChapter) return null;
    
    const verseKey = selectedVerse 
      ? `${selectedBook.name}:${selectedChapter}:${selectedVerse.verse}`
      : `${selectedBook.name}:${selectedChapter}`;
    const crossRefs = studyData?.cross_references?.[verseKey] || [];
    const dictTerms = studyData?.dictionary_links?.[verseKey] || [];
    const context = studyData?.study_context;

    return (
      <Modal
        visible={showStudyTools}
        animationType="slide"
        transparent
        onRequestClose={() => setShowStudyTools(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.studyModal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {selectedVerse 
                  ? `Studio: ${selectedBook.name} ${selectedChapter}:${selectedVerse.verse}`
                  : `Studio: ${selectedBook.name} ${selectedChapter}`
                }
              </Text>
              <TouchableOpacity onPress={() => setShowStudyTools(false)}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.studyContent}>
              {selectedVerse && (
                <View style={styles.selectedVerseBox}>
                  <Text style={styles.selectedVerseText}>{selectedVerse.text}</Text>
                </View>
              )}

              {/* Action Buttons */}
              <View style={styles.studyActions}>
                <TouchableOpacity 
                  style={styles.studyActionBtn}
                  onPress={() => { setShowStudyTools(false); setShowNoteModal(true); }}
                >
                  <Ionicons name="create" size={22} color={COLORS.primary} />
                  <Text style={styles.studyActionText}>Nota</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.studyActionBtn}
                  onPress={() => { setShowStudyTools(false); setShowAIModal(true); }}
                >
                  <Ionicons name="bulb" size={22} color={COLORS.accent} />
                  <Text style={styles.studyActionText}>AI Spiega</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.studyActionBtn}
                  onPress={() => router.push('/dictionary')}
                >
                  <Ionicons name="book" size={22} color="#9B59B6" />
                  <Text style={styles.studyActionText}>Dizionario</Text>
                </TouchableOpacity>
              </View>

              {/* Cross References */}
              {crossRefs.length > 0 && (
                <View style={styles.studySection}>
                  <Text style={styles.studySectionTitle}>
                    <Ionicons name="link" size={16} color={COLORS.primary} /> Riferimenti Incrociati
                  </Text>
                  {crossRefs.map((ref: any, idx: number) => (
                    <View key={idx} style={styles.crossRefCard}>
                      <Text style={styles.crossRefRef}>{ref.ref}</Text>
                      <Text style={styles.crossRefText}>{ref.text}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Dictionary Links */}
              {dictTerms.length > 0 && (
                <View style={styles.studySection}>
                  <Text style={styles.studySectionTitle}>
                    <Ionicons name="language" size={16} color={COLORS.accent} /> Termini nel Dizionario
                  </Text>
                  <View style={styles.dictTermsRow}>
                    {dictTerms.map((term: string, idx: number) => (
                      <TouchableOpacity 
                        key={idx} 
                        style={styles.dictTermChip}
                        onPress={() => router.push('/dictionary')}
                      >
                        <Text style={styles.dictTermText}>{term}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Historical Context */}
              {context && (
                <View style={styles.studySection}>
                  <Text style={styles.studySectionTitle}>
                    <Ionicons name="time" size={16} color="#E67E22" /> Contesto Storico
                  </Text>
                  <Text style={styles.contextText}>{context.historical_context}</Text>
                  
                  <Text style={styles.studySubtitle}>Struttura Letteraria</Text>
                  <Text style={styles.contextText}>{context.literary_structure}</Text>
                  
                  <Text style={styles.studySubtitle}>Temi Chiave</Text>
                  <View style={styles.themesRow}>
                    {context.key_themes.map((theme: string, idx: number) => (
                      <View key={idx} style={styles.themeChip}>
                        <Text style={styles.themeText}>{theme}</Text>
                      </View>
                    ))}
                  </View>
                  
                  <Text style={styles.studySubtitle}>Applicazione</Text>
                  <Text style={styles.contextText}>{context.application}</Text>
                </View>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    );
  };

  // Note Modal
  const renderNoteModal = () => (
    <Modal
      visible={showNoteModal}
      animationType="slide"
      transparent
      onRequestClose={() => setShowNoteModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.noteModal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {selectedVerse 
                ? `Nota: v.${selectedVerse.verse}`
                : 'Nota al Capitolo'
              }
            </Text>
            <TouchableOpacity onPress={() => setShowNoteModal(false)}>
              <Ionicons name="close" size={24} color={COLORS.text} />
            </TouchableOpacity>
          </View>
          
          <TextInput
            style={styles.noteInput}
            placeholder="Scrivi i tuoi appunti..."
            placeholderTextColor={COLORS.textMuted}
            multiline
            value={noteText}
            onChangeText={setNoteText}
          />
          
          <TouchableOpacity style={styles.saveNoteBtn} onPress={saveNote}>
            <Text style={styles.saveNoteBtnText}>Salva Nota</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  // AI Explain Modal
  const renderAIModal = () => (
    <Modal
      visible={showAIModal}
      animationType="slide"
      transparent
      onRequestClose={() => { setShowAIModal(false); setAiAnswer(''); }}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.aiModal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>AI Spiegazione</Text>
            <TouchableOpacity onPress={() => { setShowAIModal(false); setAiAnswer(''); }}>
              <Ionicons name="close" size={24} color={COLORS.text} />
            </TouchableOpacity>
          </View>
          
          {selectedVerse && (
            <View style={styles.aiVerseBox}>
              <Text style={styles.aiVerseRef}>{selectedBook?.name} {selectedChapter}:{selectedVerse.verse}</Text>
              <Text style={styles.aiVerseText}>{selectedVerse.text}</Text>
            </View>
          )}
          
          <TextInput
            style={styles.aiQuestionInput}
            placeholder="Fai una domanda specifica (opzionale)..."
            placeholderTextColor={COLORS.textMuted}
            value={aiQuestion}
            onChangeText={setAiQuestion}
          />
          
          <TouchableOpacity 
            style={[styles.aiAskBtn, loadingAI && styles.btnDisabled]} 
            onPress={askAIAboutVerse}
            disabled={loadingAI}
          >
            {loadingAI ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.aiAskBtnText}>Chiedi all'AI</Text>
            )}
          </TouchableOpacity>
          
          {aiAnswer && (
            <ScrollView style={styles.aiAnswerScroll}>
              <Text style={styles.aiAnswerText}>{aiAnswer}</Text>
            </ScrollView>
          )}
        </View>
      </View>
    </Modal>
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
  // Study Tools Styles
  studyContextBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '15',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.md,
  },
  studyContextText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
    marginLeft: SPACING.sm,
  },
  verseWithStudy: {
    backgroundColor: COLORS.primary + '08',
    borderRadius: BORDER_RADIUS.sm,
    marginHorizontal: -SPACING.xs,
    paddingHorizontal: SPACING.xs,
  },
  verseContent: {
    flex: 1,
  },
  verseIndicators: {
    flexDirection: 'row',
    marginTop: SPACING.xs,
  },
  indicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  indicatorText: {
    fontSize: 12,
    color: COLORS.primary,
    marginLeft: 2,
  },
  notesSection: {
    marginTop: SPACING.lg,
    paddingTop: SPACING.lg,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  notesSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  noteCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
  },
  noteVerse: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 4,
  },
  noteText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  addNoteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.md,
    marginTop: SPACING.lg,
  },
  addNoteText: {
    fontSize: 14,
    color: COLORS.primary,
    marginLeft: SPACING.sm,
  },
  // Study Modal
  studyModal: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    maxHeight: '90%',
  },
  studyContent: {
    padding: SPACING.md,
  },
  selectedVerseBox: {
    backgroundColor: COLORS.primary + '15',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.md,
  },
  selectedVerseText: {
    fontSize: 15,
    color: COLORS.text,
    fontStyle: 'italic',
    lineHeight: 22,
  },
  studyActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: SPACING.lg,
    paddingBottom: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  studyActionBtn: {
    alignItems: 'center',
    padding: SPACING.sm,
  },
  studyActionText: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 4,
  },
  studySection: {
    marginBottom: SPACING.lg,
  },
  studySectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  studySubtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textLight,
    marginTop: SPACING.md,
    marginBottom: SPACING.xs,
  },
  crossRefCard: {
    backgroundColor: COLORS.background,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  crossRefRef: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 4,
  },
  crossRefText: {
    fontSize: 14,
    color: COLORS.text,
    fontStyle: 'italic',
  },
  dictTermsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  dictTermChip: {
    backgroundColor: COLORS.accent + '20',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: BORDER_RADIUS.full,
    marginRight: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  dictTermText: {
    fontSize: 13,
    color: COLORS.accent,
    fontWeight: '600',
  },
  contextText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
  },
  themesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: SPACING.xs,
  },
  themeChip: {
    backgroundColor: COLORS.primary + '15',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: BORDER_RADIUS.sm,
    marginRight: SPACING.xs,
    marginBottom: SPACING.xs,
  },
  themeText: {
    fontSize: 12,
    color: COLORS.primary,
  },
  // Note Modal
  noteModal: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    padding: SPACING.md,
  },
  noteInput: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 15,
    color: COLORS.text,
    minHeight: 120,
    textAlignVertical: 'top',
    marginVertical: SPACING.md,
  },
  saveNoteBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  saveNoteBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // AI Modal
  aiModal: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    padding: SPACING.md,
    maxHeight: '90%',
  },
  aiVerseBox: {
    backgroundColor: COLORS.primary + '10',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginVertical: SPACING.md,
  },
  aiVerseRef: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 4,
  },
  aiVerseText: {
    fontSize: 14,
    color: COLORS.text,
    fontStyle: 'italic',
  },
  aiQuestionInput: {
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 15,
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  aiAskBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
  },
  aiAskBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  btnDisabled: {
    opacity: 0.6,
  },
  aiAnswerScroll: {
    maxHeight: 300,
    marginTop: SPACING.md,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
  },
  aiAnswerText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
  },
});
