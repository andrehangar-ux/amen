import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Icon } from '../src/components/Icon';
import { router } from 'expo-router';
import { api } from '../src/utils/api';
import { COLORS, SPACING, BORDER_RADIUS, SHADOWS } from '../src/utils/theme';

const { width } = Dimensions.get('window');

interface MapInfo {
  id: string;
  name: string;
  description: string;
  locations_count: number;
}

interface MapLocation {
  name: string;
  lat: number;
  lng: number;
  type: string;
  description: string;
}

interface MapData {
  id: string;
  name: string;
  description: string;
  center: { lat: number; lng: number };
  zoom: number;
  locations: MapLocation[];
}

export default function MapsScreen() {
  const [maps, setMaps] = useState<MapInfo[]>([]);
  const [selectedMap, setSelectedMap] = useState<MapData | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<MapLocation | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMap, setLoadingMap] = useState(false);

  useEffect(() => {
    loadMaps();
  }, []);

  const loadMaps = async () => {
    try {
      const data = await api.getMaps();
      setMaps(data);
    } catch (error) {
      console.error('Error loading maps:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMap = async (mapId: string) => {
    setLoadingMap(true);
    try {
      const data = await api.getMap(mapId);
      setSelectedMap(data);
    } catch (error) {
      console.error('Error loading map:', error);
    } finally {
      setLoadingMap(false);
    }
  };

  const getLocationIcon = (type: string) => {
    switch (type) {
      case 'city': return 'business';
      case 'water': return 'water';
      case 'mountain': return 'triangle';
      case 'river': return 'git-merge';
      case 'site': return 'location';
      default: return 'pin';
    }
  };

  const getLocationColor = (type: string) => {
    switch (type) {
      case 'city': return '#FF6B6B';
      case 'water': return '#4ECDC4';
      case 'mountain': return '#95A5A6';
      case 'river': return '#3498DB';
      case 'site': return '#E67E22';
      default: return COLORS.primary;
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Map Detail View
  if (selectedMap) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => { setSelectedMap(null); setSelectedLocation(null); }}>
            <Ionicons name="arrow-back" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title} numberOfLines={1}>{selectedMap.name}</Text>
          <View style={{ width: 28 }} />
        </View>

        {loadingMap ? (
          <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: SPACING.xl }} />
        ) : (
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Text style={styles.mapDescription}>{selectedMap.description}</Text>

            {/* Simplified Map Visualization */}
            <View style={styles.mapContainer}>
              <View style={styles.mapPlaceholder}>
                <Ionicons name="map" size={60} color={COLORS.primary} />
                <Text style={styles.mapPlaceholderText}>Mappa Interattiva</Text>
                <Text style={styles.mapCoords}>
                  Centro: {selectedMap.center.lat.toFixed(2)}°N, {selectedMap.center.lng.toFixed(2)}°E
                </Text>
              </View>

              {/* Location Markers Grid */}
              <View style={styles.locationsGrid}>
                {selectedMap.locations.map((loc, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.locationMarker,
                      selectedLocation?.name === loc.name && styles.locationMarkerSelected,
                    ]}
                    onPress={() => setSelectedLocation(loc)}
                  >
                    <View style={[styles.markerIcon, { backgroundColor: getLocationColor(loc.type) + '20' }]}>
                      <Ionicons name={getLocationIcon(loc.type)} size={20} color={getLocationColor(loc.type)} />
                    </View>
                    <Text style={styles.markerName} numberOfLines={1}>{loc.name}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Selected Location Details */}
            {selectedLocation && (
              <View style={styles.locationDetails}>
                <View style={styles.locationHeader}>
                  <View style={[styles.locationIcon, { backgroundColor: getLocationColor(selectedLocation.type) }]}>
                    <Ionicons name={getLocationIcon(selectedLocation.type)} size={24} color="#fff" />
                  </View>
                  <Text style={styles.locationName}>{selectedLocation.name}</Text>
                </View>
                <Text style={styles.locationDescription}>{selectedLocation.description}</Text>
                <View style={styles.locationCoords}>
                  <Ionicons name="location" size={16} color={COLORS.textMuted} />
                  <Text style={styles.locationCoordsText}>
                    {selectedLocation.lat.toFixed(4)}°N, {selectedLocation.lng.toFixed(4)}°E
                  </Text>
                </View>
              </View>
            )}

            {/* All Locations List */}
            <Text style={styles.sectionTitle}>Tutti i Luoghi ({selectedMap.locations.length})</Text>
            {selectedMap.locations.map((loc, index) => (
              <TouchableOpacity
                key={index}
                style={styles.locationCard}
                onPress={() => setSelectedLocation(loc)}
              >
                <View style={[styles.locationCardIcon, { backgroundColor: getLocationColor(loc.type) + '20' }]}>
                  <Ionicons name={getLocationIcon(loc.type)} size={22} color={getLocationColor(loc.type)} />
                </View>
                <View style={styles.locationCardContent}>
                  <Text style={styles.locationCardName}>{loc.name}</Text>
                  <Text style={styles.locationCardDesc} numberOfLines={2}>{loc.description}</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={COLORS.textMuted} />
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </SafeAreaView>
    );
  }

  // Maps List View
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={28} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Mappe Bibliche</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.heroCard}>
          <Ionicons name="globe" size={50} color={COLORS.primary} />
          <Text style={styles.heroTitle}>Esplora la Terra Santa</Text>
          <Text style={styles.heroText}>
            Scopri i luoghi biblici dove si sono svolti gli eventi della Scrittura.
          </Text>
        </View>

        {maps.map((map) => (
          <TouchableOpacity
            key={map.id}
            style={styles.mapCard}
            onPress={() => loadMap(map.id)}
          >
            <View style={styles.mapCardIcon}>
              <Ionicons name="map" size={32} color={COLORS.primary} />
            </View>
            <View style={styles.mapCardContent}>
              <Text style={styles.mapCardTitle}>{map.name}</Text>
              <Text style={styles.mapCardDescription} numberOfLines={2}>{map.description}</Text>
              <Text style={styles.mapCardMeta}>{map.locations_count} luoghi</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.textMuted} />
          </TouchableOpacity>
        ))}
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
    backgroundColor: COLORS.background,
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
    flex: 1,
    textAlign: 'center',
  },
  scrollContent: {
    padding: SPACING.md,
    paddingBottom: 100,
  },
  heroCard: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    alignItems: 'center',
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: SPACING.md,
  },
  heroText: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: SPACING.sm,
  },
  mapCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    ...SHADOWS.small,
  },
  mapCardIcon: {
    width: 60,
    height: 60,
    borderRadius: BORDER_RADIUS.lg,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  mapCardContent: {
    flex: 1,
  },
  mapCardTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
  },
  mapCardDescription: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  mapCardMeta: {
    fontSize: 12,
    color: COLORS.primary,
    marginTop: 4,
  },
  mapDescription: {
    fontSize: 15,
    color: COLORS.textLight,
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  mapContainer: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    ...SHADOWS.small,
  },
  mapPlaceholder: {
    backgroundColor: COLORS.primary + '10',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.xl,
    alignItems: 'center',
  },
  mapPlaceholderText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: SPACING.sm,
  },
  mapCoords: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: SPACING.xs,
  },
  locationsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: SPACING.md,
    justifyContent: 'center',
  },
  locationMarker: {
    alignItems: 'center',
    padding: SPACING.sm,
    margin: SPACING.xs,
    borderRadius: BORDER_RADIUS.md,
    width: (width - SPACING.md * 4 - SPACING.xs * 8) / 4,
  },
  locationMarkerSelected: {
    backgroundColor: COLORS.primary + '15',
  },
  markerIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  markerName: {
    fontSize: 10,
    color: COLORS.text,
    textAlign: 'center',
    marginTop: SPACING.xs,
  },
  locationDetails: {
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
    ...SHADOWS.small,
  },
  locationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  locationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  locationName: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  locationDescription: {
    fontSize: 14,
    color: COLORS.textLight,
    lineHeight: 22,
  },
  locationCoords: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.sm,
  },
  locationCoordsText: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginLeft: SPACING.xs,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  locationCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  locationCardIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  locationCardContent: {
    flex: 1,
  },
  locationCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  locationCardDesc: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
});
