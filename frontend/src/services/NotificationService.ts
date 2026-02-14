import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../utils/api';

const DAILY_VERSE_NOTIFICATION_ID = 'daily-verse-notification';
const NOTIFICATION_ENABLED_KEY = '@notification_enabled';
const NOTIFICATION_TIME_KEY = '@notification_time';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export class NotificationService {
  static async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'web') {
      // Web notifications
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
      }
      return false;
    }

    if (Device.isDevice) {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      return finalStatus === 'granted';
    }

    return false;
  }

  static async scheduleDailyVerseNotification(hour: number = 8, minute: number = 0): Promise<boolean> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        console.log('Notification permissions not granted');
        return false;
      }

      // Cancel any existing daily verse notifications
      await this.cancelDailyVerseNotification();

      // Get current language from storage
      const language = await AsyncStorage.getItem('@language') || 'it';
      
      // Fetch daily verse for notification content
      let verseText = 'Apri Amen! per leggere il versetto del giorno';
      let verseRef = 'Versetto del Giorno';
      
      try {
        const verse = await api.getDailyVerse(language);
        if (verse && verse.text) {
          verseText = verse.text.substring(0, 150) + (verse.text.length > 150 ? '...' : '');
          verseRef = verse.reference || 'Versetto del Giorno';
        }
      } catch (error) {
        console.log('Could not fetch verse for notification:', error);
      }

      if (Platform.OS === 'web') {
        // For web, we'll use a simpler approach with localStorage reminder
        await AsyncStorage.setItem(NOTIFICATION_ENABLED_KEY, 'true');
        await AsyncStorage.setItem(NOTIFICATION_TIME_KEY, JSON.stringify({ hour, minute }));
        console.log('Web notification reminder set');
        return true;
      }

      // Schedule notification for mobile
      await Notifications.scheduleNotificationAsync({
        content: {
          title: `${verseRef}`,
          body: verseText,
          data: { type: 'daily_verse' },
          sound: true,
        },
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DAILY,
          hour: hour,
          minute: minute,
        },
        identifier: DAILY_VERSE_NOTIFICATION_ID,
      });

      await AsyncStorage.setItem(NOTIFICATION_ENABLED_KEY, 'true');
      await AsyncStorage.setItem(NOTIFICATION_TIME_KEY, JSON.stringify({ hour, minute }));
      
      console.log(`Daily verse notification scheduled for ${hour}:${minute}`);
      return true;
    } catch (error) {
      console.error('Error scheduling notification:', error);
      return false;
    }
  }

  static async cancelDailyVerseNotification(): Promise<void> {
    try {
      if (Platform.OS !== 'web') {
        await Notifications.cancelScheduledNotificationAsync(DAILY_VERSE_NOTIFICATION_ID);
      }
      await AsyncStorage.setItem(NOTIFICATION_ENABLED_KEY, 'false');
    } catch (error) {
      console.log('Error canceling notification:', error);
    }
  }

  static async isNotificationEnabled(): Promise<boolean> {
    const enabled = await AsyncStorage.getItem(NOTIFICATION_ENABLED_KEY);
    return enabled === 'true';
  }

  static async getNotificationTime(): Promise<{ hour: number; minute: number }> {
    const timeStr = await AsyncStorage.getItem(NOTIFICATION_TIME_KEY);
    if (timeStr) {
      return JSON.parse(timeStr);
    }
    return { hour: 8, minute: 0 }; // Default 8:00 AM
  }

  static async sendImmediateNotification(title: string, body: string, data?: any): Promise<void> {
    if (Platform.OS === 'web') {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body, icon: '/icon.png' });
      }
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
      },
      trigger: null, // Immediate
    });
  }

  static async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    if (Platform.OS === 'web') return [];
    return await Notifications.getAllScheduledNotificationsAsync();
  }
}

export default NotificationService;
