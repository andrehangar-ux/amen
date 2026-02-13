import React from 'react';
import { Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import {
  Home,
  Book,
  BookOpen,
  Edit3,
  Users,
  Bell,
  Settings,
  User,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  X,
  Search,
  Heart,
  Star,
  Bookmark,
  Share2,
  Volume2,
  VolumeX,
  Play,
  Pause,
  SkipForward,
  SkipBack,
  Calendar,
  Clock,
  Check,
  AlertCircle,
  Info,
  HelpCircle,
  Eye,
  EyeOff,
  Lock,
  Mail,
  MessageSquare,
  Send,
  Image,
  Camera,
  Mic,
  Phone,
  MapPin,
  Globe,
  Moon,
  Sun,
  Flame,
  Trophy,
  Award,
  Target,
  TrendingUp,
  BarChart2,
  PieChart,
  RefreshCw,
  Download,
  Upload,
  Trash2,
  Copy,
  ExternalLink,
  Link,
  Highlighter,
  Sparkles,
  Bot,
  Radio,
  Map,
  type LucideIcon
} from 'lucide-react';

// Map Ionicons names to Lucide icons
const iconMap: Record<string, LucideIcon> = {
  // Navigation
  'home': Home,
  'home-outline': Home,
  'book': Book,
  'book-outline': BookOpen,
  'create': Edit3,
  'create-outline': Edit3,
  'people': Users,
  'people-outline': Users,
  'notifications': Bell,
  'notifications-outline': Bell,
  'settings': Settings,
  'settings-outline': Settings,
  'person': User,
  'person-outline': User,
  
  // Chevrons
  'chevron-forward': ChevronRight,
  'chevron-forward-outline': ChevronRight,
  'chevron-back': ChevronLeft,
  'chevron-back-outline': ChevronLeft,
  'chevron-down': ChevronDown,
  'chevron-down-outline': ChevronDown,
  'chevron-up': ChevronUp,
  'chevron-up-outline': ChevronUp,
  'arrow-back': ChevronLeft,
  'arrow-forward': ChevronRight,
  
  // Actions
  'close': X,
  'close-outline': X,
  'search': Search,
  'search-outline': Search,
  'heart': Heart,
  'heart-outline': Heart,
  'star': Star,
  'star-outline': Star,
  'bookmark': Bookmark,
  'bookmark-outline': Bookmark,
  'share': Share2,
  'share-outline': Share2,
  'share-social': Share2,
  'share-social-outline': Share2,
  
  // Audio
  'volume-high': Volume2,
  'volume-high-outline': Volume2,
  'volume-mute': VolumeX,
  'volume-mute-outline': VolumeX,
  'play': Play,
  'play-outline': Play,
  'pause': Pause,
  'pause-outline': Pause,
  'play-skip-forward': SkipForward,
  'play-skip-forward-outline': SkipForward,
  'play-skip-back': SkipBack,
  'play-skip-back-outline': SkipBack,
  'radio': Radio,
  'radio-outline': Radio,
  
  // Time
  'calendar': Calendar,
  'calendar-outline': Calendar,
  'time': Clock,
  'time-outline': Clock,
  
  // Status
  'checkmark': Check,
  'checkmark-outline': Check,
  'checkmark-circle': Check,
  'checkmark-circle-outline': Check,
  'alert-circle': AlertCircle,
  'alert-circle-outline': AlertCircle,
  'information-circle': Info,
  'information-circle-outline': Info,
  'help-circle': HelpCircle,
  'help-circle-outline': HelpCircle,
  
  // Visibility
  'eye': Eye,
  'eye-outline': Eye,
  'eye-off': EyeOff,
  'eye-off-outline': EyeOff,
  
  // Auth
  'lock-closed': Lock,
  'lock-closed-outline': Lock,
  'mail': Mail,
  'mail-outline': Mail,
  'shield-checkmark': Check,
  'shield-checkmark-outline': Check,
  
  // Communication
  'chatbubble': MessageSquare,
  'chatbubble-outline': MessageSquare,
  'chatbubbles': MessageSquare,
  'chatbubbles-outline': MessageSquare,
  'send': Send,
  'send-outline': Send,
  
  // Media
  'image': Image,
  'image-outline': Image,
  'camera': Camera,
  'camera-outline': Camera,
  'mic': Mic,
  'mic-outline': Mic,
  'call': Phone,
  'call-outline': Phone,
  
  // Location
  'location': MapPin,
  'location-outline': MapPin,
  'globe': Globe,
  'globe-outline': Globe,
  'map': Map,
  'map-outline': Map,
  
  // Theme
  'moon': Moon,
  'moon-outline': Moon,
  'sunny': Sun,
  'sunny-outline': Sun,
  
  // Progress
  'flame': Flame,
  'flame-outline': Flame,
  'trophy': Trophy,
  'trophy-outline': Trophy,
  'ribbon': Award,
  'ribbon-outline': Award,
  'medal': Award,
  'medal-outline': Award,
  'flag': Target,
  'flag-outline': Target,
  'trending-up': TrendingUp,
  'trending-up-outline': TrendingUp,
  'bar-chart': BarChart2,
  'bar-chart-outline': BarChart2,
  'pie-chart': PieChart,
  'pie-chart-outline': PieChart,
  
  // File actions
  'refresh': RefreshCw,
  'refresh-outline': RefreshCw,
  'download': Download,
  'download-outline': Download,
  'cloud-upload': Upload,
  'cloud-upload-outline': Upload,
  'trash': Trash2,
  'trash-outline': Trash2,
  'copy': Copy,
  'copy-outline': Copy,
  'open': ExternalLink,
  'open-outline': ExternalLink,
  'link': Link,
  'link-outline': Link,
  
  // AI & Study tools
  'color-wand': Highlighter,
  'color-wand-outline': Highlighter,
  'sparkles': Sparkles,
  'sparkles-outline': Sparkles,
  'bulb': Sparkles,
  'bulb-outline': Sparkles,
  
  // Additional
  'language': Globe,
  'language-outline': Globe,
  'videocam': Play,
  'videocam-outline': Play,
  
  // Logos - fallback to similar icons
  'logo-google': Globe,
};

interface IconProps {
  name: keyof typeof Ionicons.glyphMap | string;
  size?: number;
  color?: string;
  style?: any;
}

export const Icon: React.FC<IconProps> = ({ name, size = 24, color = '#000', style }) => {
  // Always use Ionicons on mobile, lucide-react on web
  if (Platform.OS !== 'web') {
    return <Ionicons name={name as any} size={size} color={color} style={style} />;
  }
  
  // Web: try to find Lucide equivalent
  const LucideIcon = iconMap[name];
  
  if (LucideIcon) {
    return <LucideIcon size={size} color={color} style={style} />;
  }
  
  // Fallback: try Ionicons anyway (might work if font loads)
  return <Ionicons name={name as any} size={size} color={color} style={style} />;
};

export default Icon;
