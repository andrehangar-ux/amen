import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export const api = {
  async fetch(endpoint: string, options: RequestInit = {}) {
    const token = await AsyncStorage.getItem('session_token');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'bypass-tunnel-reminder': 'true',  // Required for localtunnel
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
  getStudyNotes: (book: string, chapter: number, verse: number) =>
    api.fetch(`/api/bible/study/${encodeURIComponent(book)}/${chapter}/${verse}`),
  translateVerse: (text: string, sourceLang: string, targetLang: string) =>
    api.fetch('/api/bible/translate-verse', {
      method: 'POST',
      body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang }),
    }),

  // Feelings - Come mi sento
  analyzeFeeling: (text: string, language = 'it') =>
    api.fetch('/api/feelings/analyze', {
      method: 'POST',
      body: JSON.stringify({ text, language }),
    }),
  getFeelingsHistory: () => api.fetch('/api/feelings/history'),

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

  // Account Management
  deleteAccount: () => api.fetch('/api/auth/delete-account', { method: 'DELETE' }),

  // Groups
  getGroupTopics: () => api.fetch('/api/groups/topics'),
  createGroup: (data: { name: string; description: string; topic: string; is_public?: boolean; language?: string }) =>
    api.fetch('/api/groups', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getGroups: (topic?: string, lang?: string) => {
    let url = '/api/groups';
    const params = [];
    if (topic) params.push(`topic=${topic}`);
    if (lang) params.push(`lang=${lang}`);
    if (params.length) url += `?${params.join('&')}`;
    return api.fetch(url);
  },
  getMyGroups: () => api.fetch('/api/groups/my'),
  getGroup: (groupId: string) => api.fetch(`/api/groups/${groupId}`),
  joinGroup: (groupId: string) => api.fetch(`/api/groups/${groupId}/join`, { method: 'POST' }),
  leaveGroup: (groupId: string) => api.fetch(`/api/groups/${groupId}/leave`, { method: 'POST' }),
  
  // Group Posts
  createGroupPost: (groupId: string, content: string, postType = 'text', bibleReference?: string) =>
    api.fetch(`/api/groups/${groupId}/posts`, {
      method: 'POST',
      body: JSON.stringify({ content, post_type: postType, bible_reference: bibleReference }),
    }),
  getGroupPosts: (groupId: string) => api.fetch(`/api/groups/${groupId}/posts`),
  likePost: (groupId: string, postId: string) => 
    api.fetch(`/api/groups/${groupId}/posts/${postId}/like`, { method: 'POST' }),
  addComment: (groupId: string, postId: string, content: string) =>
    api.fetch(`/api/groups/${groupId}/posts/${postId}/comment`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  // Private Messages
  sendPrivateMessage: (receiverId: string, content: string) =>
    api.fetch('/api/messages', {
      method: 'POST',
      body: JSON.stringify({ receiver_id: receiverId, content }),
    }),
  getConversations: () => api.fetch('/api/messages'),
  getConversation: (otherUserId: string) => api.fetch(`/api/messages/${otherUserId}`),

  // Notifications
  getNotifications: () => api.fetch('/api/notifications'),
  getUnreadCount: () => api.fetch('/api/notifications/unread-count'),
  markNotificationRead: (notificationId: string) =>
    api.fetch(`/api/notifications/${notificationId}/read`, { method: 'POST' }),
  markAllNotificationsRead: () => api.fetch('/api/notifications/read-all', { method: 'POST' }),

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
  getRadios: (lang?: string, region?: string) => {
    let url = '/api/radios';
    const params = [];
    if (lang) params.push(`lang=${lang}`);
    if (region) params.push(`region=${region}`);
    if (params.length) url += `?${params.join('&')}`;
    return api.fetch(url);
  },

  // Worship Content
  getWorshipContent: (lang?: string) => api.fetch(`/api/worship${lang ? `?lang=${lang}` : ''}`),

  // Bible Study Tools
  getStudyData: (book: string, chapter: number, verse?: number) => {
    let url = `/api/bible/study/${encodeURIComponent(book)}/${chapter}`;
    if (verse) url += `?verse=${verse}`;
    return api.fetch(url);
  },
  createStudyNote: (book: string, chapter: number, verse: number | null, note: string, highlightColor: string | null, tags: string[]) =>
    api.fetch('/api/bible/study/notes', {
      method: 'POST',
      body: JSON.stringify({ book, chapter, verse, note, highlight_color: highlightColor, tags }),
    }),
  getStudyNotes: () => api.fetch('/api/bible/study/notes'),
  deleteStudyNote: (noteId: string) => api.fetch(`/api/bible/study/notes/${noteId}`, { method: 'DELETE' }),
  aiExplainVerse: (verseRef: string, verseText: string, question?: string, language?: string) =>
    api.fetch('/api/bible/study/ai-explain', {
      method: 'POST',
      body: JSON.stringify({ verse_ref: verseRef, verse_text: verseText, question, language }),
    }),

  // Settings
  updateSettings: (settings: any) =>
    api.fetch('/api/users/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),

  // Donations Config
  getDonationConfig: () => api.fetch('/api/donations/config'),

  // Quiz
  getQuizTopics: () => api.fetch('/api/quiz/topics'),
  getQuiz: (topic: string) => api.fetch(`/api/quiz/${topic}`),
  submitQuiz: (topic: string, answers: Record<string, number>) =>
    api.fetch('/api/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ topic, answers }),
    }),
  getQuizHistory: () => api.fetch('/api/quiz/history'),

  // Dictionary
  getDictionaryTerms: () => api.fetch('/api/dictionary'),
  getDictionaryTerm: (termId: string) => api.fetch(`/api/dictionary/${termId}`),
  searchDictionary: (query: string) => api.fetch(`/api/dictionary/search/${encodeURIComponent(query)}`),
  aiDictionaryStudy: (termId: string, question: string) =>
    api.fetch('/api/dictionary/ai-study', {
      method: 'POST',
      body: JSON.stringify({ term_id: termId, question }),
    }),

  // Study - Open Questions
  askQuestion: (question: string, topic?: string, language = 'it') =>
    api.fetch('/api/study/ask', {
      method: 'POST',
      body: JSON.stringify({ question, topic, language }),
    }),
  getStudyHistory: () => api.fetch('/api/study/history'),

  // Forum
  getForumCategories: () => api.fetch('/api/forum/categories'),
  createForumPost: (title: string, content: string, category: string, tags: string[] = []) =>
    api.fetch('/api/forum/posts', {
      method: 'POST',
      body: JSON.stringify({ title, content, category, tags }),
    }),
  getForumPosts: (category?: string, sort = 'recent') => {
    let url = '/api/forum/posts';
    const params = [];
    if (category) params.push(`category=${category}`);
    if (sort) params.push(`sort=${sort}`);
    if (params.length) url += `?${params.join('&')}`;
    return api.fetch(url);
  },
  getForumPost: (postId: string) => api.fetch(`/api/forum/posts/${postId}`),
  voteForumPost: (postId: string) => api.fetch(`/api/forum/posts/${postId}/vote`, { method: 'POST' }),
  replyForumPost: (postId: string, content: string) =>
    api.fetch(`/api/forum/posts/${postId}/reply`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
  getAIMentorReply: (postId: string) => api.fetch(`/api/forum/posts/${postId}/ai-mentor`, { method: 'POST' }),

  // Maps
  getMaps: () => api.fetch('/api/maps'),
  getMap: (mapId: string) => api.fetch(`/api/maps/${mapId}`),
  getLocationDetails: (mapId: string, locationName: string) =>
    api.fetch(`/api/maps/${mapId}/location/${encodeURIComponent(locationName)}`),

  // Live Events
  createEvent: (data: { title: string; description: string; event_type: string; scheduled_at: string; duration_minutes?: number; bible_book?: string; bible_chapter?: number }) =>
    api.fetch('/api/events', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getEvents: (status?: string) => api.fetch(`/api/events${status ? `?status=${status}` : ''}`),
  getEvent: (eventId: string) => api.fetch(`/api/events/${eventId}`),
  joinEvent: (eventId: string) => api.fetch(`/api/events/${eventId}/join`, { method: 'POST' }),
  startEvent: (eventId: string) => api.fetch(`/api/events/${eventId}/start`, { method: 'POST' }),
  endEvent: (eventId: string) => api.fetch(`/api/events/${eventId}/end`, { method: 'POST' }),

  // FAQ & Support
  getFaq: (category?: string) => api.fetch(`/api/faq${category ? `?category=${category}` : ''}`),
  getFaqCategories: () => api.fetch('/api/faq/categories'),
  contactSupport: (message: string) =>
    api.fetch('/api/support/contact', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
};
