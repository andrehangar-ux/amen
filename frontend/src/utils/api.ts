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

  // Bible
  getBibleBooks: (lang = 'it') => api.fetch(`/api/bible/books?lang=${lang}`),
  getChapter: (book: string, chapter: number) => api.fetch(`/api/bible/chapter/${book}/${chapter}`),
  getDailyVerse: () => api.fetch('/api/bible/daily-verse'),

  // AI
  sendMessage: (message: string, mood?: string) => 
    api.fetch('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, mood }),
    }),
  getChatHistory: () => api.fetch('/api/ai/chat-history'),
  clearChatHistory: () => api.fetch('/api/ai/chat-history', { method: 'DELETE' }),
  moodCheckin: (mood: string) => 
    api.fetch('/api/ai/mood-checkin', {
      method: 'POST',
      body: JSON.stringify({ mood }),
    }),

  // Journal
  createJournalEntry: (content: string, mood: string) =>
    api.fetch('/api/journal', {
      method: 'POST',
      body: JSON.stringify({ content, mood }),
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

  // Donations
  createDonation: (amount: number, method: string, message?: string) =>
    api.fetch('/api/donations', {
      method: 'POST',
      body: JSON.stringify({ amount, method, message }),
    }),
  getDonations: () => api.fetch('/api/donations'),

  // Radios
  getRadios: () => api.fetch('/api/radios'),

  // Settings
  updateSettings: (settings: any) =>
    api.fetch('/api/users/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
};
