import PushNotification from 'react-native-push-notification';

export class NotificationService {
  private static instance: NotificationService;
  
  private constructor() {}
  
  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }
  
  static async initialize(): Promise<void> {
    try {
      PushNotification.configure({
        onRegister: function (token) {
          console.log('TOKEN:', token);
        },
        onNotification: function (notification) {
          console.log('NOTIFICATION:', notification);
        },
        permissions: {
          alert: true,
          badge: true,
          sound: true,
        },
        popInitialNotification: true,
        requestPermissions: Platform.OS === 'ios',
      });
    } catch (error) {
      console.error('NotificationService initialization error:', error);
    }
  }
  
  static async showNotification(
    title: string,
    message: string,
    data?: any
  ): Promise<void> {
    try {
      PushNotification.localNotification({
        channelId: 'worldwidecoin',
        title,
        message,
        playSound: true,
        soundName: 'default',
        actions: ['View'],
        userInfo: data,
      });
    } catch (error) {
      console.error('Show notification error:', error);
    }
  }
  
  static async scheduleNotification(
    title: string,
    message: string,
    date: Date,
    data?: any
  ): Promise<void> {
    try {
      PushNotification.localNotificationSchedule({
        channelId: 'worldwidecoin',
        title,
        message,
        date,
        playSound: true,
        soundName: 'default',
        userInfo: data,
      });
    } catch (error) {
      console.error('Schedule notification error:', error);
    }
  }
  
  static async cancelAllNotifications(): Promise<void> {
    try {
      PushNotification.cancelAllLocalNotifications();
    } catch (error) {
      console.error('Cancel notifications error:', error);
    }
  }
}
