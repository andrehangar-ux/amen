import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Pressable,
  Platform,
  ScrollView,
  Dimensions,
} from 'react-native';
import { router, usePathname } from 'expo-router';
import { Icon } from './Icon';
import { COLORS, SHADOWS, SPACING } from '../utils/theme';
import { useLanguageStore } from '../store/languageStore';
import { useAuthStore } from '../store/authStore';

const MENU_LABELS: Record<string, Record<string, string>> = {
  it: { home: 'Home', bible: 'Bibbia', journal: 'Diario', profile: 'Profilo', donate: 'Donazioni', settings: 'Impostazioni', myContent: 'I Miei Contenuti', quiz: 'Quiz', dictionary: 'Dizionario', community: 'Community', studyGroups: 'Gruppi di Studio', friends: 'Amici', search: 'Ricerca' },
  en: { home: 'Home', bible: 'Bible', journal: 'Journal', profile: 'Profile', donate: 'Donate', settings: 'Settings', myContent: 'My Content', quiz: 'Quiz', dictionary: 'Dictionary', community: 'Community', studyGroups: 'Study Groups', friends: 'Friends', search: 'Search' },
  es: { home: 'Inicio', bible: 'Biblia', journal: 'Diario', profile: 'Perfil', donate: 'Donar', settings: 'Configuracion', myContent: 'Mi Contenido', quiz: 'Quiz', dictionary: 'Diccionario', community: 'Comunidad', studyGroups: 'Grupos de Estudio', friends: 'Amigos', search: 'Buscar' },
  de: { home: 'Start', bible: 'Bibel', journal: 'Tagebuch', profile: 'Profil', donate: 'Spenden', settings: 'Einstellungen', myContent: 'Meine Inhalte', quiz: 'Quiz', dictionary: 'Worterbuch', community: 'Community', studyGroups: 'Studiengruppen', friends: 'Freunde', search: 'Suche' },
  fr: { home: 'Accueil', bible: 'Bible', journal: 'Journal', profile: 'Profil', donate: 'Dons', settings: 'Parametres', myContent: 'Mon Contenu', quiz: 'Quiz', dictionary: 'Dictionnaire', community: 'Communaute', studyGroups: 'Groupes d\'Etude', friends: 'Amis', search: 'Rechercher' },
  pt: { home: 'Inicio', bible: 'Biblia', journal: 'Diario', profile: 'Perfil', donate: 'Doar', settings: 'Configuracoes', myContent: 'Meu Conteudo', quiz: 'Quiz', dictionary: 'Dicionario', community: 'Comunidade', studyGroups: 'Grupos de Estudo', friends: 'Amigos', search: 'Pesquisar' },
};

const HIDDEN_ON = ['/(auth)', '/login', '/register', '/forgot-password'];

export const FloatingMenu: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const { currentLanguage } = useLanguageStore();
  const { user } = useAuthStore();
  const pathname = usePathname();
  const labels = MENU_LABELS[currentLanguage] || MENU_LABELS['it'];

  if (!user || HIDDEN_ON.some(p => pathname.startsWith(p))) return null;

  const menuItems = [
    { key: 'home', label: labels.home, icon: 'home', route: '/(tabs)' },
    { key: 'bible', label: labels.bible, icon: 'book', route: '/(tabs)/bible' },
    { key: 'profile', label: labels.profile, icon: 'person', route: '/(tabs)/profile' },
    { key: 'search', label: labels.search, icon: 'search', route: '/search' },
    { key: 'journal', label: labels.journal, icon: 'create', route: '/(tabs)/journal' },
    { key: 'quiz', label: labels.quiz, icon: 'help-circle', route: '/quiz' },
    { key: 'dictionary', label: labels.dictionary, icon: 'library', route: '/dictionary' },
    { key: 'community', label: labels.community, icon: 'people', route: '/community' },
    { key: 'friends', label: labels.friends, icon: 'heart', route: '/friends' },
    { key: 'studyGroups', label: labels.studyGroups, icon: 'school', route: '/study-groups' },
    { key: 'myContent', label: labels.myContent, icon: 'bookmark', route: '/my-content' },
    { key: 'assistant', label: 'AI', icon: 'chatbubbles', route: '/assistant' },
    { key: 'donate', label: labels.donate, icon: 'gift', route: '/donate' },
    { key: 'settings', label: labels.settings, icon: 'settings', route: '/settings' },
  ];

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

  const handleNavigate = (route: string) => {
    setVisible(false);
    setTimeout(() => router.push(route as any), 150);
  };

  return (
    <>
      <TouchableOpacity
        style={styles.fab}
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
        testID="floating-menu-button"
        accessibilityLabel="Menu"
        accessibilityRole="button"
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <View style={styles.fabInner} pointerEvents="none">
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
        statusBarTranslucent
      >
        <View style={styles.modalFull}>
          {/* Tappable top area to close */}
          <Pressable style={styles.topClose} onPress={() => setVisible(false)} />

          {/* Menu panel */}
          <View style={styles.menuPanel}>
            <View style={styles.menuHeader}>
              <Text style={styles.menuTitle}>Menu</Text>
              <TouchableOpacity onPress={() => setVisible(false)} activeOpacity={0.4} style={styles.closeBtn}>
                <View style={styles.closeLine1} />
                <View style={styles.closeLine2} />
              </TouchableOpacity>
            </View>

            <ScrollView
              style={styles.scrollView}
              showsVerticalScrollIndicator={true}
              bounces={false}
              nestedScrollEnabled={true}
              contentContainerStyle={styles.scrollContent}
            >
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
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 100 : 90,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
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
  // Full screen modal layout
  modalFull: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  topClose: {
    flex: 1,
  },
  menuPanel: {
    backgroundColor: COLORS.card,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    // Numeric maxHeight (Dimensions) instead of '85%': some Android versions
    // do not resolve % maxHeight correctly inside a transparent Modal, leaving
    // the ScrollView unbounded and therefore not scrollable.
    maxHeight: Math.round(Dimensions.get('window').height * 0.85),
    // flexShrink lets the panel respect its maxHeight even when content is
    // larger than the available space.
    flexShrink: 1,
    ...SHADOWS.large,
  },
  scrollView: {
    // Required on Android: without an explicit flex/flexGrow inside a parent
    // that uses maxHeight, the ScrollView may render with 0 height and lose
    // its scrolling capability on certain devices.
    flexGrow: 1,
    flexShrink: 1,
  },
  menuHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  menuTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  closeBtn: {
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeLine1: {
    position: 'absolute',
    width: 20,
    height: 2,
    backgroundColor: COLORS.text,
    borderRadius: 1,
    transform: [{ rotate: '45deg' }],
  },
  closeLine2: {
    position: 'absolute',
    width: 20,
    height: 2,
    backgroundColor: COLORS.text,
    borderRadius: 1,
    transform: [{ rotate: '-45deg' }],
  },
  scrollContent: {
    paddingBottom: 120,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
    paddingHorizontal: SPACING.lg,
    gap: 14,
  },
  menuItemActive: {
    backgroundColor: COLORS.primary + '08',
  },
  menuItemText: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.text,
  },
  menuItemTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
});
