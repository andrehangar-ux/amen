import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  Alert,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../../src/components/Icon';
import { HamburgerMenu } from '../../src/components/HamburgerMenu';
import { api } from '../../src/utils/api';
import { MoodSelector } from '../../src/components/MoodSelector';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS, MOODS } from '../../src/utils/theme';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

interface JournalEntry {
  entry_id: string;
  content: string;
  mood: string;
  ai_insight: string | null;
  created_at: string;
}

export default function JournalScreen() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [content, setContent] = useState('');
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const loadEntries = useCallback(async () => {
    try {
      const data = await api.getJournalEntries();
      setEntries(data);
    } catch (error) {
      console.log('Error loading entries:', error);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadEntries().finally(() => setLoading(false));
  }, [loadEntries]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadEntries();
    setRefreshing(false);
  };

  const handleSave = async () => {
    if (!content.trim()) {
      Alert.alert('Errore', 'Scrivi qualcosa nel diario');
      return;
    }
    if (!selectedMood) {
      Alert.alert('Errore', 'Seleziona il tuo stato d\'animo');
      return;
    }

    setSaving(true);
    try {
      await api.createJournalEntry(content, selectedMood);
      setContent('');
      setSelectedMood(null);
      setShowForm(false);
      await loadEntries();
      Alert.alert('Salvato', 'La tua voce è stata salvata nel diario');
    } catch (error: any) {
      Alert.alert('Errore', error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    Alert.alert(
      'Elimina',
      'Vuoi eliminare questa voce?',
      [
        { text: 'Annulla', style: 'cancel' },
        {
          text: 'Elimina',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteJournalEntry(entryId);
              await loadEntries();
            } catch (error: any) {
              Alert.alert('Errore', error.message);
            }
          },
        },
      ]
    );
  };

  const getMoodEmoji = (moodKey: string) => {
    const mood = MOODS.find(m => m.key === moodKey);
    return mood?.emoji || '🙂';
  };

  const renderEntry = ({ item }: { item: JournalEntry }) => (
    <View style={styles.entryCard}>
      <View style={styles.entryHeader}>
        <View style={styles.entryMeta}>
          <Text style={styles.entryEmoji}>{getMoodEmoji(item.mood)}</Text>
          <Text style={styles.entryDate}>
            {format(new Date(item.created_at), "d MMMM yyyy, HH:mm", { locale: it })}
          </Text>
        </View>
        <TouchableOpacity onPress={() => handleDelete(item.entry_id)}>
          <Icon name="trash-outline" size={20} color={COLORS.textMuted} />
        </TouchableOpacity>
      </View>
      <Text style={styles.entryContent}>{item.content}</Text>
      {item.ai_insight && (
        <View style={styles.aiInsight}>
          <Icon name="sparkles" size={16} color={COLORS.accent} />
          <Text style={styles.aiInsightText}>{item.ai_insight}</Text>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Il Mio Diario</Text>
          <View style={styles.headerActions}>
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => setShowForm(!showForm)}
            >
              <Icon
                name={showForm ? 'close' : 'add'}
                size={24}
                color="#fff"
              />
            </TouchableOpacity>
            <HamburgerMenu currentScreen="journal" />
          </View>
        </View>

        {/* New Entry Form */}
        {showForm && (
          <View style={styles.formContainer}>
            <Text style={styles.formLabel}>Come ti senti?</Text>
            <MoodSelector
              selectedMood={selectedMood}
              onSelect={setSelectedMood}
            />
            
            <Text style={[styles.formLabel, { marginTop: SPACING.md }]}>I tuoi pensieri</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Scrivi i tuoi pensieri, preghiere, riflessioni..."
              placeholderTextColor={COLORS.textMuted}
              value={content}
              onChangeText={setContent}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
            />
            
            <TouchableOpacity
              style={styles.saveButton}
              onPress={handleSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Icon name="save" size={20} color="#fff" />
                  <Text style={styles.saveButtonText}>Salva nel Diario</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Entries List */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.primary} />
          </View>
        ) : (
          <FlatList
            data={entries}
            keyExtractor={(item) => item.entry_id}
            renderItem={renderEntry}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Icon name="book-outline" size={64} color={COLORS.textMuted} />
                <Text style={styles.emptyText}>Il tuo diario è vuoto</Text>
                <Text style={styles.emptySubtext}>Inizia a scrivere i tuoi pensieri</Text>
              </View>
            }
          />
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
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  formContainer: {
    backgroundColor: COLORS.card,
    margin: SPACING.md,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.lg,
    ...SHADOWS.medium,
  },
  formLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  textInput: {
    backgroundColor: COLORS.secondary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    fontSize: 16,
    color: COLORS.text,
    minHeight: 120,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  saveButton: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SPACING.md,
    gap: SPACING.sm,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  listContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  entryCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  entryMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  entryEmoji: {
    fontSize: 24,
  },
  entryDate: {
    fontSize: 12,
    color: COLORS.textLight,
  },
  entryContent: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 24,
  },
  aiInsight: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: COLORS.accent + '15',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.md,
    gap: SPACING.sm,
  },
  aiInsightText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.textLight,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textLight,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
});
