import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const DAILY_VERSE_NOTIFICATION_ID = 'daily-verse-reminder';
const NOTIFICATION_ENABLED_KEY = 'daily_verse_notification_enabled';
const NOTIFICATION_TIME_KEY = 'daily_verse_notification_time';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export class NotificationService {
  /**
   * Request notification permissions
   */
  static async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'web') {
      // Web notifications require a different approach
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
      }
      return false;
    }

    if (!Device.isDevice) {
      console.log('Push notifications require a physical device');
      return false;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Permission not granted for notifications');
      return false;
    }

    // Set up Android channel
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('daily-verse', {
        name: 'Versetto del Giorno',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4A7C59',
        sound: 'default',
      });
    }

    return true;
  }

  /**
   * Schedule daily verse notification
   */
  static async scheduleDailyVerseNotification(
    hour: number = 7,
    minute: number = 0
  ): Promise<boolean> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        return false;
      }

      // Cancel existing notification first
      await this.cancelDailyVerseNotification();

      // Schedule new notification
      const trigger: Notifications.NotificationTriggerInput = {
        type: Notifications.SchedulableTriggerInputTypes.DAILY,
        hour,
        minute,
      };

      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Versetto del Giorno',
          body: 'Inizia la giornata con una parola di Dio. Apri Amen! per leggerlo.',
          data: { type: 'daily-verse' },
          sound: 'default',
        },
        trigger,
        identifier: DAILY_VERSE_NOTIFICATION_ID,
      });

      // Save settings
      await AsyncStorage.setItem(NOTIFICATION_ENABLED_KEY, 'true');
      await AsyncStorage.setItem(NOTIFICATION_TIME_KEY, JSON.stringify({ hour, minute }));

      console.log(`Daily verse notification scheduled for ${hour}:${minute.toString().padStart(2, '0')}`);
      return true;
    } catch (error) {
      console.error('Error scheduling notification:', error);
      return false;
    }
  }

  /**
   * Cancel daily verse notification
   */
  static async cancelDailyVerseNotification(): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(DAILY_VERSE_NOTIFICATION_ID);
      await AsyncStorage.setItem(NOTIFICATION_ENABLED_KEY, 'false');
      console.log('Daily verse notification cancelled');
    } catch (error) {
      console.error('Error cancelling notification:', error);
    }
  }

  /**
   * Check if daily verse notification is enabled
   */
  static async isDailyVerseEnabled(): Promise<boolean> {
    try {
      const enabled = await AsyncStorage.getItem(NOTIFICATION_ENABLED_KEY);
      return enabled === 'true';
    } catch {
      return false;
    }
  }

  /**
   * Get notification time setting
   */
  static async getNotificationTime(): Promise<{ hour: number; minute: number }> {
    try {
      const time = await AsyncStorage.getItem(NOTIFICATION_TIME_KEY);
      if (time) {
        return JSON.parse(time);
      }
    } catch {}
    return { hour: 7, minute: 0 }; // Default: 7:00 AM
  }

  /**
   * Get all scheduled notifications (for debugging)
   */
  static async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    return await Notifications.getAllScheduledNotificationsAsync();
  }

  /**
   * Send a test notification immediately
   */
  static async sendTestNotification(): Promise<void> {
    const hasPermission = await this.requestPermissions();
    if (!hasPermission) {
      throw new Error('Permessi notifiche non concessi');
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title: 'Test Notifica Amen!',
        body: 'Le notifiche funzionano correttamente.',
        data: { type: 'test' },
        sound: 'default',
      },
      trigger: null, // null = immediate
    });
  }

  /**
   * Add listener for notifications received while app is in foreground
   */
  static addNotificationReceivedListener(
    callback: (notification: Notifications.Notification) => void
  ): Notifications.EventSubscription {
    return Notifications.addNotificationReceivedListener(callback);
  }

  /**
   * Add listener for when user interacts with notification
   */
  static addNotificationResponseReceivedListener(
    callback: (response: Notifications.NotificationResponse) => void
  ): Notifications.EventSubscription {
    return Notifications.addNotificationResponseReceivedListener(callback);
  }
}
