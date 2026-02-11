import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export const api = {
  async fetch(endpoint: string, options: RequestInit = {}) {
    const token = await AsyncStorage.getItem('session_token');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Errore sconosciuto' }));
      throw new Error(error.detail || 'Errore API');
    }
    
    return response.json();
  },

  // Languages
  getLanguages: () => api.fetch('/api/languages'),

  // Translation
  translate: (text: string, sourceLang: string, targetLang: string) =>
    api.fetch('/api/translate', {
      method: 'POST',
      body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang }),
    }),

  // Bible
  getBibleEditions: (lang?: string) => api.fetch(`/api/bible/editions${lang ? `?lang=${lang}` : ''}`),
  getBibleBooks: (lang = 'it') => api.fetch(`/api/bible/books?lang=${lang}`),
  getChapter: (book: string, chapter: number, lang = 'it') => 
    api.fetch(`/api/bible/chapter/${encodeURIComponent(book)}/${chapter}?lang=${lang}`),
  getDailyVerse: (lang = 'it') => api.fetch(`/api/bible/daily-verse?lang=${lang}`),
  translateVerse: (text: string, sourceLang: string, targetLang: string) =>
    api.fetch('/api/bible/translate-verse', {
      method: 'POST',
      body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang }),
    }),

  // AI
  sendMessage: (message: string, mood?: string, language?: string) => 
    api.fetch('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, mood, language }),
    }),
  getChatHistory: () => api.fetch('/api/ai/chat-history'),
  clearChatHistory: () => api.fetch('/api/ai/chat-history', { method: 'DELETE' }),
  moodCheckin: (mood: string, language?: string) => 
    api.fetch('/api/ai/mood-checkin', {
      method: 'POST',
      body: JSON.stringify({ mood, language }),
    }),

  // Journal
  createJournalEntry: (content: string, mood: string, language?: string) =>
    api.fetch('/api/journal', {
      method: 'POST',
      body: JSON.stringify({ content, mood, language }),
    }),
  getJournalEntries: () => api.fetch('/api/journal'),
  deleteJournalEntry: (entryId: string) => 
    api.fetch(`/api/journal/${entryId}`, { method: 'DELETE' }),

  // Bookmarks
  createBookmark: (data: any) =>
    api.fetch('/api/bookmarks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getBookmarks: () => api.fetch('/api/bookmarks'),
  deleteBookmark: (bookmarkId: string) =>
    api.fetch(`/api/bookmarks/${bookmarkId}`, { method: 'DELETE' }),

  // Progress
  getProgress: () => api.fetch('/api/progress'),
  updateReadingProgress: () => api.fetch('/api/progress/reading', { method: 'POST' }),

  // Community
  getCommunityMessages: (lang = 'it') => api.fetch(`/api/community/messages?lang=${lang}`),
  createCommunityMessage: (content: string, language: string, messageType = 'text') =>
    api.fetch('/api/community/messages', {
      method: 'POST',
      body: JSON.stringify({ content, language, message_type: messageType }),
    }),
  likeCommunityMessage: (messageId: string) =>
    api.fetch(`/api/community/messages/${messageId}/like`, { method: 'POST' }),
  getCommunityUsers: () => api.fetch('/api/community/users'),

  // Donations
  createDonation: (amount: number, method: string, message?: string) =>
    api.fetch('/api/donations', {
      method: 'POST',
      body: JSON.stringify({ amount, method, message }),
    }),
  getDonations: () => api.fetch('/api/donations'),

  // Radios
  getRadios: (lang?: string) => api.fetch(`/api/radios${lang ? `?lang=${lang}` : ''}`),

  // Settings
  updateSettings: (settings: any) =>
    api.fetch('/api/users/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
};
