/**
 * Habit management screen — add, reorder, delete habits and non-negotiables.
 * Max 5 non-negotiables enforced here (matches backend rule).
 */
import { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, Alert, Switch, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';
const MAX_NON_NEG = 5;

interface Habit {
  id: number;
  name: string;
  is_non_negotiable: boolean;
  completed_today: boolean;
}

export default function HabitsManageScreen() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const queryClient = useQueryClient();
  const [newName, setNewName] = useState('');
  const [newIsNN, setNewIsNN] = useState(false);
  const [adding, setAdding] = useState(false);

  const { data: habits, isLoading } = useQuery<Habit[]>({
    queryKey: ['habits'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/habits`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    enabled: !!token,
  });

  const nnCount = habits?.filter(h => h.is_non_negotiable).length ?? 0;

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/habits`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim(), is_non_negotiable: newIsNN }),
      });
      if (!res.ok) throw new Error('Failed to create habit');
      return res.json();
    },
    onSuccess: () => {
      setNewName('');
      setNewIsNN(false);
      setAdding(false);
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
    onError: () => Alert.alert('Error', 'Could not add habit'),
  });

  const deleteMutation = useMutation({
    mutationFn: async (habitId: number) => {
      const res = await fetch(`${API_BASE}/habits/${habitId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['habits'] }),
  });

  const handleAdd = () => {
    if (!newName.trim()) return;
    if (newIsNN && nnCount >= MAX_NON_NEG) {
      Alert.alert(
        'Limit reached',
        `You can have at most ${MAX_NON_NEG} non-negotiables. Remove one first.`,
      );
      return;
    }
    createMutation.mutate();
  };

  const handleDelete = (habit: Habit) => {
    Alert.alert(
      'Remove habit',
      `Remove "${habit.name}"? Your completion history is preserved.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Remove', style: 'destructive', onPress: () => deleteMutation.mutate(habit.id) },
      ],
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: PAPER }]}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={[styles.back, { color: INK }]}>← BACK</Text>
        </TouchableOpacity>
        <Text style={[styles.header, { color: INK }]}>HABITS</Text>
        <TouchableOpacity onPress={() => setAdding(v => !v)}>
          <Text style={[styles.addBtn, { color: INK }]}>{adding ? '✕' : '+ ADD'}</Text>
        </TouchableOpacity>
      </View>

      {/* Add form */}
      {adding && (
        <View style={[styles.addForm, { borderColor: INK }]}>
          <TextInput
            style={[styles.addInput, { color: INK, borderColor: INK }]}
            value={newName}
            onChangeText={setNewName}
            placeholder="Habit name"
            placeholderTextColor="rgba(20,19,13,0.35)"
            autoFocus
            returnKeyType="done"
            onSubmitEditing={handleAdd}
          />
          <View style={styles.nnRow}>
            <Text style={[styles.nnLabel, { color: INK }]}>
              NON-NEGOTIABLE ({nnCount}/{MAX_NON_NEG})
            </Text>
            <Switch
              value={newIsNN}
              onValueChange={setNewIsNN}
              trackColor={{ false: 'rgba(20,19,13,0.1)', true: INK }}
              thumbColor={PAPER}
              disabled={!newIsNN && nnCount >= MAX_NON_NEG}
            />
          </View>
          <TouchableOpacity
            style={[styles.confirmBtn, { backgroundColor: INK, opacity: createMutation.isPending || !newName.trim() ? 0.4 : 1 }]}
            onPress={handleAdd}
            disabled={createMutation.isPending || !newName.trim()}
          >
            {createMutation.isPending
              ? <ActivityIndicator color={PAPER} />
              : <Text style={{ color: PAPER, fontWeight: '600', letterSpacing: 1, fontSize: 13 }}>ADD HABIT</Text>
            }
          </TouchableOpacity>
        </View>
      )}

      {isLoading ? (
        <ActivityIndicator color={INK} style={{ marginTop: 40 }} />
      ) : (
        <>
          {/* Non-negotiables section */}
          {(habits?.filter(h => h.is_non_negotiable) ?? []).length > 0 && (
            <Text style={[styles.sectionLabel, { color: INK }]}>NON-NEGOTIABLES</Text>
          )}
          <FlatList
            data={habits ?? []}
            keyExtractor={h => String(h.id)}
            renderItem={({ item }) => (
              <View style={styles.habitRow}>
                <View style={styles.habitLeft}>
                  {item.is_non_negotiable && (
                    <View style={[styles.nnDot, { backgroundColor: INK }]} />
                  )}
                  <Text style={[styles.habitName, { color: INK, opacity: item.is_non_negotiable ? 1 : 0.65 }]}>
                    {item.name}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => handleDelete(item)}
                  style={styles.deleteBtn}
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                >
                  <Text style={[styles.deleteTxt, { color: INK }]}>✕</Text>
                </TouchableOpacity>
              </View>
            )}
            contentContainerStyle={{ paddingBottom: 60 }}
            ListEmptyComponent={
              <Text style={[styles.empty, { color: INK }]}>
                No habits yet. Tap + ADD to create one.
              </Text>
            }
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 56 },
  topBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, marginBottom: 16 },
  back: { fontSize: 11, letterSpacing: 1 },
  header: { fontSize: 12, letterSpacing: 3, fontWeight: '700' },
  addBtn: { fontSize: 11, letterSpacing: 1.5, fontWeight: '600' },
  addForm: { marginHorizontal: 20, marginBottom: 16, borderWidth: 1, borderRadius: 2, padding: 14 },
  addInput: { borderWidth: 1, borderRadius: 2, padding: 10, fontSize: 15, marginBottom: 12 },
  nnRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  nnLabel: { fontSize: 10, letterSpacing: 1.5, fontWeight: '600' },
  confirmBtn: { padding: 12, borderRadius: 2, alignItems: 'center' },
  sectionLabel: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginHorizontal: 20, marginBottom: 8 },
  habitRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, paddingHorizontal: 20, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.07)' },
  habitLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  nnDot: { width: 6, height: 6, borderRadius: 3, marginRight: 10 },
  habitName: { fontSize: 15 },
  deleteBtn: { paddingLeft: 16 },
  deleteTxt: { fontSize: 14, opacity: 0.4 },
  empty: { textAlign: 'center', marginTop: 60, fontSize: 14, opacity: 0.4 },
});
