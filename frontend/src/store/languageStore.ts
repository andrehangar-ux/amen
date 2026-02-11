import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Language {
  name: string;
  flag: string;
  tts_code: string;
}

interface LanguageState {
  currentLanguage: string;
  languages: Record<string, Language>;
  setLanguage: (lang: string) => Promise<void>;
  loadLanguage: () => Promise<void>;
  loadLanguages: () => Promise<void>;
}

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export const useLanguageStore = create<LanguageState>((set, get) => ({
  currentLanguage: 'it',
  languages: {
    it: { name: 'Italiano', flag: '🇮🇹', tts_code: 'it-IT' },
    es: { name: 'Español', flag: '🇪🇸', tts_code: 'es-ES' },
    en: { name: 'English', flag: '🇬🇧', tts_code: 'en-US' },
    pt: { name: 'Português', flag: '🇧🇷', tts_code: 'pt-BR' },
    fr: { name: 'Français', flag: '🇫🇷', tts_code: 'fr-FR' },
    de: { name: 'Deutsch', flag: '🇩🇪', tts_code: 'de-DE' },
  },

  setLanguage: async (lang: string) => {
    await AsyncStorage.setItem('app_language', lang);
    set({ currentLanguage: lang });
  },

  loadLanguage: async () => {
    const saved = await AsyncStorage.getItem('app_language');
    if (saved) {
      set({ currentLanguage: saved });
    }
  },

  loadLanguages: async () => {
    try {
      const response = await fetch(`${API_URL}/api/languages`);
      if (response.ok) {
        const data = await response.json();
        set({ languages: data });
      }
    } catch (error) {
      console.log('Error loading languages:', error);
    }
  },
}));

