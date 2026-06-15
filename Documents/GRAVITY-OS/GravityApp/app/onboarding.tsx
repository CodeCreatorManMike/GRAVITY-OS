import { useState, useRef, useEffect } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  KeyboardAvoidingView, Platform, StyleSheet, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

interface Message {
  id: string;
  role: 'ai' | 'user';
  text: string;
}

export default function OnboardingScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState(1);
  const flatListRef = useRef<FlatList>(null);
  const router = useRouter();
  const token = useAuthStore(s => s.token);

  useEffect(() => {
    startOnboarding();
  }, []);

  const startOnboarding = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/onboarding/start`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setMessages([{ id: '0', role: 'ai', text: data.message }]);
      setPhase(data.phase);
    } catch {
      setMessages([{ id: '0', role: 'ai', text: 'Connection error. Is the server running?' }]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput('');
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: userText };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/onboarding/message`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userText }),
      });
      const data = await res.json();
      const aiMsg: Message = { id: (Date.now() + 1).toString(), role: 'ai', text: data.message };
      setMessages(prev => [...prev, aiMsg]);
      setPhase(data.phase);
      if (data.onboarding_complete) {
        setTimeout(() => router.replace('/'), 1500);
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { id: Date.now().toString(), role: 'ai', text: 'Something went wrong.' },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: PAPER }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <Text style={[styles.header, { color: INK }]}>GRAVITY — Phase {phase}/5</Text>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={({ item }) => (
          <View style={[
            styles.bubble,
            item.role === 'ai' ? styles.aiBubble : styles.userBubble,
          ]}>
            <Text style={[styles.bubbleText, { color: INK }]}>{item.text}</Text>
          </View>
        )}
        style={styles.list}
        contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: false })}
      />
      {loading && <ActivityIndicator style={{ marginBottom: 8 }} color={INK} />}
      <View style={styles.inputRow}>
        <TextInput
          style={[styles.input, { color: INK, borderColor: INK }]}
          value={input}
          onChangeText={setInput}
          placeholder="Type here..."
          placeholderTextColor="#888"
          onSubmitEditing={sendMessage}
          returnKeyType="send"
          editable={!loading}
          multiline
        />
        <TouchableOpacity
          onPress={sendMessage}
          disabled={loading || !input.trim()}
          style={[styles.sendBtn, { backgroundColor: INK, opacity: (loading || !input.trim()) ? 0.4 : 1 }]}
        >
          <Text style={{ color: PAPER, fontWeight: 'bold' }}>→</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { paddingTop: 60, paddingHorizontal: 16, paddingBottom: 8, fontSize: 12, letterSpacing: 2, fontWeight: '600' },
  list: { flex: 1 },
  bubble: { marginVertical: 4, maxWidth: '85%', padding: 12, borderRadius: 2 },
  aiBubble: { alignSelf: 'flex-start', backgroundColor: 'transparent' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#e0dfd7' },
  bubbleText: { fontSize: 15, lineHeight: 22 },
  inputRow: { flexDirection: 'row', padding: 12, paddingBottom: 32, gap: 8 },
  input: { flex: 1, borderWidth: 1, padding: 10, fontSize: 15, borderRadius: 2, maxHeight: 100 },
  sendBtn: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center', borderRadius: 2 },
});
