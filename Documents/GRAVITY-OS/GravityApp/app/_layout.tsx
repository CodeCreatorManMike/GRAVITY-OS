import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { useFonts } from 'expo-font';
import { useAuthStore } from '../store/authStore';
import { usePushNotifications } from '../hooks/usePushNotifications';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function AppInner() {
  usePushNotifications();
  return (
    <>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="login" />
        <Stack.Screen name="onboarding" />
        <Stack.Screen name="review" />
        <Stack.Screen name="goal-edit" />
        <Stack.Screen name="habits-manage" />
        <Stack.Screen name="faces" />
        <Stack.Screen name="files" />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  const loadAuth = useAuthStore(s => s.loadAuth);

  const [fontsLoaded] = useFonts({
    JetBrainsMono_400Regular: require('../assets/fonts/JetBrainsMono-Regular.ttf'),
    JetBrainsMono_700Bold: require('../assets/fonts/JetBrainsMono-Bold.ttf'),
    JetBrainsMono_500Medium: require('../assets/fonts/JetBrainsMono-Medium.ttf'),
  });

  useEffect(() => { loadAuth(); }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  );
}