// UI Translations
export const translations: Record<string, Record<string, string>> = {
  it: {
    welcome: 'Benvenuto',
    goodMorning: 'Buongiorno',
    goodAfternoon: 'Buon pomeriggio',
    goodEvening: 'Buonasera',
    dailyVerse: 'Versetto del Giorno',
    howAreYou: 'Come ti senti oggi?',
    quickActions: 'Azioni Rapide',
    read: 'Leggi',
    write: 'Scrivi',
    ask: 'Chiedi',
    theBible: 'La Bibbia',
    inJournal: 'Nel Diario',
    toAssistant: "All'Assistente",
    yourProgress: 'Il Tuo Progresso',
    daysInRow: 'Giorni di fila',
    chaptersRead: 'Capitoli letti',
    journalEntries: 'Voci diario',
    community: 'Community',
    translate: 'Traduci',
    send: 'Invia',
    login: 'Accedi',
    register: 'Registrati',
    logout: 'Esci',
    settings: 'Impostazioni',
    language: 'Lingua',
    profile: 'Profilo',
    home: 'Home',
    bible: 'Bibbia',
    journal: 'Diario',
    assistant: 'Assistente',
    donate: 'Dona',
    radios: 'Radio Evangeliche',
  },
  es: {
    welcome: 'Bienvenido',
    goodMorning: 'Buenos días',
    goodAfternoon: 'Buenas tardes',
    goodEvening: 'Buenas noches',
    dailyVerse: 'Versículo del Día',
    howAreYou: '¿Cómo te sientes hoy?',
    quickActions: 'Acciones Rápidas',
    read: 'Leer',
    write: 'Escribir',
    ask: 'Preguntar',
    theBible: 'La Biblia',
    inJournal: 'En el Diario',
    toAssistant: 'Al Asistente',
    yourProgress: 'Tu Progreso',
    daysInRow: 'Días seguidos',
    chaptersRead: 'Capítulos leídos',
    journalEntries: 'Entradas del diario',
    community: 'Comunidad',
    translate: 'Traducir',
    send: 'Enviar',
    login: 'Iniciar sesión',
    register: 'Registrarse',
    logout: 'Salir',
    settings: 'Configuración',
    language: 'Idioma',
    profile: 'Perfil',
    home: 'Inicio',
    bible: 'Biblia',
    journal: 'Diario',
    assistant: 'Asistente',
    donate: 'Donar',
    radios: 'Radios Evangélicas',
  },
  en: {
    welcome: 'Welcome',
    goodMorning: 'Good morning',
    goodAfternoon: 'Good afternoon',
    goodEvening: 'Good evening',
    dailyVerse: 'Daily Verse',
    howAreYou: 'How are you feeling today?',
    quickActions: 'Quick Actions',
    read: 'Read',
    write: 'Write',
    ask: 'Ask',
    theBible: 'The Bible',
    inJournal: 'In Journal',
    toAssistant: 'the Assistant',
    yourProgress: 'Your Progress',
    daysInRow: 'Days in a row',
    chaptersRead: 'Chapters read',
    journalEntries: 'Journal entries',
    community: 'Community',
    translate: 'Translate',
    send: 'Send',
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    settings: 'Settings',
    language: 'Language',
    profile: 'Profile',
    home: 'Home',
    bible: 'Bible',
    journal: 'Journal',
    assistant: 'Assistant',
    donate: 'Donate',
    radios: 'Evangelical Radios',
  },
  pt: {
    welcome: 'Bem-vindo',
    goodMorning: 'Bom dia',
    goodAfternoon: 'Boa tarde',
    goodEvening: 'Boa noite',
    dailyVerse: 'Versículo do Dia',
    howAreYou: 'Como você está se sentindo hoje?',
    quickActions: 'Ações Rápidas',
    read: 'Ler',
    write: 'Escrever',
    ask: 'Perguntar',
    theBible: 'A Bíblia',
    inJournal: 'No Diário',
    toAssistant: 'ao Assistente',
    yourProgress: 'Seu Progresso',
    daysInRow: 'Dias seguidos',
    chaptersRead: 'Capítulos lidos',
    journalEntries: 'Entradas no diário',
    community: 'Comunidade',
    translate: 'Traduzir',
    send: 'Enviar',
    login: 'Entrar',
    register: 'Registrar',
    logout: 'Sair',
    settings: 'Configurações',
    language: 'Idioma',
    profile: 'Perfil',
    home: 'Início',
    bible: 'Bíblia',
    journal: 'Diário',
    assistant: 'Assistente',
    donate: 'Doar',
    radios: 'Rádios Evangélicas',
  },
  fr: {
    welcome: 'Bienvenue',
    goodMorning: 'Bonjour',
    goodAfternoon: 'Bon après-midi',
    goodEvening: 'Bonsoir',
    dailyVerse: 'Verset du Jour',
    howAreYou: 'Comment vous sentez-vous aujourd\'hui?',
    quickActions: 'Actions Rapides',
    read: 'Lire',
    write: 'Écrire',
    ask: 'Demander',
    theBible: 'La Bible',
    inJournal: 'Dans le Journal',
    toAssistant: "à l'Assistant",
    yourProgress: 'Votre Progrès',
    daysInRow: 'Jours consécutifs',
    chaptersRead: 'Chapitres lus',
    journalEntries: 'Entrées du journal',
    community: 'Communauté',
    translate: 'Traduire',
    send: 'Envoyer',
    login: 'Connexion',
    register: "S'inscrire",
    logout: 'Déconnexion',
    settings: 'Paramètres',
    language: 'Langue',
    profile: 'Profil',
    home: 'Accueil',
    bible: 'Bible',
    journal: 'Journal',
    assistant: 'Assistant',
    donate: 'Donner',
    radios: 'Radios Évangéliques',
  },
};

export const useTranslation = () => {
  const { currentLanguage } = useLanguageStore();
  
  const t = (key: string): string => {
    return translations[currentLanguage]?.[key] || translations['it'][key] || key;
  };
  
  return { t, currentLanguage };
};
