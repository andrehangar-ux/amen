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
  
  // Interactive Features State
  const [highlightedVerses, setHighlightedVerses] = useState<Set<number>>(new Set());
  const [bookmarkedVerses, setBookmarkedVerses] = useState<Set<string>>(new Set());
  const [fontSize, setFontSize] = useState(16);
  const [showFontSettings, setShowFontSettings] = useState(false);
  const [showTutorial, setShowTutorial] = useState(false);
  const [showEditionModal, setShowEditionModal] = useState(false);

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

  const loadChapter = async (book: string, chapter: number, lang?: string) => {
    const languageToUse = lang || currentLanguage;
    setLoading(true);
    try {
      const data = await api.getChapter(book, chapter, languageToUse);
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

  // Toggle highlight for a verse
  const toggleHighlight = (verseNum: number) => {
    setHighlightedVerses(prev => {
      const newSet = new Set(prev);
      if (newSet.has(verseNum)) {
        newSet.delete(verseNum);
      } else {
        newSet.add(verseNum);
      }
      return newSet;
    });
  };

  // Toggle bookmark for a verse
  const toggleBookmark = (verseRef: string) => {
    setBookmarkedVerses(prev => {
      const newSet = new Set(prev);
      if (newSet.has(verseRef)) {
        newSet.delete(verseRef);
      } else {
        newSet.add(verseRef);
      }
      return newSet;
    });
  };

  // Share verse
  const shareVerse = async (verse: Verse) => {
    if (!selectedBook || !selectedChapter) return;
    const text = `"${verse.text}"\n\n- ${selectedBook.name} ${selectedChapter}:${verse.verse}`;
    try {
      const { Share } = await import('react-native');
      await Share.share({ message: text, title: 'Versetto dalla Bibbia' });
    } catch (error) {
      Alert.alert('Errore', 'Impossibile condividere');
    }
  };

  // Open Wikipedia for biblical terms
  const openWikipedia = (term: string) => {
    const url = `https://it.wikipedia.org/wiki/${encodeURIComponent(term)}`;
    import('expo-linking').then(Linking => Linking.openURL(url));
  };

  // Open Maps for biblical locations
  const openMaps = () => {
    router.push('/maps');
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
        aiQuestion || undefined,
        currentLanguage  // Pass current language to API
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
      // Update language and immediately reload content
      setLanguage(edition.language).then(() => {
        loadBooks();
        if (selectedBook && selectedChapter && view === 'reading') {
          loadChapter(selectedBook.name, selectedChapter);
        }
      });
    }
    setShowEditionSelector(false);
  };

  const handleLanguageSelect = async (lang: string) => {
    // Set language and close modal first for immediate feedback
    setShowLanguageModal(false);
    await setLanguage(lang);
    
    // Reload content with new language
    await loadBooks();
    
    // Ricarica il capitolo corrente con la nuova lingua
    if (selectedBook && selectedChapter && view === 'reading') {
      loadChapter(selectedBook.name, selectedChapter);
    }
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

  // Get current Bible edition name based on language
  const getCurrentEditionName = () => {
    const editionNames: { [key: string]: string } = {
      'it': 'Nuova Diodati',
      'es': 'Reina Valera 1960',
      'en': 'King James Version',
      'de': 'Luther Bibel',
      'fr': 'Louis Segond',
      'pt': 'Almeida Revista'
    };
    return editionNames[currentLanguage] || 'Bibbia';
  };

  const renderReading = () => {
    const verseKey = selectedBook && selectedChapter ? `${selectedBook.name}:${selectedChapter}` : '';
    const crossRefs = studyData?.cross_references || {};
    const dictLinks = studyData?.dictionary_links || {};
    
    const languageFlags: { [key: string]: string } = {
      'it': '🇮🇹',
      'es': '🇪🇸', 
      'en': '🇬🇧',
      'de': '🇩🇪',
      'fr': '🇫🇷',
      'pt': '🇧🇷'
    };
    
    const availableLanguages = ['it', 'es', 'en', 'de', 'fr', 'pt'];
    
    return (
      <View style={styles.readingContainer}>
        {/* Current Edition Banner */}
        <View style={styles.editionBanner}>
          <Ionicons name="book-outline" size={16} color={COLORS.primary} />
          <Text style={styles.editionBannerText}>
            {getCurrentEditionName()} • {selectedBook?.name} {selectedChapter}
          </Text>
        </View>

        {/* Language Quick Switch Bar */}
        <View style={styles.languageBar}>
          {availableLanguages.map((lang) => (
            <TouchableOpacity
              key={lang}
              style={[
                styles.langButton,
                currentLanguage === lang && styles.langButtonActive
              ]}
              onPress={() => handleLanguageSelect(lang)}
            >
              <Text style={styles.langButtonFlag}>{languageFlags[lang]}</Text>
              <Text style={[
                styles.langButtonText,
                currentLanguage === lang && styles.langButtonTextActive
              ]}>
                {lang.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Reading Toolbar */}
        <View style={styles.readingToolbar}>
          <TouchableOpacity 
            style={styles.toolbarButton}
            onPress={() => setShowEditionModal(true)}
          >
            <Ionicons name="swap-horizontal" size={20} color={COLORS.accent} />
            <Text style={styles.toolbarButtonText}>Edizioni</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.toolbarButton}
            onPress={() => {
              const newSize = fontSize >= 24 ? 14 : fontSize + 2;
              setFontSize(newSize);
            }}
          >
            <Ionicons name="text" size={20} color={COLORS.textLight} />
            <Text style={styles.toolbarButtonText}>A{fontSize}</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.toolbarButton}
            onPress={() => setShowTutorial(true)}
          >
            <Ionicons name="help-circle" size={20} color="#9B59B6" />
            <Text style={styles.toolbarButtonText}>Aiuto</Text>
          </TouchableOpacity>
        </View>

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
            const isHighlighted = highlightedVerses.has(verse.verse);
            const isBookmarked = bookmarkedVerses.has(fullVerseKey);
            
            return (
              <TouchableOpacity 
                key={verse.verse} 
                style={[
                  styles.verseContainer, 
                  hasStudyData && styles.verseWithStudy,
                  isHighlighted && styles.verseHighlighted
                ]}
                onPress={() => handleVersePress(verse)}
                activeOpacity={0.7}
              >
                <View style={styles.verseNumberContainer}>
                  <Text style={styles.verseNumber}>{verse.verse}</Text>
                {isBookmarked && (
                  <Ionicons name="bookmark" size={12} color="#E74C3C" style={styles.bookmarkIcon} />
                )}
              </View>
              <View style={styles.verseContent}>
                <Text style={[styles.verseText, { fontSize }]}>{verse.text}</Text>
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
      </View>
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

              {/* Action Buttons - Prima Riga */}
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

              {/* Action Buttons - Seconda Riga (Nuovi Tool) */}
              <View style={styles.studyActions}>
                {selectedVerse && (
                  <>
                    <TouchableOpacity 
                      style={[styles.studyActionBtn, highlightedVerses.has(selectedVerse.verse) && styles.studyActionActive]}
                      onPress={() => { toggleHighlight(selectedVerse.verse); }}
                    >
                      <Ionicons 
                        name={highlightedVerses.has(selectedVerse.verse) ? "color-fill" : "color-fill-outline"} 
                        size={22} 
                        color="#F1C40F" 
                      />
                      <Text style={styles.studyActionText}>Evidenzia</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={styles.studyActionBtn}
                      onPress={() => { shareVerse(selectedVerse); setShowStudyTools(false); }}
                    >
                      <Ionicons name="share-social" size={22} color="#2ECC71" />
                      <Text style={styles.studyActionText}>Condividi</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.studyActionBtn, bookmarkedVerses.has(`${selectedBook?.name}:${selectedChapter}:${selectedVerse.verse}`) && styles.studyActionActive]}
                      onPress={() => { 
                        if (selectedBook && selectedChapter) {
                          toggleBookmark(`${selectedBook.name}:${selectedChapter}:${selectedVerse.verse}`);
                        }
                      }}
                    >
                      <Ionicons 
                        name={bookmarkedVerses.has(`${selectedBook?.name}:${selectedChapter}:${selectedVerse.verse}`) ? "bookmark" : "bookmark-outline"} 
                        size={22} 
                        color="#E74C3C" 
                      />
                      <Text style={styles.studyActionText}>Segnalibro</Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>

              {/* Action Buttons - Terza Riga (Link Esterni) */}
              <View style={styles.studyActions}>
                <TouchableOpacity 
                  style={styles.studyActionBtn}
                  onPress={() => router.push('/maps')}
                >
                  <Ionicons name="map" size={22} color="#3498DB" />
                  <Text style={styles.studyActionText}>Mappe</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.studyActionBtn}
                  onPress={() => openWikipedia(selectedBook?.name || 'Bibbia')}
                >
                  <Ionicons name="globe" size={22} color="#95A5A6" />
                  <Text style={styles.studyActionText}>Wikipedia</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.studyActionBtn}
                  onPress={() => {
                    const url = `https://www.laparola.net/testo.php?riferimento=${encodeURIComponent(selectedBook?.name + ' ' + selectedChapter)}`;
                    import('expo-linking').then(Linking => Linking.openURL(url));
                  }}
                >
                  <Ionicons name="open" size={22} color="#1ABC9C" />
                  <Text style={styles.studyActionText}>LaParola</Text>
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

  // Tutorial Modal for new users
  const renderTutorialModal = () => (
    <Modal
      visible={showTutorial}
      animationType="fade"
      transparent
      onRequestClose={() => setShowTutorial(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.tutorialModal}>
          <ScrollView>
            <View style={styles.tutorialHeader}>
              <Ionicons name="help-circle" size={50} color={COLORS.primary} />
              <Text style={styles.tutorialTitle}>Guida alla Lettura</Text>
            </View>

            <View style={styles.tutorialStep}>
              <View style={styles.tutorialStepNumber}>
                <Text style={styles.tutorialStepNumberText}>1</Text>
              </View>
              <View style={styles.tutorialStepContent}>
                <Text style={styles.tutorialStepTitle}>🌐 Cambia Lingua</Text>
                <Text style={styles.tutorialStepText}>
                  Tocca le bandiere in alto (🇮🇹 🇪🇸 🇬🇧 🇩🇪 🇫🇷) per cambiare la lingua della Bibbia in qualsiasi momento.
                </Text>
              </View>
            </View>

            <View style={styles.tutorialStep}>
              <View style={styles.tutorialStepNumber}>
                <Text style={styles.tutorialStepNumberText}>2</Text>
              </View>
              <View style={styles.tutorialStepContent}>
                <Text style={styles.tutorialStepTitle}>📖 Traduzioni Bibliche</Text>
                <Text style={styles.tutorialStepText}>
                  Il banner in alto mostra quale traduzione stai leggendo:{'\n'}
                  • Italiano: Nuova Diodati{'\n'}
                  • Spagnolo: Reina Valera 1960{'\n'}
                  • Inglese: King James Version{'\n'}
                  • Tedesco: Luther Bibel{'\n'}
                  • Francese: Louis Segond
                </Text>
              </View>
            </View>

            <View style={styles.tutorialStep}>
              <View style={styles.tutorialStepNumber}>
                <Text style={styles.tutorialStepNumberText}>3</Text>
              </View>
              <View style={styles.tutorialStepContent}>
                <Text style={styles.tutorialStepTitle}>👆 Tocca un Versetto</Text>
                <Text style={styles.tutorialStepText}>
                  Tocca qualsiasi versetto per aprire gli strumenti di studio:{'\n'}
                  • Aggiungi note personali{'\n'}
                  • Chiedi spiegazione all'AI{'\n'}
                  • Evidenzia il versetto{'\n'}
                  • Condividi con amici{'\n'}
                  • Salva nei segnalibri
                </Text>
              </View>
            </View>

            <View style={styles.tutorialStep}>
              <View style={styles.tutorialStepNumber}>
                <Text style={styles.tutorialStepNumberText}>4</Text>
              </View>
              <View style={styles.tutorialStepContent}>
                <Text style={styles.tutorialStepTitle}>🔤 Dimensione Testo</Text>
                <Text style={styles.tutorialStepText}>
                  Tocca "A16" per aumentare la dimensione del testo. Continua a toccare per tornare alla dimensione minima.
                </Text>
              </View>
            </View>

            <View style={styles.tutorialStep}>
              <View style={styles.tutorialStepNumber}>
                <Text style={styles.tutorialStepNumberText}>5</Text>
              </View>
              <View style={styles.tutorialStepContent}>
                <Text style={styles.tutorialStepTitle}>🔊 Ascolta</Text>
                <Text style={styles.tutorialStepText}>
                  Tocca l'icona dell'altoparlante in alto a destra per ascoltare la lettura del capitolo.
                </Text>
              </View>
            </View>

            <TouchableOpacity 
              style={styles.tutorialCloseBtn}
              onPress={() => setShowTutorial(false)}
            >
              <Text style={styles.tutorialCloseBtnText}>Ho Capito!</Text>
            </TouchableOpacity>
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
      {renderStudyToolsModal()}
      {renderNoteModal()}
      {renderAIModal()}
      {renderTutorialModal()}
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
  readingContainer: {
    flex: 1,
  },
  readingToolbar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.card,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  toolbarButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.sm,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    gap: 4,
  },
  toolbarButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
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
  verseHighlighted: {
    backgroundColor: 'rgba(241, 196, 15, 0.2)',
    borderRadius: BORDER_RADIUS.sm,
    paddingHorizontal: SPACING.xs,
    marginHorizontal: -SPACING.xs,
  },
  verseNumberContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginRight: SPACING.sm,
    minWidth: 30,
  },
  bookmarkIcon: {
    marginLeft: 2,
    marginTop: 2,
  },
  studyActionActive: {
    backgroundColor: COLORS.primaryLight || 'rgba(52, 152, 219, 0.15)',
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
  // Language Bar Styles
  editionBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.primary + '10',
    gap: 8,
  },
  editionBannerText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
  },
  languageBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.xs,
    backgroundColor: COLORS.card,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    gap: 4,
  },
  langButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.background,
    gap: 4,
  },
  langButtonActive: {
    backgroundColor: COLORS.primary,
  },
  langButtonFlag: {
    fontSize: 16,
  },
  langButtonText: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.textLight,
  },
  langButtonTextActive: {
    color: '#fff',
  },
  // Tutorial Modal Styles
  tutorialModal: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    maxHeight: '85%',
    padding: SPACING.md,
  },
  tutorialHeader: {
    alignItems: 'center',
    paddingVertical: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    marginBottom: SPACING.md,
  },
  tutorialTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.sm,
  },
  tutorialStep: {
    flexDirection: 'row',
    marginBottom: SPACING.lg,
    paddingBottom: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border + '50',
  },
  tutorialStepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  tutorialStepNumberText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  tutorialStepContent: {
    flex: 1,
  },
  tutorialStepTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 4,
  },
  tutorialStepText: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 22,
  },
  tutorialCloseBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.md,
    marginBottom: SPACING.lg,
  },
  tutorialCloseBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
