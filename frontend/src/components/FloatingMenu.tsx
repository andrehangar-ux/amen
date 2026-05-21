import React, { useState, useEffect, useRef, useMemo } from 'react';
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
  Animated,
  PanResponder,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
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

// Persisted position storage key. The user can drag the FAB anywhere and the
// last position is restored on next launch.
const FAB_POSITION_KEY = '@amen/fab_position_v1';
const FAB_SIZE = 56;
const EDGE_MARGIN = 8;          // minimum distance from any screen edge
const DRAG_THRESHOLD = 6;       // px of movement before a press becomes a drag

export const FloatingMenu: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const { currentLanguage } = useLanguageStore();
  const { user } = useAuthStore();
  const pathname = usePathname();
  const labels = MENU_LABELS[currentLanguage] || MENU_LABELS['it'];

  // ---- Draggable FAB position ------------------------------------------------
  const { width: screenW, height: screenH } = Dimensions.get('window');
  // Default = old hardcoded position (bottom-right).
  const defaultX = screenW - FAB_SIZE - 20;
  const defaultY = screenH - FAB_SIZE - (Platform.OS === 'ios' ? 100 : 90);

  const pan = useRef(new Animated.ValueXY({ x: defaultX, y: defaultY })).current;
  // Snapshot of the current position — needed because Animated.Value lives outside React state.
  const lastPos = useRef({ x: defaultX, y: defaultY });
  const isDragging = useRef(false);

  // Restore saved position on mount.
  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(FAB_POSITION_KEY);
        if (raw) {
          const saved = JSON.parse(raw);
          if (typeof saved.x === 'number' && typeof saved.y === 'number') {
            // Clamp to current screen in case the device was rotated since.
            const x = Math.min(Math.max(saved.x, EDGE_MARGIN), screenW - FAB_SIZE - EDGE_MARGIN);
            const y = Math.min(Math.max(saved.y, EDGE_MARGIN), screenH - FAB_SIZE - EDGE_MARGIN);
            pan.setValue({ x, y });
            lastPos.current = { x, y };
          }
        }
      } catch {
        /* ignore */
      }
    })();
  }, []);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        // Activate only on real drag — a static press still goes to onPress.
        onStartShouldSetPanResponder: () => false,
        onMoveShouldSetPanResponder: (_evt, gesture) =>
          Math.abs(gesture.dx) > DRAG_THRESHOLD || Math.abs(gesture.dy) > DRAG_THRESHOLD,

        onPanResponderGrant: () => {
          isDragging.current = true;
          pan.setOffset({ x: lastPos.current.x, y: lastPos.current.y });
          pan.setValue({ x: 0, y: 0 });
        },

        onPanResponderMove: Animated.event([null, { dx: pan.x, dy: pan.y }], {
          useNativeDriver: false,
        }),

        onPanResponderRelease: (_evt, gesture) => {
          pan.flattenOffset();
          // Clamp inside screen.
          let nx = lastPos.current.x + gesture.dx;
          let ny = lastPos.current.y + gesture.dy;
          nx = Math.min(Math.max(nx, EDGE_MARGIN), screenW - FAB_SIZE - EDGE_MARGIN);
          ny = Math.min(Math.max(ny, EDGE_MARGIN), screenH - FAB_SIZE - EDGE_MARGIN);

          Animated.spring(pan, {
            toValue: { x: nx, y: ny },
            useNativeDriver: false,
            friction: 7,
          }).start();

          lastPos.current = { x: nx, y: ny };
          AsyncStorage.setItem(FAB_POSITION_KEY, JSON.stringify({ x: nx, y: ny })).catch(() => {});
          // Reset drag flag on next tick so onPress fires for taps but not for drags.
          setTimeout(() => {
            isDragging.current = false;
          }, 50);
        },

        onPanResponderTerminate: () => {
          pan.flattenOffset();
          isDragging.current = false;
        },
      }),
    [screenW, screenH],
  );
  // ---------------------------------------------------------------------------

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
      <Animated.View
        style={[
          styles.fab,
          {
            transform: pan.getTranslateTransform(),
          },
        ]}
        {...panResponder.panHandlers}
      >
        <TouchableOpacity
          style={styles.fabTouchable}
          onPress={() => {
            if (isDragging.current) return; // ignore tap if user just dragged
            setVisible(true);
          }}
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
      </Animated.View>

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
    // top/left are 0 — the actual placement is driven by `pan` (Animated.ValueXY)
    // via `transform: [{translateX}, {translateY}]`. This lets the user drag
    // the burger anywhere on the screen and we persist that position.
    top: 0,
    left: 0,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    elevation: 8,
    ...SHADOWS.large,
  },
  fabTouchable: {
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    justifyContent: 'center',
    alignItems: 'center',
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
