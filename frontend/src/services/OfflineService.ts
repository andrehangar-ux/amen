import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

// Storage keys
const KEYS = {
  BIBLE_BOOKS: 'offline_bible_books',
  BIBLE_CHAPTERS: 'offline_bible_chapters',
  BIBLE_EDITIONS: 'offline_bible_editions',
  USER_NOTES: 'offline_user_notes',
  USER_BOOKMARKS: 'offline_user_bookmarks',
  QUIZ_DATA: 'offline_quiz_data',
  DOWNLOAD_STATUS: 'offline_download_status',
  LAST_SYNC: 'offline_last_sync',
};

// Editions to download for offline
const OFFLINE_EDITIONS = ['nuova_diodati', 'reina_valera', 'cei'];

// Languages to support
const OFFLINE_LANGUAGES = ['it', 'es', 'en', 'pt', 'fr', 'de'];

interface DownloadStatus {
  isDownloading: boolean;
  progress: number;
  totalItems: number;
  completedItems: number;
  currentItem: string;
  error?: string;
  lastDownload?: string;
}

interface OfflineChapter {
  book: string;
  chapter: number;
  edition: string;
  lang: string;
  verses: Array<{ verse: number; text: string }>;
  downloadedAt: string;
}

class OfflineService {
  private isOnline: boolean = true;
  private listeners: Set<(isOnline: boolean) => void> = new Set();

  constructor() {
    this.initNetworkListener();
  }

