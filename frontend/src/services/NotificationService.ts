import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const DAILY_VERSE_NOTIFICATION_ID = 'daily-verse-reminder';
const QUIZ_NOTIFICATION_ID = 'quiz-reminder';
const READING_NOTIFICATION_ID = 'reading-reminder';

const NOTIFICATION_KEYS = {
  verseEnabled: 'notif_verse_enabled',
  verseTime: 'notif_verse_time',
  quizEnabled: 'notif_quiz_enabled',
  quizTime: 'notif_quiz_time',
  readingEnabled: 'notif_reading_enabled',
  readingTime: 'notif_reading_time',
};

const NOTIFICATION_MESSAGES = {
  it: {
    verseTitle: 'Versetto del Giorno',
    verseBody: 'Buongiorno! Un nuovo versetto ti aspetta. Inizia la giornata con la Parola di Dio.',
    quizTitle: 'Quiz Biblico',
    quizBody: 'Metti alla prova la tua conoscenza biblica! Un nuovo quiz ti aspetta.',
    readingTitle: 'Tempo di Lettura',
    readingBody: 'Hai letto la Bibbia oggi? Dedica qualche minuto alla lettura.',
  },
  en: {
    verseTitle: 'Verse of the Day',
    verseBody: 'Good morning! A new verse awaits you. Start your day with God\'s Word.',
    quizTitle: 'Bible Quiz',
    quizBody: 'Test your Bible knowledge! A new quiz is waiting for you.',
    readingTitle: 'Reading Time',
    readingBody: 'Have you read the Bible today? Take a few minutes to read.',
  },
  es: {
    verseTitle: 'Versiculo del Dia',
    verseBody: 'Buenos dias! Un nuevo versiculo te espera. Comienza el dia con la Palabra de Dios.',
    quizTitle: 'Quiz Biblico',
    quizBody: 'Pon a prueba tu conocimiento biblico! Un nuevo quiz te espera.',
    readingTitle: 'Tiempo de Lectura',
    readingBody: 'Has leido la Biblia hoy? Dedica unos minutos a la lectura.',
  },
  pt: {
    verseTitle: 'Versiculo do Dia',
    verseBody: 'Bom dia! Um novo versiculo espera por voce. Comece o dia com a Palavra de Deus.',
    quizTitle: 'Quiz Biblico',
    quizBody: 'Teste seu conhecimento biblico! Um novo quiz espera por voce.',
    readingTitle: 'Tempo de Leitura',
    readingBody: 'Voce leu a Biblia hoje? Dedique alguns minutos a leitura.',
  },
  fr: {
    verseTitle: 'Verset du Jour',
    verseBody: 'Bonjour! Un nouveau verset vous attend. Commencez la journee avec la Parole de Dieu.',
    quizTitle: 'Quiz Biblique',
    quizBody: 'Testez vos connaissances bibliques! Un nouveau quiz vous attend.',
    readingTitle: 'Temps de Lecture',
    readingBody: 'Avez-vous lu la Bible aujourd\'hui? Prenez quelques minutes pour lire.',
  },
  de: {
    verseTitle: 'Vers des Tages',
    verseBody: 'Guten Morgen! Ein neuer Vers wartet auf Sie. Beginnen Sie den Tag mit Gottes Wort.',
    quizTitle: 'Bibel-Quiz',
    quizBody: 'Testen Sie Ihr Bibelwissen! Ein neues Quiz wartet auf Sie.',
    readingTitle: 'Lesezeit',
    readingBody: 'Haben Sie heute in der Bibel gelesen? Nehmen Sie sich ein paar Minuten.',
  },
};

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export class NotificationService {
  static async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'web') {
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
      }
      return false;
    }

    if (!Device.isDevice) {
      return false;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      return false;
    }

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('daily-verse', {
        name: 'Versetto del Giorno',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4A7C59',
        sound: 'default',
      });
      await Notifications.setNotificationChannelAsync('quiz-reminder', {
        name: 'Promemoria Quiz',
        importance: Notifications.AndroidImportance.DEFAULT,
        sound: 'default',
      });
      await Notifications.setNotificationChannelAsync('reading-reminder', {
        name: 'Promemoria Lettura',
        importance: Notifications.AndroidImportance.DEFAULT,
        sound: 'default',
      });
    }

    return true;
  }

  // ========== DAILY VERSE ==========
  static async scheduleDailyVerseNotification(hour: number = 7, minute: number = 0, lang: string = 'it'): Promise<boolean> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) return false;

      await this.cancelNotification(DAILY_VERSE_NOTIFICATION_ID);
      const msgs = NOTIFICATION_MESSAGES[lang as keyof typeof NOTIFICATION_MESSAGES] || NOTIFICATION_MESSAGES.it;

      await Notifications.scheduleNotificationAsync({
        content: {
          title: msgs.verseTitle,
          body: msgs.verseBody,
          data: { type: 'daily-verse', screen: '/(tabs)/bible' },
          sound: 'default',
        },
        trigger: { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour, minute },
        identifier: DAILY_VERSE_NOTIFICATION_ID,
      });

      await AsyncStorage.setItem(NOTIFICATION_KEYS.verseEnabled, 'true');
      await AsyncStorage.setItem(NOTIFICATION_KEYS.verseTime, JSON.stringify({ hour, minute }));
      return true;
    } catch (error) {
      console.error('Error scheduling verse notification:', error);
      return false;
    }
  }

  static async cancelDailyVerseNotification(): Promise<void> {
    await this.cancelNotification(DAILY_VERSE_NOTIFICATION_ID);
    await AsyncStorage.setItem(NOTIFICATION_KEYS.verseEnabled, 'false');
  }

  // ========== QUIZ REMINDER ==========
  static async scheduleQuizNotification(hour: number = 12, minute: number = 0, lang: string = 'it'): Promise<boolean> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) return false;

      await this.cancelNotification(QUIZ_NOTIFICATION_ID);
      const msgs = NOTIFICATION_MESSAGES[lang as keyof typeof NOTIFICATION_MESSAGES] || NOTIFICATION_MESSAGES.it;

      await Notifications.scheduleNotificationAsync({
        content: {
          title: msgs.quizTitle,
          body: msgs.quizBody,
          data: { type: 'quiz', screen: '/quiz' },
          sound: 'default',
        },
        trigger: { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour, minute },
        identifier: QUIZ_NOTIFICATION_ID,
      });

      await AsyncStorage.setItem(NOTIFICATION_KEYS.quizEnabled, 'true');
      await AsyncStorage.setItem(NOTIFICATION_KEYS.quizTime, JSON.stringify({ hour, minute }));
      return true;
    } catch (error) {
      console.error('Error scheduling quiz notification:', error);
      return false;
    }
  }

  static async cancelQuizNotification(): Promise<void> {
    await this.cancelNotification(QUIZ_NOTIFICATION_ID);
    await AsyncStorage.setItem(NOTIFICATION_KEYS.quizEnabled, 'false');
  }

  // ========== READING REMINDER ==========
  static async scheduleReadingNotification(hour: number = 20, minute: number = 0, lang: string = 'it'): Promise<boolean> {
    try {
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) return false;

      await this.cancelNotification(READING_NOTIFICATION_ID);
      const msgs = NOTIFICATION_MESSAGES[lang as keyof typeof NOTIFICATION_MESSAGES] || NOTIFICATION_MESSAGES.it;

      await Notifications.scheduleNotificationAsync({
        content: {
          title: msgs.readingTitle,
          body: msgs.readingBody,
          data: { type: 'reading', screen: '/(tabs)/bible' },
          sound: 'default',
        },
        trigger: { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour, minute },
        identifier: READING_NOTIFICATION_ID,
      });

      await AsyncStorage.setItem(NOTIFICATION_KEYS.readingEnabled, 'true');
      await AsyncStorage.setItem(NOTIFICATION_KEYS.readingTime, JSON.stringify({ hour, minute }));
      return true;
    } catch (error) {
      console.error('Error scheduling reading notification:', error);
      return false;
    }
  }

  static async cancelReadingNotification(): Promise<void> {
    await this.cancelNotification(READING_NOTIFICATION_ID);
    await AsyncStorage.setItem(NOTIFICATION_KEYS.readingEnabled, 'false');
  }

  // ========== HELPERS ==========
  private static async cancelNotification(id: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(id);
    } catch {}
  }

  static async getSettings() {
    const [verseEnabled, verseTime, quizEnabled, quizTime, readingEnabled, readingTime] = await Promise.all([
      AsyncStorage.getItem(NOTIFICATION_KEYS.verseEnabled),
      AsyncStorage.getItem(NOTIFICATION_KEYS.verseTime),
      AsyncStorage.getItem(NOTIFICATION_KEYS.quizEnabled),
      AsyncStorage.getItem(NOTIFICATION_KEYS.quizTime),
      AsyncStorage.getItem(NOTIFICATION_KEYS.readingEnabled),
      AsyncStorage.getItem(NOTIFICATION_KEYS.readingTime),
    ]);

    return {
      verse: {
        enabled: verseEnabled === 'true',
        hour: verseTime ? JSON.parse(verseTime).hour : 7,
        minute: verseTime ? JSON.parse(verseTime).minute : 0,
      },
      quiz: {
        enabled: quizEnabled === 'true',
        hour: quizTime ? JSON.parse(quizTime).hour : 12,
        minute: quizTime ? JSON.parse(quizTime).minute : 0,
      },
      reading: {
        enabled: readingEnabled === 'true',
        hour: readingTime ? JSON.parse(readingTime).hour : 20,
        minute: readingTime ? JSON.parse(readingTime).minute : 0,
      },
    };
  }

  // Legacy compatibility
  static async isDailyVerseEnabled(): Promise<boolean> {
    const settings = await this.getSettings();
    return settings.verse.enabled;
  }

  static async getNotificationTime(): Promise<{ hour: number; minute: number }> {
    const settings = await this.getSettings();
    return { hour: settings.verse.hour, minute: settings.verse.minute };
  }

  static async sendTestNotification(): Promise<void> {
    const hasPermission = await this.requestPermissions();
    if (!hasPermission) throw new Error('Permessi notifiche non concessi');

    await Notifications.scheduleNotificationAsync({
      content: {
        title: 'Test Notifica Amen!',
        body: 'Le notifiche funzionano correttamente.',
        data: { type: 'test' },
        sound: 'default',
      },
      trigger: null,
    });
  }

  static addNotificationReceivedListener(callback: (notification: Notifications.Notification) => void) {
    return Notifications.addNotificationReceivedListener(callback);
  }

  static addNotificationResponseReceivedListener(callback: (response: Notifications.NotificationResponse) => void) {
    return Notifications.addNotificationResponseReceivedListener(callback);
  }
}
