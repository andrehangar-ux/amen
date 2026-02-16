import React from 'react';
import { Platform, Text, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Emoji fallback map for web
const emojiMap: Record<string, string> = {
  // Navigation
  'home': '🏠',
  'home-outline': '🏠',
  'book': '📖',
  'book-outline': '📖',
  'create': '✏️',
  'create-outline': '✏️',
  'people': '👥',
  'people-outline': '👥',
  'notifications': '🔔',
  'notifications-outline': '🔔',
  'settings': '⚙️',
  'settings-outline': '⚙️',
  'person': '👤',
  'person-outline': '👤',
  
  // Chevrons/Arrows
  'chevron-forward': '›',
  'chevron-forward-outline': '›',
  'chevron-back': '‹',
  'chevron-back-outline': '‹',
  'chevron-down': '▼',
  'chevron-down-outline': '▼',
  'chevron-up': '▲',
  'chevron-up-outline': '▲',
  'arrow-back': '←',
  'arrow-forward': '→',
  
  // Actions
  'close': '✕',
  'close-outline': '✕',
  'search': '🔍',
  'search-outline': '🔍',
  'heart': '❤️',
  'heart-outline': '🤍',
  'star': '⭐',
  'star-outline': '☆',
  'bookmark': '🔖',
  'bookmark-outline': '🔖',
  'share': '📤',
  'share-outline': '📤',
  'share-social': '📤',
  'share-social-outline': '📤',
  
  // Audio
  'volume-high': '🔊',
  'volume-high-outline': '🔊',
  'volume-mute': '🔇',
  'volume-mute-outline': '🔇',
  'play': '▶️',
  'play-outline': '▶️',
  'play-circle': '▶️',
  'play-circle-outline': '▶️',
  'pause': '⏸️',
  'pause-outline': '⏸️',
  'stop': '⏹️',
  'stop-outline': '⏹️',
  'play-skip-forward': '⏭️',
  'play-skip-forward-outline': '⏭️',
  'play-skip-back': '⏮️',
  'play-skip-back-outline': '⏮️',
  'radio': '📻',
  'radio-outline': '📻',
  
  // Time
  'calendar': '📅',
  'calendar-outline': '📅',
  'time': '🕐',
  'time-outline': '🕐',
  
  // Status
  'checkmark': '✓',
  'checkmark-outline': '✓',
  'checkmark-circle': '✅',
  'checkmark-circle-outline': '✅',
  'checkbox': '☑️',
  'checkbox-outline': '☑️',
  'square': '⬜',
  'square-outline': '⬜',
  'alert-circle': '⚠️',
  'alert-circle-outline': '⚠️',
  'information-circle': 'ℹ️',
  'information-circle-outline': 'ℹ️',
  'help-circle': '❓',
  'help-circle-outline': '❓',
  
  // Visibility
  'eye': '👁️',
  'eye-outline': '👁️',
  'eye-off': '🙈',
  'eye-off-outline': '🙈',
  
  // Auth
  'lock-closed': '🔒',
  'lock-closed-outline': '🔒',
  'lock-open': '🔓',
  'lock-open-outline': '🔓',
  'mail': '📧',
  'mail-outline': '📧',
  'shield-checkmark': '🛡️',
  'shield-checkmark-outline': '🛡️',
  'finger-print': '👆',
  
  // Communication
  'chatbubble': '💬',
  'chatbubble-outline': '💬',
  'chatbubbles': '💬',
  'chatbubbles-outline': '💬',
  'chatbubble-ellipses': '💬',
  'chatbubble-ellipses-outline': '💬',
  'send': '📨',
  'send-outline': '📨',
  
  // Media
  'image': '🖼️',
  'image-outline': '🖼️',
  'camera': '📷',
  'camera-outline': '📷',
  'mic': '🎤',
  'mic-outline': '🎤',
  'call': '📞',
  'call-outline': '📞',
  'videocam': '📹',
  'videocam-outline': '📹',
  
  // Location
  'location': '📍',
  'location-outline': '📍',
  'globe': '🌍',
  'globe-outline': '🌍',
  'map': '🗺️',
  'map-outline': '🗺️',
  
  // Theme
  'moon': '🌙',
  'moon-outline': '🌙',
  'sunny': '☀️',
  'sunny-outline': '☀️',
  
  // Progress/Achievement
  'flame': '🔥',
  'flame-outline': '🔥',
  'trophy': '🏆',
  'trophy-outline': '🏆',
  'ribbon': '🎖️',
  'ribbon-outline': '🎖️',
  'medal': '🏅',
  'medal-outline': '🏅',
  'flag': '🚩',
  'flag-outline': '🚩',
  'trending-up': '📈',
  'trending-up-outline': '📈',
  'bar-chart': '📊',
  'bar-chart-outline': '📊',
  'pie-chart': '📊',
  'pie-chart-outline': '📊',
  
  // File actions
  'refresh': '🔄',
  'refresh-outline': '🔄',
  'download': '⬇️',
  'download-outline': '⬇️',
  'cloud-upload': '⬆️',
  'cloud-upload-outline': '⬆️',
  'trash': '🗑️',
  'trash-outline': '🗑️',
  'copy': '📋',
  'copy-outline': '📋',
  'open': '↗️',
  'open-outline': '↗️',
  'link': '🔗',
  'link-outline': '🔗',
  
  // Study tools
  'color-wand': '🎨',
  'color-wand-outline': '🎨',
  'sparkles': '✨',
  'sparkles-outline': '✨',
  'bulb': '💡',
  'bulb-outline': '💡',
  'brush': '🖌️',
  'brush-outline': '🖌️',
  'card': '🃏',
  'card-outline': '🃏',
  'keypad': '🔢',
  'keypad-outline': '🔢',
  'close-circle': '✕',
  'close-circle-outline': '✕',
  
  // Language
  'language': '🌐',
  'language-outline': '🌐',
  
  // Social/Logos
  'logo-google': '🔵',
  
  // Misc
  'add': '+',
  'add-outline': '+',
  'remove': '-',
  'remove-outline': '-',
  'menu': '☰',
  'menu-outline': '☰',
  'options': '⋮',
  'ellipsis-vertical': '⋮',
  'ellipsis-horizontal': '⋯',
  'list': '☰',
  'list-outline': '☰',
  'grid': '▦',
  'grid-outline': '▦',
  'document-text': '📄',
  'document-text-outline': '📄',
  'newspaper': '📰',
  'newspaper-outline': '📰',
  'text': '📝',
  'text-outline': '📝',
  'cash': '💰',
  'cash-outline': '💰',
  'wallet': '👛',
  'wallet-outline': '👛',
  'gift': '🎁',
  'gift-outline': '🎁',
  'at': '@',
  'at-outline': '@',
  'exit': '🚪',
  'exit-outline': '🚪',
  'log-out': '🚪',
  'log-out-outline': '🚪',
  'enter': '➡️',
  'enter-outline': '➡️',
  'log-in': '➡️',
  'log-in-outline': '➡️',
};

interface IconProps {
  name: string;
  size?: number;
  color?: string;
  style?: any;
}

export const Icon: React.FC<IconProps> = ({ name, size = 24, color = '#000', style }) => {
  // On native platforms, always use Ionicons
  if (Platform.OS !== 'web') {
    return <Ionicons name={name as any} size={size} color={color} style={style} />;
  }
  
  // On web, use emoji fallback
  const emoji = emojiMap[name];
  
  if (emoji) {
    return (
      <Text style={[styles.emoji, { fontSize: size * 0.85, color }, style]}>
        {emoji}
      </Text>
    );
  }
  
  // Fallback to Ionicons (might not render correctly but try anyway)
  return <Ionicons name={name as any} size={size} color={color} style={style} />;
};

const styles = StyleSheet.create({
  emoji: {
    textAlign: 'center',
    lineHeight: 1.2,
  },
});

export default Icon;
