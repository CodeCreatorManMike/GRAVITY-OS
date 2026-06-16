import { useState, useRef, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl, Modal, ScrollView, Dimensions,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';
import { useGravitySocket } from '../../hooks/useGravitySocket';
import DevicePreview, { FaceCard } from '../../components/DevicePreview';

const INK = '#14130d';
const PAPER = '#f4f2ea';
const SCREEN_W = Dimensions.get('window').width;
const FACE_SIZE = Math.min(SCREEN_W * 0.62, 240);
const FACES_CACHE_KEY = 'gravity_faces_v1';

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

interface DeviceState {
  generated_at: string;
  faces: FaceCard[];
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

// ── Face carousel ─────────────────────────────────────────────────────────────

function FaceCarousel({ faces, offline }: { faces: FaceCard[]; offline: boolean }) {
  const [activeIdx, setActiveIdx] = useState(0);
  const scrollRef = useRef<ScrollView>(null);

  const handleScroll = useCallback((e: any) => {
    const idx = Math.round(e.nativeEvent.contentOffset.x / SCREEN_W);
    setActiveIdx(idx);
  }, []);

  if (faces.length === 0) {
    return (
      <View style={carousel.wrapper}>
        <DevicePreview face={null} size={FACE_SIZE} offline={offline} />
      </View>
    );
  }

  return (
    <View style={carousel.wrapper}>
      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={handleScroll}
        decelerationRate="fast"
        style={{ width: SCREEN_W }}
      >
        {faces.map((face, i) => (
          <View key={i} style={[carousel.page, { width: SCREEN_W }]}>
            <DevicePreview face={face} size={FACE_SIZE} offline={offline} />
          </View>
        ))}
      </ScrollView>
      {faces.length > 1 && (
        <View style={carousel.dots}>
          {faces.map((_, i) => (
            <View key={i} style={[carousel.dot, { backgroundColor: i === activeIdx ? INK : 'rgba(20,19,13,0.2)' }]} />
          ))}
        </View>
      )}
    </View>
  );
}

const carousel = StyleSheet.create({
  wrapper: { alignItems: 'center', paddingVertical: 20 },
  page: { alignItems: 'center', justifyContent: 'center' },
  dots: { flexDirection: 'row', gap: 6, marginTop: 12 },
  dot: { width: 5, height: 5, borderRadius: 2.5 },
});

// ── Main screen ───────────────────────────────────────────────────────────────

export default function HomeScreen() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const queryClient = useQueryClient();
  const [activeNudge, setActiveNudge] = useState<NudgeData | null>(null);
  const [cachedFaces, setCachedFaces] = useState<FaceCard[]>([]);

  const { sendEvent, isConnected } = useGravitySocket({
    onNudge: (data) => setActiveNudge(data),
    onCycleReviewReady: () => router.push('/review' as any),
  });

  if (!token) {
    router.replace('/login');
    return null;
  }

  const { data: goal, isLoading: goalLoading } = useApi<Goal>(['goal'], '/goals');
  const { data: habits, isLoading: habitsLoading, refetch } = useApi<Habit[]>(['habits'], '/habits');

  const { data: deviceState, isError: deviceError } = useQuery<DeviceState>({
    queryKey: ['device_state'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/device/state`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      // Cache for offline use
      await AsyncStorage.setItem(FACES_CACHE_KEY, JSON.stringify(data.faces));
      return data;
    },
    enabled: !!token,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  // Load cache if device state fetch failed
  const facesToShow = deviceState?.faces ?? cachedFaces;
  const isOffline = deviceError && cachedFaces.length > 0;

  // Load cache on mount (background)
  useState(() => {
    AsyncStorage.getItem(FACES_CACHE_KEY).then(raw => {
      if (raw) {
        try { setCachedFaces(JSON.parse(raw)); } catch {}
      }
    });
  });

  const completeMutation = useMutation({
    mutationFn: async (habitId: number) => {
      const res = await fetch(`${API_BASE}/habits/${habitId}/complete`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
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
    onError: (_err, _id, context) => {
      queryClient.setQueryData(['habits'], context?.previous);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['habits'] }),
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
      {/* Connection indicator */}
      <View style={styles.connRow}>
        <Text style={[styles.connLabel, { color: INK }]}>GRAVITY</Text>
        <View style={[styles.connDot, { backgroundColor: isConnected ? INK : 'rgba(20,19,13,0.25)' }]} />
      </View>

      <FlatList
        data={nonNeg}
        keyExtractor={h => String(h.id)}
        ListHeaderComponent={
          <>
            {/* Device face carousel */}
            <FaceCarousel faces={facesToShow} offline={!!isOffline} />

            {/* Goal stats */}
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

            <Text style={[styles.label, { color: INK, marginHorizontal: 20, marginTop: 16 }]}>
              TODAY'S NON-NEGOTIABLES
            </Text>

            {allDone && (
              <View style={styles.allDoneBanner}>
                <Text style={[styles.allDoneText, { color: INK }]}>ALL DONE TODAY</Text>
              </View>
            )}
          </>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.habitRow}
            onPress={() => !item.completed_today && completeMutation.mutate(item.id)}
            activeOpacity={item.completed_today ? 1 : 0.6}
          >
            <View style={[styles.checkbox, { borderColor: INK, backgroundColor: item.completed_today ? INK : 'transparent' }]}>
              {item.completed_today && <Text style={{ color: PAPER, fontSize: 12 }}>✓</Text>}
            </View>
            <Text style={[styles.habitName, {
              color: INK,
              textDecorationLine: item.completed_today ? 'line-through' : 'none',
              opacity: item.completed_today ? 0.35 : 1,
            }]}>
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
            <Text style={[styles.nudgeMessage, { color: PAPER }]}>{activeNudge?.message}</Text>
            {activeNudge?.sub_message ? (
              <Text style={[styles.nudgeSubMessage, { color: PAPER }]}>{activeNudge.sub_message}</Text>
            ) : null}
            <TouchableOpacity style={[styles.nudgeDismiss, { borderColor: PAPER }]} onPress={acknowledgeNudge}>
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
  connRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, marginBottom: 4 },
  connLabel: { fontSize: 11, letterSpacing: 3, fontWeight: '700' },
  connDot: { width: 6, height: 6, borderRadius: 3 },
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
