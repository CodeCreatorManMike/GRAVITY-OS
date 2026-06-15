import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore(s => s.setAuth);
  const router = useRouter();

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
        Alert.alert('Login failed', 'Check your email and password');
        return;
      }
      const data = await res.json();
      await setAuth(data.access_token, data.user_id, data.name);
      router.replace('/');
    } catch {
      Alert.alert('Error', 'Could not connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: PAPER }]}>
      <Text style={[styles.title, { color: INK }]}>GRAVITY</Text>
      <TextInput
        style={[styles.input, { color: INK, borderColor: INK }]}
        placeholder="Email"
        placeholderTextColor="#888"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        style={[styles.input, { color: INK, borderColor: INK }]}
        placeholder="Password"
        placeholderTextColor="#888"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <TouchableOpacity
        style={[styles.btn, { backgroundColor: INK, opacity: loading ? 0.5 : 1 }]}
        onPress={login}
        disabled={loading}
      >
        <Text style={{ color: PAPER, fontWeight: '600', letterSpacing: 1 }}>
          {loading ? 'LOGGING IN...' : 'LOGIN'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 32 },
  title: { fontSize: 28, fontWeight: '700', letterSpacing: 4, marginBottom: 48, textAlign: 'center' },
  input: { borderWidth: 1, padding: 14, marginBottom: 12, fontSize: 15, borderRadius: 2 },
  btn: { padding: 16, borderRadius: 2, alignItems: 'center', marginTop: 8 },
});
