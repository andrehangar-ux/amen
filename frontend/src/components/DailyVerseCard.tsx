import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../utils/theme';

interface DailyVerseCardProps {
  reference: string;
  text: string;
  onSpeak?: () => void;
  onShare?: () => void;
  onBookmark?: () => void;
}

export const DailyVerseCard: React.FC<DailyVerseCardProps> = ({
  reference,
  text,
  onSpeak,
  onShare,
  onBookmark,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.badge}>
          <Ionicons name="sunny" size={16} color={COLORS.accent} />
          <Text style={styles.badgeText}>Versetto del Giorno</Text>
        </View>
      </View>
      
      <Text style={styles.verseText}>"{text}"</Text>
      <Text style={styles.reference}>— {reference}</Text>
      
      <View style={styles.actions}>
        {onSpeak && (
          <TouchableOpacity style={styles.actionButton} onPress={onSpeak}>
            <Ionicons name="volume-high-outline" size={22} color={COLORS.primary} />
          </TouchableOpacity>
        )}
        {onBookmark && (
          <TouchableOpacity style={styles.actionButton} onPress={onBookmark}>
            <Ionicons name="bookmark-outline" size={22} color={COLORS.primary} />
          </TouchableOpacity>
        )}
        {onShare && (
          <TouchableOpacity style={styles.actionButton} onPress={onShare}>
            <Ionicons name="share-outline" size={22} color={COLORS.primary} />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    ...SHADOWS.medium,
  },
  header: {
    marginBottom: SPACING.md,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accent + '20',
    alignSelf: 'flex-start',
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
    borderRadius: BORDER_RADIUS.full,
  },
  badgeText: {
    fontSize: 12,
    color: COLORS.accent,
    fontWeight: '600',
    marginLeft: SPACING.xs,
  },
  verseText: {
    fontSize: 18,
    color: COLORS.text,
    lineHeight: 28,
    fontStyle: 'italic',
    marginBottom: SPACING.md,
  },
  reference: {
    fontSize: 14,
    color: COLORS.primary,
    fontWeight: '600',
    marginBottom: SPACING.md,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: SPACING.md,
  },
  actionButton: {
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.secondary,
  },
});
