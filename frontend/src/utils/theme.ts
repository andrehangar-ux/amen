// Cibo Spirituale Theme
export const COLORS = {
  primary: '#6B7F5B',      // Deep Sage Green
  secondary: '#F5F3F0',    // Warm Cream
  accent: '#D4A574',       // Golden Yellow
  background: '#FAFAF8',
  card: '#FFFFFF',
  text: '#2D3436',
  textLight: '#636E72',
  textMuted: '#B2BEC3',
  border: '#E8E8E8',
  success: '#00B894',
  error: '#E74C3C',
  warning: '#F39C12',
};

export const FONTS = {
  heading: 'System',  // Would use Playfair Display with expo-font
  body: 'System',     // Would use Inter with expo-font
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const BORDER_RADIUS = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

export const SHADOWS = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 4,
  },
};

export const MOODS = [
  { key: 'felice', label: 'Felice', emoji: '😊', color: '#FFD93D' },
  { key: 'triste', label: 'Triste', emoji: '😢', color: '#74B9FF' },
  { key: 'ansioso', label: 'Ansioso', emoji: '😰', color: '#A29BFE' },
  { key: 'arrabbiato', label: 'Arrabbiato', emoji: '😤', color: '#FF7675' },
  { key: 'grato', label: 'Grato', emoji: '🙏', color: '#00B894' },
  { key: 'confuso', label: 'Confuso', emoji: '😕', color: '#FDCB6E' },
  { key: 'speranzoso', label: 'Speranzoso', emoji: '✨', color: '#81ECEC' },
  { key: 'stanco', label: 'Stanco', emoji: '😴', color: '#DFE6E9' },
];
