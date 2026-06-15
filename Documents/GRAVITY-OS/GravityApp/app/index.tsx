import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

interface Habit {
  id: number;
  name: string;
  is_non_negotiable: boolean;
  completed_today: boolean;
}

interface Goal {
  id: number;
  statement: string;
  likelihood_score: number;
  days_remaining: number;
}

function useApi<T>(key: string[], path: string) {
  const token = useAuthStore(s => s.token);
  return useQuery<T>({
    queryKey: key,
    queryFn: async () => {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Request failed');
      return res.json();
    },
    enabled: !!token,
  });
}

export default function HomeScreen() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const queryClient = useQueryClient();

  if (!token) {
    router.replace('/login');
    return null;
  }

  const { data: goal, isLoading: goalLoading } = useApi<Goal>(['goal'], '/goals');
  const { data: habits, isLoading: habitsLoading, refetch } = useApi<Habit[]>(['habits'], '/habits');

  const completeMutation = useMutation({
    mutationFn: async (habitId: number) => {
      const res = await fetch(`${API_BASE}/habits/${habitId}/complete`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to complete habit');
      return res.json();
    },
    onMutate: async (habitId: number) => {
      await queryClient.cancelQueries({ queryKey: ['habits'] });
      const previous = queryClient.getQueryData<Habit[]>(['habits']);
      queryClient.setQueryData<Habit[]>(['habits'], old =>
        old?.map(h => h.id === habitId ? { ...h, completed_today: true } : h) ?? []
      );
      return { previous };
    },
    onError: (_err, _habitId, context) => {
      queryClient.setQueryData(['habits'], context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
    },
  });

  const nonNeg = habits?.filter(h => h.is_non_negotiable) ?? [];
  const pct = goal ? Math.round(goal.likelihood_score * 100) : 0;

  return (
    <View style={[styles.container, { backgroundColor: PAPER }]}>
      <View style={styles.goalSection}>
        <Text style={[styles.label, { color: INK }]}>CURRENT GOAL</Text>
        <Text style={[styles.goalText, { color: INK }]} numberOfLines={2}>
          {goal?.statement ?? '—'}
        </Text>
        <View style={styles.statsRow}>
          <Text style={[styles.stat, { color: INK }]}>{pct}% likelihood</Text>
          <Text style={[styles.stat, { color: INK }]}>{goal?.days_remaining ?? 0}d remaining</Text>
        </View>
      </View>
      <View style={[styles.divider, { backgroundColor: INK }]} />
      <Text style={[styles.label, { color: INK, marginHorizontal: 20, marginTop: 16 }]}>
        TODAY'S NON-NEGOTIABLES
      </Text>
      <FlatList
        data={nonNeg}
        keyExtractor={h => String(h.id)}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.habitRow}
            onPress={() => !item.completed_today && completeMutation.mutate(item.id)}
            activeOpacity={item.completed_today ? 1 : 0.6}
          >
            <View style={[
              styles.checkbox,
              { borderColor: INK, backgroundColor: item.completed_today ? INK : 'transparent' },
            ]}>
              {item.completed_today && <Text style={{ color: PAPER, fontSize: 12 }}>✓</Text>}
            </View>
            <Text style={[
              styles.habitName,
              { color: INK, textDecorationLine: item.completed_today ? 'line-through' : 'none', opacity: item.completed_today ? 0.4 : 1 },
            ]}>
              {item.name}
            </Text>
          </TouchableOpacity>
        )}
        contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={habitsLoading || goalLoading} onRefresh={refetch} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60 },
  goalSection: { paddingHorizontal: 20, paddingBottom: 16 },
  label: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginBottom: 8 },
  goalText: { fontSize: 18, lineHeight: 26, fontWeight: '500' },
  statsRow: { flexDirection: 'row', gap: 16, marginTop: 8 },
  stat: { fontSize: 12, opacity: 0.6 },
  divider: { height: 1, marginHorizontal: 20, opacity: 0.15 },
  habitRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.08)' },
  checkbox: { width: 22, height: 22, borderWidth: 1.5, borderRadius: 2, marginRight: 12, justifyContent: 'center', alignItems: 'center' },
  habitName: { fontSize: 15, flex: 1 },
});
