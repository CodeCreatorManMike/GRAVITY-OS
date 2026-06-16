import { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

export default function RootIndex() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const onboardingComplete = useAuthStore(s => s.onboardingComplete);
  const setOnboardingComplete = useAuthStore(s => s.setOnboardingComplete);

  useEffect(() => {
    if (!token) {
      router.replace('/login');
      return;
    }

    // Fetch /auth/me to check onboarding status (null = not yet checked)
    if (onboardingComplete === null) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(data => {
          setOnboardingComplete(data.onboarding_complete ?? false);
        })
        .catch(() => {
          // Network error — assume onboarded, let home handle it
          setOnboardingComplete(true);
        });
      return;
    }

    if (onboardingComplete) {
      router.replace('/(tabs)');
    } else {
      router.replace('/onboarding');
    }
  }, [token, onboardingComplete]);

  return null;
}
