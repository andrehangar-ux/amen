import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { MoodSelector } from '../src/components/MoodSelector';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

export default function MoodCheckinScreen() {
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleCheckin = async () => {
    if (!selectedMood) return;
    
    setLoading(true);
    try {
      const data = await api.moodCheckin(selectedMood);
      setResult(data);
    } catch (error) {
      console.log('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
            <Ionicons name="close" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>La Tua Parola</Text>
          <View style={{ width: 40 }} />
        </View>

        <View style={styles.resultContainer}>
          <View style={styles.verseCard}>
            <Text style={styles.verseRef}>{result.verse?.ref}</Text>
            <Text style={styles.verseText}>"{result.verse?.text}"</Text>
          </View>

          <View style={styles.reflectionCard}>
            <View style={styles.reflectionHeader}>
              <Ionicons name="sparkles" size={20} color={COLORS.accent} />
              <Text style={styles.reflectionTitle}>Riflessione per Te</Text>
            </View>
            <Text style={styles.reflectionText}>{result.reflection}</Text>
          </View>

          <TouchableOpacity
            style={styles.doneButton}
            onPress={() => router.back()}
          >
            <Text style={styles.doneButtonText}>Continua il Tuo Giorno</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
          <Ionicons name="close" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Come Ti Senti?</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={styles.content}>
        <Text style={styles.subtitle}>
          Seleziona il tuo stato d'animo per ricevere una parola personalizzata
        </Text>

        <MoodSelector
          selectedMood={selectedMood}
          onSelect={setSelectedMood}
        />

        <TouchableOpacity
          style={[
            styles.submitButton,
            !selectedMood && styles.submitButtonDisabled,
          ]}
          onPress={handleCheckin}
          disabled={!selectedMood || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>Ricevi la Tua Parola</Text>
          )}
        </TouchableOpacity>
      </View>
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
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  closeButton: {
    padding: SPACING.sm,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  content: {
    flex: 1,
    padding: SPACING.lg,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: SPACING.xl,
    lineHeight: 24,
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
    marginTop: SPACING.xl,
  },
  submitButtonDisabled: {
    backgroundColor: COLORS.textMuted,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultContainer: {
    flex: 1,
    padding: SPACING.lg,
    justifyContent: 'center',
  },
  verseCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.xl,
    marginBottom: SPACING.lg,
    ...SHADOWS.medium,
  },
  verseRef: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  verseText: {
    fontSize: 20,
    fontStyle: 'italic',
    color: COLORS.text,
    lineHeight: 32,
  },
  reflectionCard: {
    backgroundColor: COLORS.accent + '15',
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    marginBottom: SPACING.xl,
  },
  reflectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
    gap: SPACING.sm,
  },
  reflectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.accent,
  },
  reflectionText: {
    fontSize: 15,
    color: COLORS.text,
    lineHeight: 24,
  },
  doneButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    alignItems: 'center',
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
