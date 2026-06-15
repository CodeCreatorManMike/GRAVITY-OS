import { useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export function usePushNotifications() {
  const token = useAuthStore(s => s.token);
  const registeredRef = useRef(false);

  useEffect(() => {
    if (!token || registeredRef.current) return;
    registerForPush(token);
    registeredRef.current = true;
  }, [token]);
}

async function registerForPush(authToken: string) {
  if (!Device.isDevice) return;  // Expo Go simulator — skip

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;

  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') return;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('gravity', {
      name: 'GRAVITY',
      importance: Notifications.AndroidImportance.HIGH,
      sound: 'default',
    });
  }

  try {
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: 'gravity-app',  // replace with your Expo project ID
    });

    await fetch(`${API_BASE}/push/register`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: tokenData.data,
        platform: Platform.OS,
      }),
    });
  } catch {
    // Push setup failed — app continues without it
  }
}
