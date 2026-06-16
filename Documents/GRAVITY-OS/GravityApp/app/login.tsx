import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';
import { BG, SURFACE, WHITE, DIM, FAINT, BORDER } from '../constants/theme';

export default function LoginScreen() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const setAuth = useAuthStore(s => s.setAuth);
  const router  = useRouter();

  const login = async () => {
    if (!email || !password) return;
    setLoading(true);
    try {
      const body = new URLSearchParams({ username: email, password });
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      });
      if (!res.ok) {
        Alert.alert('Login failed', 'Check your credentials and try again.');
        return;
      }
      const data = await res.json();
      await setAuth(data.access_token, data.user_id, data.name);
      router.replace('/');
    } catch {
      Alert.alert('Error', 'Could not connect to server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Wordmark */}
      <View style={styles.top}>
        <Text style={styles.wordmark}>GRAVITY</Text>
        <Text style={styles.tagline}>Your personal operating system</Text>
      </View>

      {/* Form */}
      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor={DIM}
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          returnKeyType="next"
          keyboardAppearance="dark"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor={DIM}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          returnKeyType="done"
          onSubmitEditing={login}
          keyboardAppearance="dark"
        />
        <TouchableOpacity
          style={[styles.btn, { opacity: loading ? 0.5 : 1 }]}
          onPress={login}
          disabled={loading}
          activeOpacity={0.8}
        >
          <Text style={styles.btnText}>{loading ? 'SIGNING IN...' : 'SIGN IN'}</Text>
        </TouchableOpacity>
      </View>

      {/* Footer */}
      <Text style={styles.footer}>Gravity OS · Private beta</Text>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: BG,
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  top: {
    alignItems: 'center',
    marginBottom: 56,
  },
  wordmark: {
    fontSize: 36,
    fontWeight: '700',
    color: WHITE,
    letterSpacing: 8,
    marginBottom: 10,
  },
  tagline: {
    fontSize: 13,
    color: DIM,
    letterSpacing: 0.5,
  },
  form: {
    gap: 12,
  },
  input: {
    backgroundColor: SURFACE,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 10,
    padding: 16,
    fontSize: 15,
    color: WHITE,
  },
  btn: {
    backgroundColor: WHITE,
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  btnText: {
    color: BG,
    fontWeight: '700',
    fontSize: 13,
    letterSpacing: 2,
  },
  footer: {
    textAlign: 'center',
    color: FAINT,
    fontSize: 11,
    letterSpacing: 0.5,
    marginTop: 56,
  },
});