  // Initialize network state listener
  private initNetworkListener() {
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected ?? true;
      
      if (wasOnline !== this.isOnline) {
        this.notifyListeners();
      }
    });
  }

  // Subscribe to network changes
  onNetworkChange(callback: (isOnline: boolean) => void) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners() {
    this.listeners.forEach(cb => cb(this.isOnline));
  }

  // Check if online
  async checkOnline(): Promise<boolean> {
    const state = await NetInfo.fetch();
    this.isOnline = state.isConnected ?? true;
    return this.isOnline;
  }

  getOnlineStatus(): boolean {
    return this.isOnline;
  }

  // ==================== DOWNLOAD STATUS ====================

  async getDownloadStatus(): Promise<DownloadStatus> {
    try {
      const status = await AsyncStorage.getItem(KEYS.DOWNLOAD_STATUS);
      if (status) {
        return JSON.parse(status);
      }
    } catch (error) {
      console.error('Error getting download status:', error);
    }
    return {
      isDownloading: false,
      progress: 0,
      totalItems: 0,
      completedItems: 0,
      currentItem: '',
    };
  }

  private async updateDownloadStatus(status: Partial<DownloadStatus>) {
    try {
      const current = await this.getDownloadStatus();
      const updated = { ...current, ...status };
      await AsyncStorage.setItem(KEYS.DOWNLOAD_STATUS, JSON.stringify(updated));
    } catch (error) {
      console.error('Error updating download status:', error);
    }
  }

  // ==================== BIBLE BOOKS ====================

  async downloadBibleBooks(sessionToken: string, onProgress?: (progress: number) => void): Promise<boolean> {
    try {
      const booksData: Record<string, any[]> = {};
      
      for (let i = 0; i < OFFLINE_LANGUAGES.length; i++) {
        const lang = OFFLINE_LANGUAGES[i];
        const response = await fetch(`${API_URL}/api/bible/books?lang=${lang}`, {
          headers: {
            'Cookie': `session_token=${sessionToken}`,
            'bypass-tunnel-reminder': 'true',
          },
        });
        
        if (response.ok) {
          booksData[lang] = await response.json();
        }
        
        if (onProgress) {
          onProgress((i + 1) / OFFLINE_LANGUAGES.length * 100);
        }
      }
      
      await AsyncStorage.setItem(KEYS.BIBLE_BOOKS, JSON.stringify(booksData));
      return true;
    } catch (error) {
      console.error('Error downloading Bible books:', error);
      return false;
    }
  }

  async getBibleBooks(lang: string): Promise<any[] | null> {
    try {
      const data = await AsyncStorage.getItem(KEYS.BIBLE_BOOKS);
      if (data) {
        const booksData = JSON.parse(data);
        return booksData[lang] || booksData['it'] || null;
      }
    } catch (error) {
      console.error('Error getting offline Bible books:', error);
    }
    return null;
  }

  // ==================== BIBLE CHAPTERS ====================

  private getChapterKey(book: string, chapter: number, edition: string, lang: string): string {
    return `${lang}_${edition}_${book}_${chapter}`;
  }

  async downloadBibleChapter(
    book: string,
    chapter: number,
    edition: string,
    lang: string,
    sessionToken: string
  ): Promise<boolean> {
    try {
      const response = await fetch(
        `${API_URL}/api/bible/chapter/${encodeURIComponent(book)}/${chapter}?edition=${edition}&lang=${lang}`,
        {
          headers: {
            'Cookie': `session_token=${sessionToken}`,
            'bypass-tunnel-reminder': 'true',
          },
        }
      );
      
      if (!response.ok) return false;
      
      const data = await response.json();
      
      // Get existing chapters
      const chaptersJson = await AsyncStorage.getItem(KEYS.BIBLE_CHAPTERS);
      const chapters: Record<string, OfflineChapter> = chaptersJson ? JSON.parse(chaptersJson) : {};
      
      // Save chapter
      const key = this.getChapterKey(book, chapter, edition, lang);
      chapters[key] = {
        book,
        chapter,
        edition,
        lang,
        verses: data.verses || [],
        downloadedAt: new Date().toISOString(),
      };
      
      await AsyncStorage.setItem(KEYS.BIBLE_CHAPTERS, JSON.stringify(chapters));
      return true;
    } catch (error) {
      console.error('Error downloading Bible chapter:', error);
      return false;
    }
  }

  async getBibleChapter(book: string, chapter: number, edition: string, lang: string): Promise<OfflineChapter | null> {
    try {
      const chaptersJson = await AsyncStorage.getItem(KEYS.BIBLE_CHAPTERS);
      if (chaptersJson) {
        const chapters: Record<string, OfflineChapter> = JSON.parse(chaptersJson);
        const key = this.getChapterKey(book, chapter, edition, lang);
        return chapters[key] || null;
      }
    } catch (error) {
      console.error('Error getting offline Bible chapter:', error);
    }
    return null;
  }

  // Download entire Bible for offline use
  async downloadFullBible(
    sessionToken: string,
    onProgress?: (status: DownloadStatus) => void
  ): Promise<boolean> {
    try {
      await this.updateDownloadStatus({
        isDownloading: true,
        progress: 0,
        totalItems: 0,
        completedItems: 0,
        currentItem: 'Preparazione...',
      });

      // First download books list
      await this.downloadBibleBooks(sessionToken);
      
      // Get books for Italian (as reference for structure)
      const books = await this.getBibleBooks('it');
      if (!books) {
        throw new Error('Could not get Bible books');
      }

      // Calculate total chapters
      let totalChapters = 0;
      for (const book of books) {
        totalChapters += book.chapters;
      }
      
      // Total = chapters * editions * languages (but we download only main editions)
      const totalItems = totalChapters * OFFLINE_EDITIONS.length;
      let completedItems = 0;

      await this.updateDownloadStatus({
        totalItems,
        completedItems: 0,
        currentItem: 'Scaricamento capitoli...',
      });

      // Download chapters for each edition
      for (const edition of OFFLINE_EDITIONS) {
        const lang = edition === 'reina_valera' ? 'es' : 'it';
        
        for (const book of books) {
          for (let chapter = 1; chapter <= book.chapters; chapter++) {
            await this.downloadBibleChapter(book.name, chapter, edition, lang, sessionToken);
            
            completedItems++;
            const progress = (completedItems / totalItems) * 100;
            
            const status: DownloadStatus = {
              isDownloading: true,
              progress,
              totalItems,
              completedItems,
              currentItem: `${book.name} ${chapter} (${edition})`,
            };
            
            await this.updateDownloadStatus(status);
            if (onProgress) onProgress(status);
            
            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 100));
          }
        }
      }

      await this.updateDownloadStatus({
        isDownloading: false,
        progress: 100,
        completedItems: totalItems,
        currentItem: 'Completato!',
        lastDownload: new Date().toISOString(),
      });

      return true;
    } catch (error) {
      console.error('Error downloading full Bible:', error);
      await this.updateDownloadStatus({
        isDownloading: false,
        error: error instanceof Error ? error.message : 'Errore sconosciuto',
      });
      return false;
    }
  }

  // ==================== QUIZ DATA ====================

  async downloadQuizData(sessionToken: string): Promise<boolean> {
    try {
      // Download quiz categories
      const categoriesResponse = await fetch(`${API_URL}/api/quiz/categories`, {
        headers: {
          'Cookie': `session_token=${sessionToken}`,
          'bypass-tunnel-reminder': 'true',
        },
      });
      
      if (!categoriesResponse.ok) return false;
      const categories = await categoriesResponse.json();

      // Download advanced quiz categories
      const advancedResponse = await fetch(`${API_URL}/api/quiz/advanced-categories`, {
        headers: {
          'Cookie': `session_token=${sessionToken}`,
          'bypass-tunnel-reminder': 'true',
        },
      });
      
      const advancedCategories = advancedResponse.ok ? await advancedResponse.json() : [];

      // Download questions for each category
      const quizData: Record<string, any> = {
        categories,
        advancedCategories,
        questions: {},
      };

      for (const cat of categories) {
        const questionsResponse = await fetch(`${API_URL}/api/quiz/${cat.id}?lang=it`, {
          headers: {
            'Cookie': `session_token=${sessionToken}`,
            'bypass-tunnel-reminder': 'true',
          },
        });
        
        if (questionsResponse.ok) {
          quizData.questions[cat.id] = await questionsResponse.json();
        }
      }

      // Download advanced quiz questions
      for (const cat of advancedCategories) {
        const questionsResponse = await fetch(`${API_URL}/api/quiz/adv_${cat.id}?lang=it`, {
          headers: {
            'Cookie': `session_token=${sessionToken}`,
            'bypass-tunnel-reminder': 'true',
          },
        });
        
        if (questionsResponse.ok) {
          quizData.questions[`adv_${cat.id}`] = await questionsResponse.json();
        }
      }

      await AsyncStorage.setItem(KEYS.QUIZ_DATA, JSON.stringify(quizData));
      return true;
    } catch (error) {
      console.error('Error downloading quiz data:', error);
      return false;
    }
  }

  async getQuizCategories(): Promise<any[] | null> {
    try {
      const data = await AsyncStorage.getItem(KEYS.QUIZ_DATA);
      if (data) {
        const quizData = JSON.parse(data);
        return quizData.categories || null;
      }
    } catch (error) {
      console.error('Error getting offline quiz categories:', error);
    }
    return null;
  }

  async getQuizQuestions(categoryId: string): Promise<any[] | null> {
    try {
      const data = await AsyncStorage.getItem(KEYS.QUIZ_DATA);
      if (data) {
        const quizData = JSON.parse(data);
        return quizData.questions?.[categoryId] || null;
      }
    } catch (error) {
      console.error('Error getting offline quiz questions:', error);
    }
    return null;
  }

  // ==================== USER NOTES & BOOKMARKS ====================

  async saveUserNotes(notes: any[]): Promise<void> {
    try {
      await AsyncStorage.setItem(KEYS.USER_NOTES, JSON.stringify(notes));
    } catch (error) {
      console.error('Error saving user notes:', error);
    }
  }

  async getUserNotes(): Promise<any[]> {
    try {
      const data = await AsyncStorage.getItem(KEYS.USER_NOTES);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting user notes:', error);
      return [];
    }
  }

  async saveUserBookmarks(bookmarks: any[]): Promise<void> {
    try {
      await AsyncStorage.setItem(KEYS.USER_BOOKMARKS, JSON.stringify(bookmarks));
    } catch (error) {
      console.error('Error saving user bookmarks:', error);
    }
  }

  async getUserBookmarks(): Promise<any[]> {
    try {
      const data = await AsyncStorage.getItem(KEYS.USER_BOOKMARKS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting user bookmarks:', error);
      return [];
    }
  }

  // ==================== SYNC ====================

  async syncUserData(sessionToken: string): Promise<boolean> {
    try {
      // Download notes
      const notesResponse = await fetch(`${API_URL}/api/bible/notes`, {
        headers: {
          'Cookie': `session_token=${sessionToken}`,
          'bypass-tunnel-reminder': 'true',
        },
      });
      
      if (notesResponse.ok) {
        const notes = await notesResponse.json();
        await this.saveUserNotes(notes);
      }

      // Download bookmarks
      const bookmarksResponse = await fetch(`${API_URL}/api/bible/bookmarks`, {
        headers: {
          'Cookie': `session_token=${sessionToken}`,
          'bypass-tunnel-reminder': 'true',
        },
      });
      
      if (bookmarksResponse.ok) {
        const bookmarks = await bookmarksResponse.json();
        await this.saveUserBookmarks(bookmarks);
      }

      await AsyncStorage.setItem(KEYS.LAST_SYNC, new Date().toISOString());
      return true;
    } catch (error) {
      console.error('Error syncing user data:', error);
      return false;
    }
  }

  async getLastSyncTime(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(KEYS.LAST_SYNC);
    } catch (error) {
      return null;
    }
  }

  // ==================== STORAGE INFO ====================

  async getStorageInfo(): Promise<{ used: number; items: number }> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const offlineKeys = keys.filter(k => k.startsWith('offline_'));
      
      let totalSize = 0;
      for (const key of offlineKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }
      
      return {
        used: totalSize,
        items: offlineKeys.length,
      };
    } catch (error) {
      console.error('Error getting storage info:', error);
      return { used: 0, items: 0 };
    }
  }

  async clearOfflineData(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const offlineKeys = keys.filter(k => k.startsWith('offline_'));
      await AsyncStorage.multiRemove(offlineKeys);
    } catch (error) {
      console.error('Error clearing offline data:', error);
    }
  }

  // Check if Bible is available offline
  async isBibleAvailableOffline(): Promise<boolean> {
    try {
      const chaptersJson = await AsyncStorage.getItem(KEYS.BIBLE_CHAPTERS);
      if (chaptersJson) {
        const chapters = JSON.parse(chaptersJson);
        return Object.keys(chapters).length > 0;
      }
    } catch (error) {
      console.error('Error checking offline availability:', error);
    }
    return false;
  }
}

export const offlineService = new OfflineService();
export default offlineService;
