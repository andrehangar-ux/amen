import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Pressable,
  Animated,
  Dimensions,
} from 'react-native';
import { router } from 'expo-router';
import { Icon } from './Icon';
import { COLORS, SHADOWS, SPACING } from '../utils/theme';
import { useLanguageStore } from '../store/languageStore';

const MENU_LABELS: Record<string, Record<string, string>> = {
  it: { home: 'Home', bible: 'Bibbia', journal: 'Diario', profile: 'Profilo', donate: 'Donazioni', settings: 'Impostazioni', myContent: 'I Miei Contenuti' },
  en: { home: 'Home', bible: 'Bible', journal: 'Journal', profile: 'Profile', donate: 'Donate', settings: 'Settings', myContent: 'My Content' },
  es: { home: 'Inicio', bible: 'Biblia', journal: 'Diario', profile: 'Perfil', donate: 'Donar', settings: 'Configuración', myContent: 'Mi Contenido' },
  de: { home: 'Start', bible: 'Bibel', journal: 'Tagebuch', profile: 'Profil', donate: 'Spenden', settings: 'Einstellungen', myContent: 'Meine Inhalte' },
  fr: { home: 'Accueil', bible: 'Bible', journal: 'Journal', profile: 'Profil', donate: 'Dons', settings: 'Paramètres', myContent: 'Mon Contenu' },
  pt: { home: 'Início', bible: 'Bíblia', journal: 'Diário', profile: 'Perfil', donate: 'Doar', settings: 'Configurações', myContent: 'Meu Conteúdo' },
};

interface HamburgerMenuProps {
  currentScreen?: string;
}

export const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ currentScreen = 'home' }) => {
  const [visible, setVisible] = useState(false);
  const { currentLanguage } = useLanguageStore();
  const labels = MENU_LABELS[currentLanguage] || MENU_LABELS['it'];

  const menuItems = [
    { key: 'home', label: labels.home, icon: 'home', route: '/(tabs)' },
    { key: 'bible', label: labels.bible, icon: 'book', route: '/(tabs)/bible' },
    { key: 'journal', label: labels.journal, icon: 'create', route: '/(tabs)/journal' },
    { key: 'myContent', label: labels.myContent, icon: 'bookmark', route: '/my-content' },
    { key: 'profile', label: labels.profile, icon: 'person', route: '/(tabs)/profile' },
    { key: 'donate', label: labels.donate, icon: 'heart', route: '/donate' },
    { key: 'settings', label: labels.settings, icon: 'settings', route: '/settings' },
  ];

  const handleNavigate = (route: string) => {
    setVisible(false);
    router.push(route as any);
  };

  return (
    <>
      <TouchableOpacity
        style={styles.menuButton}
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
      >
        <Icon name="menu" size={26} color={COLORS.text} />
      </TouchableOpacity>

      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={() => setVisible(false)}
      >
        <Pressable style={styles.overlay} onPress={() => setVisible(false)}>
          <View style={styles.menuContainer}>
            <View style={styles.menuHeader}>
              <Text style={styles.menuTitle}>Menu</Text>
              <TouchableOpacity onPress={() => setVisible(false)}>
                <Icon name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            
            {menuItems.map((item) => (
              <TouchableOpacity
                key={item.key}
                style={[
                  styles.menuItem,
                  currentScreen === item.key && styles.menuItemActive,
                ]}
                onPress={() => handleNavigate(item.route)}
                activeOpacity={0.7}
              >
                <Icon
                  name={item.icon as any}
                  size={22}
                  color={currentScreen === item.key ? COLORS.primary : COLORS.text}
                />
                <Text
                  style={[
                    styles.menuItemText,
                    currentScreen === item.key && styles.menuItemTextActive,
                  ]}
                >
                  {item.label}
                </Text>
                {currentScreen === item.key && (
                  <View style={styles.activeIndicator} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </Pressable>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  menuButton: {
    padding: 8,
    borderRadius: 8,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
  },
  menuContainer: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    marginTop: 60,
    marginRight: 16,
    minWidth: 220,
    ...SHADOWS.large,
    overflow: 'hidden',
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
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    paddingVertical: SPACING.md + 4,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  menuItemActive: {
    backgroundColor: `${COLORS.primary}10`,
  },
  menuItemText: {
    fontSize: 16,
    color: COLORS.text,
    marginLeft: SPACING.md,
    flex: 1,
  },
  menuItemTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  activeIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primary,
  },
});
