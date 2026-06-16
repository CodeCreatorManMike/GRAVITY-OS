import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface AuthState {
  token: string | null;
  userId: number | null;
  name: string | null;
  onboardingComplete: boolean | null;
  setAuth: (token: string, userId: number, name: string) => Promise<void>;
  setOnboardingComplete: (v: boolean) => void;
  clearAuth: () => Promise<void>;
  loadAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  userId: null,
  name: null,
  onboardingComplete: null,
  setAuth: async (token, userId, name) => {
    await SecureStore.setItemAsync('gravity_token', token);
    await SecureStore.setItemAsync('gravity_user_id', String(userId));
    set({ token, userId, name, onboardingComplete: null });
  },
  setOnboardingComplete: (v) => set({ onboardingComplete: v }),
  clearAuth: async () => {
    await SecureStore.deleteItemAsync('gravity_token');
    await SecureStore.deleteItemAsync('gravity_user_id');
    set({ token: null, userId: null, name: null, onboardingComplete: null });
  },
  loadAuth: async () => {
    const token = await SecureStore.getItemAsync('gravity_token');
    const userId = await SecureStore.getItemAsync('gravity_user_id');
    if (token && userId) {
      set({ token, userId: parseInt(userId), name: null, onboardingComplete: null });
    }
  },
}));
