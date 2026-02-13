import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../src/utils/api';
import { useTranslation } from '../src/store/languageStore';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

interface Radio {
  name: string;
  url: string;
  stream_url: string;
  country: string;
  language: string;
  region: string;
  continent: string;
}

export default function RadioScreen() {
  const { t } = useTranslation();
  
  // Continents with translated names
  const getContinents = () => [
    { id: 'all', name: t('all'), icon: 'globe' },
    { id: 'Europa', name: t('europe'), icon: 'earth' },
    { id: 'SudAmerica', name: t('southAmerica'), icon: 'earth' },
    { id: 'NordAmerica', name: t('northAmerica'), icon: 'earth' },
    { id: 'Africa', name: t('africa'), icon: 'earth' },
    { id: 'Asia', name: t('asia'), icon: 'earth' },
    { id: 'Oceania', name: t('oceania'), icon: 'earth' },
  ];
  
  const [radios, setRadios] = useState<Radio[]>([]);
  const [filteredRadios, setFilteredRadios] = useState<Radio[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedContinent, setSelectedContinent] = useState('all');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterRadios();
  }, [selectedContinent, radios]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [radioData, storedFavorites] = await Promise.all([
        api.getRadios(),
        AsyncStorage.getItem('radio_favorites'),
      ]);
      setRadios(radioData || []);
      if (storedFavorites) {
        setFavorites(new Set(JSON.parse(storedFavorites)));
      }
    } catch (error) {
      console.log('Error loading radios:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterRadios = () => {
    if (selectedContinent === 'all') {
      setFilteredRadios(radios);
    } else {
      setFilteredRadios(radios.filter(r => r.continent === selectedContinent));
    }
  };

  const openRadio = (radio: Radio) => {
    const url = radio.stream_url || radio.url;
    Linking.openURL(url).catch(() => {
      Alert.alert(t('error'), t('unableToOpenRadio'));
    });
  };

  const toggleFavorite = async (radioName: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(radioName)) {
      newFavorites.delete(radioName);
    } else {
      newFavorites.add(radioName);
    }
    setFavorites(newFavorites);
    await AsyncStorage.setItem('radio_favorites', JSON.stringify([...newFavorites]));
  };

  const isFavorite = (radioName: string) => favorites.has(radioName);

  // Sort radios: favorites first
  const sortedRadios = [...filteredRadios].sort((a, b) => {
    const aFav = isFavorite(a.name) ? 0 : 1;
    const bFav = isFavorite(b.name) ? 0 : 1;
    return aFav - bFav;
  });

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>{t('loadingRadios')}</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Icon name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>📻 {t('evangelicalRadios')}</Text>
        <View style={{ width: 28 }} />
      </View>

      {/* Continent Filter */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterContainer}
      >
        {getContinents().map((continent) => (
          <TouchableOpacity
            key={continent.id}
            style={[
              styles.filterChip,
              selectedContinent === continent.id && styles.filterChipSelected,
            ]}
            onPress={() => setSelectedContinent(continent.id)}
          >
            <Text
              style={[
                styles.filterChipText,
                selectedContinent === continent.id && styles.filterChipTextSelected,
              ]}
            >
              {continent.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Favorites Section */}
        {favorites.size > 0 && selectedContinent === 'all' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>⭐ {t('favorites')}</Text>
            {sortedRadios.filter(r => isFavorite(r.name)).map((radio) => (
              <RadioItem
                key={`fav-${radio.name}`}
                radio={radio}
                isFavorite={true}
                onPress={() => openRadio(radio)}
                onToggleFavorite={() => toggleFavorite(radio.name)}
              />
            ))}
          </View>
        )}

        {/* All Radios */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {selectedContinent === 'all' ? t('allRadios') : `${t('radios')} ${selectedContinent}`}
            {' '}({sortedRadios.length})
          </Text>
          {sortedRadios.map((radio) => (
            <RadioItem
              key={radio.name}
              radio={radio}
              isFavorite={isFavorite(radio.name)}
              onPress={() => openRadio(radio)}
              onToggleFavorite={() => toggleFavorite(radio.name)}
            />
          ))}
        </View>

        {sortedRadios.length === 0 && (
          <View style={styles.emptyContainer}>
            <Icon name="radio-outline" size={64} color={COLORS.textMuted} />
            <Text style={styles.emptyText}>{t('noRadiosFound')}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const RadioItem = ({ 
  radio, 
  isFavorite, 
  onPress, 
  onToggleFavorite 
}: { 
  radio: Radio; 
  isFavorite: boolean; 
  onPress: () => void; 
  onToggleFavorite: () => void;
}) => (
  <View style={styles.radioItem}>
    <TouchableOpacity 
      style={styles.radioContent} 
      onPress={onPress}
    >
      <View style={styles.radioIcon}>
        <Icon name="radio" size={22} color={COLORS.primary} />
      </View>
      <View style={styles.radioInfo}>
        <Text style={styles.radioName}>{radio.name}</Text>
        <Text style={styles.radioMeta}>
          {radio.country} • {radio.language.toUpperCase()}
        </Text>
      </View>
      <Icon name="play-circle" size={28} color={COLORS.primary} />
    </TouchableOpacity>
    <TouchableOpacity 
      style={styles.favoriteButton}
      onPress={onToggleFavorite}
    >
      <Icon 
        name={isFavorite ? 'heart' : 'heart-outline'} 
        size={24} 
        color={isFavorite ? COLORS.error : COLORS.textMuted} 
      />
    </TouchableOpacity>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  loadingText: {
    marginTop: SPACING.md,
    fontSize: 16,
    color: COLORS.textLight,
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
  filterContainer: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.card,
  },
  filterChip: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.full,
    marginRight: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  filterChipSelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  filterChipText: {
    fontSize: 14,
    color: COLORS.text,
    fontWeight: '500',
  },
  filterChipTextSelected: {
    color: '#fff',
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  section: {
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textLight,
    marginBottom: SPACING.sm,
  },
  radioItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  radioContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
  },
  radioIcon: {
    width: 44,
    height: 44,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  radioInfo: {
    flex: 1,
  },
  radioName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  radioMeta: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  favoriteButton: {
    padding: SPACING.md,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textMuted,
    marginTop: SPACING.md,
  },
});
