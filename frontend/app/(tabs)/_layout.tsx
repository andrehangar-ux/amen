import React from 'react';
import { Tabs } from 'expo-router';
import { TouchableOpacity, StyleSheet, View, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { COLORS, SHADOWS } from '../../src/utils/theme';
import { useLanguageStore } from '../../src/store/languageStore';

const TAB_LABELS: Record<string, Record<string, string>> = {
  it: { home: 'Home', bible: 'Bibbia', journal: 'Diario', profile: 'Profilo' },
  en: { home: 'Home', bible: 'Bible', journal: 'Journal', profile: 'Profile' },
  es: { home: 'Inicio', bible: 'Biblia', journal: 'Diario', profile: 'Perfil' },
  de: { home: 'Start', bible: 'Bibel', journal: 'Tagebuch', profile: 'Profil' },
  fr: { home: 'Accueil', bible: 'Bible', journal: 'Journal', profile: 'Profil' },
  pt: { home: 'Início', bible: 'Bíblia', journal: 'Diário', profile: 'Perfil' },
};

export default function TabLayout() {
  const { currentLanguage } = useLanguageStore();
  const labels = TAB_LABELS[currentLanguage] || TAB_LABELS['it'];
  
  return (
    <View style={styles.container}>
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: styles.tabBar,
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.textMuted,
          tabBarLabelStyle: styles.tabBarLabel,
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: labels.home,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="home" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="bible"
          options={{
            title: labels.bible,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="book" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="journal"
          options={{
            title: labels.journal,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="create" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            title: labels.profile,
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="person" size={size} color={color} />
            ),
          }}
        />
      </Tabs>
      
      {/* Floating AI Assistant Button */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/assistant')}
        activeOpacity={0.8}
      >
        <Ionicons name="chatbubble-ellipses" size={28} color="#fff" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  tabBar: {
    backgroundColor: COLORS.card,
    borderTopWidth: 0,
    height: Platform.OS === 'ios' ? 88 : 64,
    paddingBottom: Platform.OS === 'ios' ? 28 : 8,
    paddingTop: 8,
    ...SHADOWS.small,
  },
  tabBarLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  fab: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 100 : 76,
    right: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    ...SHADOWS.medium,
    zIndex: 100,
  },
});
