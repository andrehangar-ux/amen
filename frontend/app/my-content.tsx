import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { useLanguageStore } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface Bookmark {
  bookmark_id: string;
  book: string;
  chapter: number;
  verse: number;
  text: string;
  note?: string;
  highlight_color: string;
  created_at: string;
}

interface StudyNote {
  note_id: string;
  book: string;
  chapter: number;
  verse: number;
  note: string;
  highlight_color?: string;
  created_at: string;
}

type TabType = 'bookmarks' | 'notes' | 'highlights';

export default function MyContentScreen() {
  const { currentLanguage } = useLanguageStore();
  const [activeTab, setActiveTab] = useState<TabType>('bookmarks');
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [notes, setNotes] = useState<StudyNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const translations: Record<string, Record<string, string>> = {
    it: {
      title: 'I Miei Contenuti',
      subtitle: 'Versetti salvati, note e evidenziazioni',
      bookmarks: 'Segnalibri',
      notes: 'Note',
      highlights: 'Evidenziati',
      noBookmarks: 'Nessun versetto salvato',
      noNotes: 'Nessuna nota di studio',
      noHighlights: 'Nessuna evidenziazione',
      addBookmarkHint: 'Tocca il cuore su un versetto per salvarlo',
      addNoteHint: 'Usa gli strumenti di studio per aggiungere note',
      delete: 'Elimina',
      confirmDelete: 'Conferma eliminazione',
      deleteBookmarkMsg: 'Vuoi eliminare questo segnalibro?',
      deleteNoteMsg: 'Vuoi eliminare questa nota?',
      cancel: 'Annulla',
      goToVerse: 'Vai al versetto',
    },
    en: {
      title: 'My Content',
      subtitle: 'Saved verses, notes and highlights',
      bookmarks: 'Bookmarks',
      notes: 'Notes',
      highlights: 'Highlights',
      noBookmarks: 'No saved verses',
      noNotes: 'No study notes',
      noHighlights: 'No highlights',
      addBookmarkHint: 'Tap the heart on a verse to save it',
      addNoteHint: 'Use study tools to add notes',
      delete: 'Delete',
      confirmDelete: 'Confirm deletion',
      deleteBookmarkMsg: 'Do you want to delete this bookmark?',
      deleteNoteMsg: 'Do you want to delete this note?',
      cancel: 'Cancel',
      goToVerse: 'Go to verse',
    },
    es: {
      title: 'Mi Contenido',
      subtitle: 'Versículos guardados, notas y resaltados',
      bookmarks: 'Marcadores',
      notes: 'Notas',
      highlights: 'Resaltados',
      noBookmarks: 'Ningún versículo guardado',
      noNotes: 'Ninguna nota de estudio',
      noHighlights: 'Ningún resaltado',
      addBookmarkHint: 'Toca el corazón en un versículo para guardarlo',
      addNoteHint: 'Usa las herramientas de estudio para añadir notas',
      delete: 'Eliminar',
      confirmDelete: 'Confirmar eliminación',
      deleteBookmarkMsg: '¿Quieres eliminar este marcador?',
      deleteNoteMsg: '¿Quieres eliminar esta nota?',
      cancel: 'Cancelar',
      goToVerse: 'Ir al versículo',
    },
    pt: {
      title: 'Meu Conteúdo',
      subtitle: 'Versículos salvos, notas e destaques',
      bookmarks: 'Marcadores',
      notes: 'Notas',
      highlights: 'Destaques',
      noBookmarks: 'Nenhum versículo salvo',
      noNotes: 'Nenhuma nota de estudo',
      noHighlights: 'Nenhum destaque',
      addBookmarkHint: 'Toque no coração em um versículo para salvá-lo',
      addNoteHint: 'Use as ferramentas de estudo para adicionar notas',
      delete: 'Excluir',
      confirmDelete: 'Confirmar exclusão',
      deleteBookmarkMsg: 'Deseja excluir este marcador?',
      deleteNoteMsg: 'Deseja excluir esta nota?',
      cancel: 'Cancelar',
      goToVerse: 'Ir para o versículo',
    },
    fr: {
      title: 'Mon Contenu',
      subtitle: 'Versets enregistrés, notes et surlignages',
      bookmarks: 'Signets',
      notes: 'Notes',
      highlights: 'Surlignés',
      noBookmarks: 'Aucun verset enregistré',
      noNotes: 'Aucune note d\'étude',
      noHighlights: 'Aucun surlignage',
      addBookmarkHint: 'Appuyez sur le cœur d\'un verset pour l\'enregistrer',
      addNoteHint: 'Utilisez les outils d\'étude pour ajouter des notes',
      delete: 'Supprimer',
      confirmDelete: 'Confirmer la suppression',
      deleteBookmarkMsg: 'Voulez-vous supprimer ce signet?',
      deleteNoteMsg: 'Voulez-vous supprimer cette note?',
      cancel: 'Annuler',
      goToVerse: 'Aller au verset',
    },
    de: {
      title: 'Meine Inhalte',
      subtitle: 'Gespeicherte Verse, Notizen und Markierungen',
      bookmarks: 'Lesezeichen',
      notes: 'Notizen',
      highlights: 'Markierungen',
      noBookmarks: 'Keine gespeicherten Verse',
      noNotes: 'Keine Studiennotizen',
      noHighlights: 'Keine Markierungen',
      addBookmarkHint: 'Tippen Sie auf das Herz eines Verses, um ihn zu speichern',
      addNoteHint: 'Verwenden Sie Studienwerkzeuge, um Notizen hinzuzufügen',
      delete: 'Löschen',
      confirmDelete: 'Löschen bestätigen',
      deleteBookmarkMsg: 'Möchten Sie dieses Lesezeichen löschen?',
      deleteNoteMsg: 'Möchten Sie diese Notiz löschen?',
      cancel: 'Abbrechen',
      goToVerse: 'Zum Vers gehen',
    },
  };

  const t = (key: string) => translations[currentLanguage]?.[key] || translations['it'][key] || key;

  const loadData = useCallback(async () => {
    try {
      const [bookmarksData, notesData] = await Promise.all([
        api.getBookmarks(),
        api.getStudyNotes(),
      ]);
      setBookmarks(bookmarksData || []);
      setNotes(notesData || []);
    } catch (error) {
      console.error('Error loading content:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const deleteBookmark = async (bookmarkId: string) => {
    Alert.alert(
      t('confirmDelete'),
      t('deleteBookmarkMsg'),
      [
        { text: t('cancel'), style: 'cancel' },
        {
          text: t('delete'),
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteBookmark(bookmarkId);
              setBookmarks(prev => prev.filter(b => b.bookmark_id !== bookmarkId));
            } catch (error) {
              console.error('Error deleting bookmark:', error);
            }
          },
        },
      ]
    );
  };

  const deleteNote = async (noteId: string) => {
    Alert.alert(
      t('confirmDelete'),
      t('deleteNoteMsg'),
      [
        { text: t('cancel'), style: 'cancel' },
        {
          text: t('delete'),
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteStudyNote(noteId);
              setNotes(prev => prev.filter(n => n.note_id !== noteId));
            } catch (error) {
              console.error('Error deleting note:', error);
            }
          },
        },
      ]
    );
  };

  const navigateToVerse = (book: string, chapter: number) => {
    router.push({
      pathname: '/(tabs)/bible',
      params: { book, chapter: chapter.toString() }
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(currentLanguage === 'en' ? 'en-US' : currentLanguage + '-' + currentLanguage.toUpperCase());
  };

  const highlights = bookmarks.filter(b => b.highlight_color && b.highlight_color !== '#D4A574');
  const regularBookmarks = bookmarks.filter(b => !b.highlight_color || b.highlight_color === '#D4A574');

  const renderBookmarkItem = (item: Bookmark) => (
    <View 
      key={item.bookmark_id} 
      style={[styles.contentCard, { borderLeftColor: item.highlight_color || COLORS.primary }]}
      data-testid={`bookmark-item-${item.bookmark_id}`}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.verseRef}>{item.book} {item.chapter}:{item.verse}</Text>
        <View style={styles.cardActions}>
          <TouchableOpacity 
            onPress={() => navigateToVerse(item.book, item.chapter)}
            style={styles.actionBtn}
            data-testid={`goto-verse-${item.bookmark_id}`}
          >
            <Icon name="book-open" size={18} color={COLORS.primary} />
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => deleteBookmark(item.bookmark_id)}
            style={styles.actionBtn}
            data-testid={`delete-bookmark-${item.bookmark_id}`}
          >
            <Icon name="trash" size={18} color="#E74C3C" />
          </TouchableOpacity>
        </View>
      </View>
      <Text style={styles.verseText}>"{item.text}"</Text>
      {item.note && (
        <View style={styles.noteContainer}>
          <Icon name="chatbox" size={14} color={COLORS.textSecondary} />
          <Text style={styles.noteText}>{item.note}</Text>
        </View>
      )}
      <Text style={styles.dateText}>{formatDate(item.created_at)}</Text>
    </View>
  );

  const renderNoteItem = (item: StudyNote) => (
    <View 
      key={item.note_id} 
      style={[styles.contentCard, { borderLeftColor: item.highlight_color || COLORS.accent }]}
      data-testid={`note-item-${item.note_id}`}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.verseRef}>{item.book} {item.chapter}:{item.verse}</Text>
        <View style={styles.cardActions}>
          <TouchableOpacity 
            onPress={() => navigateToVerse(item.book, item.chapter)}
            style={styles.actionBtn}
            data-testid={`goto-note-verse-${item.note_id}`}
          >
            <Icon name="book-open" size={18} color={COLORS.primary} />
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => deleteNote(item.note_id)}
            style={styles.actionBtn}
            data-testid={`delete-note-${item.note_id}`}
          >
            <Icon name="trash" size={18} color="#E74C3C" />
          </TouchableOpacity>
        </View>
      </View>
      <Text style={styles.noteContent}>{item.note}</Text>
      <Text style={styles.dateText}>{formatDate(item.created_at)}</Text>
    </View>
  );

  const renderEmptyState = (type: TabType) => {
    const emptyMessages: Record<TabType, { icon: string; text: string; hint: string }> = {
      bookmarks: { icon: 'bookmark', text: t('noBookmarks'), hint: t('addBookmarkHint') },
      notes: { icon: 'document-text', text: t('noNotes'), hint: t('addNoteHint') },
      highlights: { icon: 'color-palette', text: t('noHighlights'), hint: t('addBookmarkHint') },
    };
    const { icon, text, hint } = emptyMessages[type];

    return (
      <View style={styles.emptyState} data-testid={`empty-state-${type}`}>
        <Icon name={icon as any} size={64} color={COLORS.textSecondary} />
        <Text style={styles.emptyText}>{text}</Text>
        <Text style={styles.emptyHint}>{hint}</Text>
      </View>
    );
  };

  const getCurrentContent = () => {
    switch (activeTab) {
      case 'bookmarks':
        return regularBookmarks.length > 0 
          ? regularBookmarks.map(renderBookmarkItem)
          : renderEmptyState('bookmarks');
      case 'notes':
        return notes.length > 0 
          ? notes.map(renderNoteItem)
          : renderEmptyState('notes');
      case 'highlights':
        return highlights.length > 0 
          ? highlights.map(renderBookmarkItem)
          : renderEmptyState('highlights');
    }
  };

  const getTabCount = (tab: TabType) => {
    switch (tab) {
      case 'bookmarks': return regularBookmarks.length;
      case 'notes': return notes.length;
      case 'highlights': return highlights.length;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} data-testid="my-content-screen">
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          onPress={() => router.back()} 
          style={styles.backBtn}
          data-testid="my-content-back-btn"
        >
          <Icon name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.title}>{t('title')}</Text>
          <Text style={styles.subtitle}>{t('subtitle')}</Text>
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        {(['bookmarks', 'notes', 'highlights'] as TabType[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
            data-testid={`tab-${tab}`}
          >
            <Icon 
              name={tab === 'bookmarks' ? 'bookmark' : tab === 'notes' ? 'document-text' : 'color-palette'} 
              size={20} 
              color={activeTab === tab ? COLORS.primary : COLORS.textSecondary} 
            />
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {t(tab)} ({getTabCount(tab)})
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
        }
        showsVerticalScrollIndicator={false}
      >
        {getCurrentContent()}
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
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backBtn: {
    padding: SPACING.sm,
    marginRight: SPACING.md,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  tabsContainer: {
    flexDirection: 'row',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.xs,
    borderRadius: BORDER_RADIUS.md,
    marginHorizontal: 4,
  },
  activeTab: {
    backgroundColor: COLORS.primaryLight,
  },
  tabText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginLeft: 4,
    fontWeight: '500',
  },
  activeTabText: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: SPACING.md,
    paddingBottom: SPACING.xl * 2,
  },
  contentCard: {
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    borderLeftWidth: 4,
    ...SHADOWS.small,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  verseRef: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.primary,
  },
  cardActions: {
    flexDirection: 'row',
    gap: SPACING.sm,
  },
  actionBtn: {
    padding: SPACING.xs,
  },
  verseText: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 22,
    fontStyle: 'italic',
    marginBottom: SPACING.sm,
  },
  noteContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.backgroundAlt,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: SPACING.sm,
  },
  noteText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginLeft: SPACING.xs,
    flex: 1,
  },
  noteContent: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 22,
    marginBottom: SPACING.sm,
  },
  dateText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    textAlign: 'right',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.lg,
  },
  emptyHint: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    textAlign: 'center',
    paddingHorizontal: SPACING.xl,
  },
});
