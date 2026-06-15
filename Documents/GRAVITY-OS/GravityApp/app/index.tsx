import { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';

export default function RootIndex() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);

  useEffect(() => {
    if (token) {
      router.replace('/(tabs)');
    } else {
      router.replace('/login');
    }
  }, [token]);

  return null;
}
