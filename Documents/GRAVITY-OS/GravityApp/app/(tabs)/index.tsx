import { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Modal } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';
import { useGravitySocket } from '../../hooks/useGravitySocket';

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

interface NudgeData {
  id: number;
  message: string;
  sub_message: string | null;
  action_label: string;
  category: string;
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
  const [activeNudge, setActiveNudge] = useState<NudgeData | null>(null);

  // WebSocket connection — live updates
  const { sendEvent } = useGravitySocket({
    onNudge: (data) => setActiveNudge(data),
    onCycleReviewReady: () => router.push('/review' as any),
  });

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

  const acknowledgeNudge = async () => {
    if (!activeNudge) return;
    try {
      await fetch(`${API_BASE}/nudges/${activeNudge.id}/acknowledge`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {}
    setActiveNudge(null);
  };

  const nonNeg = habits?.filter(h => h.is_non_negotiable) ?? [];
  const pct = goal ? Math.round(goal.likelihood_score * 100) : 0;
  const allDone = nonNeg.length > 0 && nonNeg.every(h => h.completed_today);

  return (
    <View style={[styles.container, { backgroundColor: PAPER }]}>
      {/* Goal header */}
      <View style={styles.goalSection}>
        <Text style={[styles.label, { color: INK }]}>CURRENT GOAL</Text>
        <Text style={[styles.goalText, { color: INK }]} numberOfLines={2}>
          {goal?.statement ?? '—'}
        </Text>
        <View style={styles.statsRow}>
          <View style={styles.statBlock}>
            <Text style={[styles.statNumber, { color: INK }]}>{pct}%</Text>
            <Text style={[styles.statLabel, { color: INK }]}>LIKELIHOOD</Text>
          </View>
          <View style={[styles.statDivider, { backgroundColor: INK }]} />
          <View style={styles.statBlock}>
            <Text style={[styles.statNumber, { color: INK }]}>{goal?.days_remaining ?? 0}</Text>
            <Text style={[styles.statLabel, { color: INK }]}>DAYS LEFT</Text>
          </View>
          <View style={[styles.statDivider, { backgroundColor: INK }]} />
          <View style={styles.statBlock}>
            <Text style={[styles.statNumber, { color: INK }]}>
              {nonNeg.filter(h => h.completed_today).length}/{nonNeg.length}
            </Text>
            <Text style={[styles.statLabel, { color: INK }]}>TODAY</Text>
          </View>
        </View>
      </View>

      <View style={[styles.divider, { backgroundColor: INK }]} />

      {/* Non-negotiables */}
      <Text style={[styles.label, { color: INK, marginHorizontal: 20, marginTop: 16 }]}>
        TODAY'S NON-NEGOTIABLES
      </Text>

      {allDone && (
        <View style={styles.allDoneBanner}>
          <Text style={[styles.allDoneText, { color: INK }]}>ALL DONE TODAY</Text>
        </View>
      )}

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
              {
                color: INK,
                textDecorationLine: item.completed_today ? 'line-through' : 'none',
                opacity: item.completed_today ? 0.35 : 1,
              },
            ]}>
              {item.name}
            </Text>
          </TouchableOpacity>
        )}
        contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40 }}
        refreshControl={
          <RefreshControl
            refreshing={habitsLoading || goalLoading}
            onRefresh={refetch}
            tintColor={INK}
          />
        }
      />

      {/* Nudge modal */}
      <Modal visible={!!activeNudge} transparent animationType="fade">
        <View style={styles.nudgeOverlay}>
          <View style={[styles.nudgeCard, { backgroundColor: INK }]}>
            <Text style={[styles.nudgeCategory, { color: PAPER }]}>
              {activeNudge?.category?.toUpperCase() ?? 'GRAVITY'}
            </Text>
            <Text style={[styles.nudgeMessage, { color: PAPER }]}>
              {activeNudge?.message}
            </Text>
            {activeNudge?.sub_message ? (
              <Text style={[styles.nudgeSubMessage, { color: PAPER }]}>
                {activeNudge.sub_message}
              </Text>
            ) : null}
            <TouchableOpacity
              style={[styles.nudgeDismiss, { borderColor: PAPER }]}
              onPress={acknowledgeNudge}
            >
              <Text style={{ color: PAPER, fontWeight: '600', letterSpacing: 2, fontSize: 12 }}>
                {activeNudge?.action_label?.toUpperCase() ?? 'DISMISS'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60 },
  goalSection: { paddingHorizontal: 20, paddingBottom: 16 },
  label: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginBottom: 8 },
  goalText: { fontSize: 17, lineHeight: 26, fontWeight: '500', marginBottom: 12 },
  statsRow: { flexDirection: 'row', alignItems: 'center' },
  statBlock: { flex: 1, alignItems: 'center' },
  statNumber: { fontSize: 22, fontWeight: '700', letterSpacing: -0.5 },
  statLabel: { fontSize: 9, letterSpacing: 1.5, opacity: 0.5, marginTop: 2 },
  statDivider: { width: 1, height: 32, opacity: 0.1 },
  divider: { height: 1, marginHorizontal: 20, opacity: 0.12, marginBottom: 4 },
  allDoneBanner: { marginHorizontal: 20, marginBottom: 8, paddingVertical: 6, alignItems: 'center' },
  allDoneText: { fontSize: 10, letterSpacing: 2, opacity: 0.5 },
  habitRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.06)' },
  checkbox: { width: 22, height: 22, borderWidth: 1.5, borderRadius: 2, marginRight: 12, justifyContent: 'center', alignItems: 'center' },
  habitName: { fontSize: 15, flex: 1 },
  nudgeOverlay: { flex: 1, backgroundColor: 'rgba(20,19,13,0.6)', justifyContent: 'center', alignItems: 'center', padding: 24 },
  nudgeCard: { width: '100%', borderRadius: 4, padding: 28 },
  nudgeCategory: { fontSize: 10, letterSpacing: 3, opacity: 0.6, marginBottom: 16 },
  nudgeMessage: { fontSize: 20, lineHeight: 30, fontWeight: '500', marginBottom: 12 },
  nudgeSubMessage: { fontSize: 14, lineHeight: 22, opacity: 0.7, marginBottom: 24 },
  nudgeDismiss: { borderWidth: 1, paddingVertical: 12, alignItems: 'center', borderRadius: 2 },
});
