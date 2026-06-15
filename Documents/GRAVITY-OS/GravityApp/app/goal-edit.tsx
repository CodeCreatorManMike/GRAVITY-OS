/**
 * Goal editing screen — edit statement, real_why, or create a new goal.
 * Reached from the home tab header or settings.
 */
import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

interface Goal {
  id: number;
  statement: string;
  real_why: string;
  likelihood_score: number;
  cycle_start: string;
  cycle_end: string;
  days_remaining: number;
}

export default function GoalEditScreen() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const queryClient = useQueryClient();

  const { data: goal, isLoading } = useQuery<Goal | null>({
    queryKey: ['goal'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/goals`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    enabled: !!token,
  });

  const [statement, setStatement] = useState('');
  const [realWhy, setRealWhy] = useState('');
  const [cycleLength, setCycleLength] = useState('180');
  const [isCreating, setIsCreating] = useState(false);

  // Pre-fill when goal loads
  useState(() => {
    if (goal) {
      setStatement(goal.statement);
      setRealWhy(goal.real_why);
    } else {
      setIsCreating(true);
    }
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!goal) {
        // Create new goal
        const res = await fetch(`${API_BASE}/goals`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            statement: statement.trim(),
            real_why: realWhy.trim(),
            cycle_length_days: parseInt(cycleLength) || 180,
          }),
        });
        if (!res.ok) throw new Error('Failed to create goal');
        return res.json();
      } else {
        const res = await fetch(`${API_BASE}/goals/${goal.id}`, {
          method: 'PUT',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            statement: statement.trim(),
            real_why: realWhy.trim(),
          }),
        });
        if (!res.ok) throw new Error('Failed to update goal');
        return res.json();
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goal'] });
      router.back();
    },
    onError: () => Alert.alert('Error', 'Could not save goal'),
  });

  const handleSave = () => {
    if (!statement.trim()) {
      Alert.alert('Required', 'Goal statement cannot be empty');
      return;
    }
    updateMutation.mutate();
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: PAPER, justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator color={INK} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: PAPER }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Text style={[styles.backText, { color: INK }]}>← BACK</Text>
        </TouchableOpacity>

        <Text style={[styles.header, { color: INK }]}>
          {!goal ? 'SET GOAL' : 'EDIT GOAL'}
        </Text>

        {goal && (
          <View style={styles.cycleInfo}>
            <Text style={[styles.cycleText, { color: INK }]}>
              {goal.cycle_start} → {goal.cycle_end} · {goal.days_remaining}d remaining
            </Text>
          </View>
        )}

        <Text style={[styles.label, { color: INK }]}>WHAT DO YOU WANT TO ACHIEVE?</Text>
        <TextInput
          style={[styles.input, styles.inputLarge, { color: INK, borderColor: INK }]}
          value={statement}
          onChangeText={setStatement}
          placeholder="e.g. Release my first EP and grow my audience to 1,000 followers"
          placeholderTextColor="rgba(20,19,13,0.35)"
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />

        <Text style={[styles.label, { color: INK }]}>WHY DOES THIS MATTER?</Text>
        <TextInput
          style={[styles.input, styles.inputLarge, { color: INK, borderColor: INK }]}
          value={realWhy}
          onChangeText={setRealWhy}
          placeholder="Be honest — what's the real reason this matters to you?"
          placeholderTextColor="rgba(20,19,13,0.35)"
          multiline
          numberOfLines={3}
          textAlignVertical="top"
        />

        {!goal && (
          <>
            <Text style={[styles.label, { color: INK }]}>CYCLE LENGTH (DAYS)</Text>
            <TextInput
              style={[styles.input, { color: INK, borderColor: INK }]}
              value={cycleLength}
              onChangeText={setCycleLength}
              keyboardType="number-pad"
              maxLength={3}
            />
            <Text style={[styles.hint, { color: INK }]}>Default 180 days (6 months)</Text>
          </>
        )}

        <TouchableOpacity
          style={[styles.saveBtn, { backgroundColor: INK, opacity: updateMutation.isPending ? 0.5 : 1 }]}
          onPress={handleSave}
          disabled={updateMutation.isPending}
        >
          {updateMutation.isPending
            ? <ActivityIndicator color={PAPER} />
            : <Text style={{ color: PAPER, fontWeight: '700', letterSpacing: 2, fontSize: 13 }}>SAVE</Text>
          }
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20, paddingTop: 60, paddingBottom: 60 },
  backBtn: { marginBottom: 24 },
  backText: { fontSize: 11, letterSpacing: 1.5 },
  header: { fontSize: 13, letterSpacing: 3, fontWeight: '700', marginBottom: 8 },
  cycleInfo: { marginBottom: 24 },
  cycleText: { fontSize: 12, opacity: 0.45 },
  label: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginTop: 20, marginBottom: 8 },
  input: { borderWidth: 1, borderRadius: 2, padding: 12, fontSize: 15 },
  inputLarge: { minHeight: 100, textAlignVertical: 'top' },
  hint: { fontSize: 11, opacity: 0.4, marginTop: 4 },
  saveBtn: { marginTop: 32, padding: 16, borderRadius: 2, alignItems: 'center' },
});
