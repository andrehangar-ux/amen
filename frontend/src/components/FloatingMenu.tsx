import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Pressable,
  Platform,
} from 'react-native';
import { router, usePathname } from 'expo-router';
import { Icon } from './Icon';
import { COLORS, SHADOWS, SPACING } from '../utils/theme';
import { useLanguageStore } from '../store/languageStore';
import { useAuthStore } from '../store/authStore';

const MENU_LABELS: Record<string, Record<string, string>> = {
  it: { home: 'Home', bible: 'Bibbia', journal: 'Diario', profile: 'Profilo', donate: 'Donazioni', settings: 'Impostazioni', myContent: 'I Miei Contenuti', quiz: 'Quiz', dictionary: 'Dizionario', community: 'Community' },
  en: { home: 'Home', bible: 'Bible', journal: 'Journal', profile: 'Profile', donate: 'Donate', settings: 'Settings', myContent: 'My Content', quiz: 'Quiz', dictionary: 'Dictionary', community: 'Community' },
  es: { home: 'Inicio', bible: 'Biblia', journal: 'Diario', profile: 'Perfil', donate: 'Donar', settings: 'Configuracion', myContent: 'Mi Contenido', quiz: 'Quiz', dictionary: 'Diccionario', community: 'Comunidad' },
  de: { home: 'Start', bible: 'Bibel', journal: 'Tagebuch', profile: 'Profil', donate: 'Spenden', settings: 'Einstellungen', myContent: 'Meine Inhalte', quiz: 'Quiz', dictionary: 'Worterbuch', community: 'Community' },
  fr: { home: 'Accueil', bible: 'Bible', journal: 'Journal', profile: 'Profil', donate: 'Dons', settings: 'Parametres', myContent: 'Mon Contenu', quiz: 'Quiz', dictionary: 'Dictionnaire', community: 'Communaute' },
  pt: { home: 'Inicio', bible: 'Biblia', journal: 'Diario', profile: 'Perfil', donate: 'Doar', settings: 'Configuracoes', myContent: 'Meu Conteudo', quiz: 'Quiz', dictionary: 'Dicionario', community: 'Comunidade' },
};

const HIDDEN_ON = ['/(auth)', '/login', '/register', '/forgot-password'];

export const FloatingMenu: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const { currentLanguage } = useLanguageStore();
  const { user } = useAuthStore();
  const pathname = usePathname();
  const labels = MENU_LABELS[currentLanguage] || MENU_LABELS['it'];

  // Hide on auth screens or when not logged in
  if (!user || HIDDEN_ON.some(p => pathname.startsWith(p))) return null;

  const menuItems = [
    { key: 'home', label: labels.home, icon: 'home', route: '/(tabs)' },
    { key: 'bible', label: labels.bible, icon: 'book', route: '/(tabs)/bible' },
    { key: 'journal', label: labels.journal, icon: 'create', route: '/(tabs)/journal' },
    { key: 'quiz', label: labels.quiz, icon: 'help-circle', route: '/quiz' },
    { key: 'dictionary', label: labels.dictionary, icon: 'search', route: '/dictionary' },
    { key: 'community', label: labels.community, icon: 'people', route: '/community' },
    { key: 'myContent', label: labels.myContent, icon: 'bookmark', route: '/my-content' },
    { key: 'profile', label: labels.profile, icon: 'person', route: '/(tabs)/profile' },
    { key: 'donate', label: labels.donate, icon: 'heart', route: '/donate' },
    { key: 'settings', label: labels.settings, icon: 'settings', route: '/settings' },
  ];

  const handleNavigate = (route: string) => {
    setVisible(false);
    router.push(route as any);
  };

  const isActive = (key: string) => {
    if (key === 'home') return pathname === '/' || pathname === '/(tabs)';
    if (key === 'bible') return pathname.includes('bible');
    if (key === 'journal') return pathname.includes('journal');
    if (key === 'profile') return pathname.includes('profile');
    if (key === 'quiz') return pathname.includes('quiz');
    if (key === 'dictionary') return pathname.includes('dictionary');
    if (key === 'community') return pathname.includes('community');
    return false;
  };

  return (
    <>
      <TouchableOpacity
        style={styles.fab}
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
      >
        <View style={styles.fabInner}>
          <View style={styles.burgLine} />
          <View style={styles.burgLine} />
          <View style={styles.burgLine} />
        </View>
      </TouchableOpacity>

      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={() => setVisible(false)}
      >
        <Pressable style={styles.overlay} onPress={() => setVisible(false)}>
          <View style={styles.menuContainer} onStartShouldSetResponder={() => true}>
            <View style={styles.menuHeader}>
              <Text style={styles.menuTitle}>Menu</Text>
              <TouchableOpacity onPress={() => setVisible(false)} activeOpacity={0.4} style={styles.closeBtn}>
                <View style={styles.closeLine1} />
                <View style={styles.closeLine2} />
              </TouchableOpacity>
            </View>
            
            {menuItems.map((item) => (
              <TouchableOpacity
                key={item.key}
                style={[styles.menuItem, isActive(item.key) && styles.menuItemActive]}
                onPress={() => handleNavigate(item.route)}
                activeOpacity={0.7}
              >
                <Icon
                  name={item.icon as any}
                  size={20}
                  color={isActive(item.key) ? COLORS.primary : COLORS.text}
                />
                <Text style={[styles.menuItemText, isActive(item.key) && styles.menuItemTextActive]}>
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </Pressable>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 32 : 20,
    right: 20,
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    elevation: 8,
    ...SHADOWS.large,
  },
  fabInner: {
    width: 22,
    height: 16,
    justifyContent: 'space-between',
  },
  burgLine: {
    width: 22,
    height: 2.5,
    backgroundColor: '#fff',
    borderRadius: 2,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
  },
  menuContainer: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    width: '100%',
    maxHeight: '70%',
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
    ...SHADOWS.large,
  },
  menuHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  menuTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  closeBtn: {
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeLine1: {
    position: 'absolute',
    width: 18,
    height: 2,
    backgroundColor: COLORS.text,
    borderRadius: 1,
    transform: [{ rotate: '45deg' }],
  },
  closeLine2: {
    position: 'absolute',
    width: 18,
    height: 2,
    backgroundColor: COLORS.text,
    borderRadius: 1,
    transform: [{ rotate: '-45deg' }],
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: SPACING.lg,
    gap: 14,
  },
  menuItemActive: {
    backgroundColor: COLORS.primary + '10',
  },
  menuItemText: {
    fontSize: 16,
    color: COLORS.text,
  },
  menuItemTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
});
