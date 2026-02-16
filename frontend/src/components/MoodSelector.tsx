import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { COLORS, SPACING, BORDER_RADIUS, MOODS } from '../utils/theme';
import { useTranslation } from '../store/languageStore';

interface MoodSelectorProps {
  selectedMood: string | null;
  onSelect: (mood: string) => void;
  horizontal?: boolean;
}

export const MoodSelector: React.FC<MoodSelectorProps> = ({ 
  selectedMood, 
  onSelect,
  horizontal = false 
}) => {
  const { t } = useTranslation();

  if (horizontal) {
    return (
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.horizontalContainer}
      >
        {MOODS.map((mood) => (
          <TouchableOpacity
            key={mood.key}
            style={[
              styles.moodButtonHorizontal,
              selectedMood === mood.key && { backgroundColor: mood.color + '30', borderColor: mood.color },
            ]}
            onPress={() => onSelect(mood.key)}
            data-testid={`mood-${mood.key}`}
          >
            <Text style={styles.moodEmoji}>{mood.emoji}</Text>
            <Text style={[
              styles.moodLabel,
              selectedMood === mood.key && { color: COLORS.text }
            ]}>
              {t(mood.labelKey)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  return (
    <View style={styles.gridContainer}>
      {MOODS.map((mood) => (
        <TouchableOpacity
          key={mood.key}
          style={[
            styles.moodButton,
            selectedMood === mood.key && { backgroundColor: mood.color + '30', borderColor: mood.color },
          ]}
          onPress={() => onSelect(mood.key)}
          data-testid={`mood-${mood.key}`}
        >
          <Text style={styles.moodEmoji}>{mood.emoji}</Text>
          <Text style={[
            styles.moodLabel,
            selectedMood === mood.key && { color: COLORS.text }
          ]}>
            {t(mood.labelKey)}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: SPACING.sm,
  },
  horizontalContainer: {
    paddingHorizontal: SPACING.md,
    gap: SPACING.sm,
  },
  moodButton: {
    width: '23%',
    aspectRatio: 1,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: COLORS.border,
  },
  moodButtonHorizontal: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: COLORS.border,
    minWidth: 80,
  },
  moodEmoji: {
    fontSize: 28,
    marginBottom: SPACING.xs,
  },
  moodLabel: {
    fontSize: 12,
    color: COLORS.textLight,
    fontWeight: '500',
  },
});
