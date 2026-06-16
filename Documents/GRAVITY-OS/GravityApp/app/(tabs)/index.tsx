import { useState, useRef, useCallback, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Modal, FlatList, RefreshControl,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';
import { useGravitySocket } from '../../hooks/useGravitySocket';
import DevicePreview, { FaceCard } from '../../components/DevicePreview';
import { RingProgress } from '../../components/RingProgress';
import {
  BG, SURFACE, SURFACE2, WHITE, DIM, FAINT, BORDER,
  DEVICE_INK, DEVICE_PAPER, T, S,
} from '../../constants/theme';

const SCREEN_W      = Dimensions.get('window').width;
const FACE_SIZE     = Math.min(SCREEN_W * 0.55, 220);
const FACES_CACHE   = 'gravity_faces_v1';

interface Habit  { id: number; name: string; is_non_negotiable: boolean; completed_today: boolean; }
interface Goal   { id: number; statement: string; likelihood_score: number; days_remaining: number; }
interface Nudge  { id: number; message: string; sub_message: string | null; action_label: string; category: string; }
interface DeviceState { generated_at: string; faces: FaceCard[]; }

function greeting(name: string | null) {
  const h = new Date().getHours();
  const time = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  return `Good ${time}${name ? `, ${name.split(' ')[0]}` : ''}`;
}

// ── Face carousel ─────────────────────────────────────────────────────────────

function FaceCarousel({ faces, offline }: { faces: FaceCard[]; offline: boolean }) {
  const [idx, setIdx] = useState(0);

  const onScroll = useCallback((e: any) => {
    setIdx(Math.round(e.nativeEvent.contentOffset.x / SCREEN_W));
  }, []);

  const content = faces.length === 0
    ? [null]
    : faces;

  return (
    <View style={cs.wrapper}>
      <ScrollView
        horizontal pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onScroll}
        decelerationRate="fast"
        style={{ width: SCREEN_W }}
      >
        {content.map((face, i) => (
          <View key={i} style={[cs.page, { width: SCREEN_W }]}>
            {/* Device card — warm bezel inside dark card */}
            <View style={cs.card}>
              <DevicePreview face={face as FaceCard | null} size={FACE_SIZE} offline={offline} />
            </View>
          </View>
        ))}
      </ScrollView>
      {content.length > 1 && (
        <View style={cs.dots}>
          {content.map((_, i) => (
            <View key={i} style={[cs.dot, { backgroundColor: i === idx ? WHITE : FAINT }]} />
          ))}
        </View>
      )}
    </View>
  );
}

const cs = StyleSheet.create({
  wrapper: { alignItems: 'center', paddingVertical: 4 },
  page:    { alignItems: 'center', justifyContent: 'center', paddingVertical: 8 },
  card:    {
    backgroundColor: SURFACE,
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 10,
  },
  dots:    { flexDirection: 'row', gap: 6, marginTop: 16 },
  dot:     { width: 5, height: 5, borderRadius: 2.5 },
});

// ── Home screen ───────────────────────────────────────────────────────────────

export default function HomeScreen() {
  const router       = useRouter();
  const token        = useAuthStore(s => s.token);
  const name         = useAuthStore(s => s.name);
  const queryClient  = useQueryClient();
  const [activeNudge, setActiveNudge] = useState<Nudge | null>(null);
  const [cachedFaces, setCachedFaces] = useState<FaceCard[]>([]);

  const { isConnected } = useGravitySocket({
    onNudge: (data) => setActiveNudge(data),
    onCycleReviewReady: () => router.push('/review' as any),
  });

  useEffect(() => {
    AsyncStorage.getItem(FACES_CACHE).then(raw => {
      if (raw) try { setCachedFaces(JSON.parse(raw)); } catch {}
    });
  }, []);

  if (!token) { router.replace('/login'); return null; }

  const { data: goal, isLoading: goalLoading } = useQuery<Goal>({
    queryKey: ['goal'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/goals`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
  });

  const { data: habits, isLoading: habitsLoading, refetch } = useQuery<Habit[]>({
    queryKey: ['habits'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/habits`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
  });

  const { data: deviceState, isError: deviceError } = useQuery<DeviceState>({
    queryKey: ['device_state'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/device/state`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      const d = await r.json();
      await AsyncStorage.setItem(FACES_CACHE, JSON.stringify(d.faces));
      return d;
    },
    enabled: !!token,
    staleTime: 5 * 60_000,
    retry: 1,
  });

  const completeMutation = useMutation({
    mutationFn: async (id: number) => {
      const r = await fetch(`${API_BASE}/habits/${id}/complete`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error();
      return r.json();
    },
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['habits'] });
      const prev = queryClient.getQueryData<Habit[]>(['habits']);
      queryClient.setQueryData<Habit[]>(['habits'], old =>
        old?.map(h => h.id === id ? { ...h, completed_today: true } : h) ?? []
      );
      return { prev };
    },
    onError: (_e, _id, ctx) => queryClient.setQueryData(['habits'], ctx?.prev),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['habits'] }),
  });

  const acknowledgeNudge = async () => {
    if (!activeNudge) return;
    try {
      await fetch(`${API_BASE}/nudges/${activeNudge.id}/acknowledge`, {
        method: 'PUT', headers: { Authorization: `Bearer ${token}` },
      });
    } catch {}
    setActiveNudge(null);
  };

  const faces     = deviceState?.faces ?? cachedFaces;
  const offline   = !!deviceError && cachedFaces.length > 0;
  const nonNeg    = habits?.filter(h => h.is_non_negotiable) ?? [];
  const doneCount = nonNeg.filter(h => h.completed_today).length;
  const pct       = goal ? goal.likelihood_score : 0;

  return (
    <View style={s.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={habitsLoading || goalLoading}
            onRefresh={refetch}
            tintColor={DIM}
          />
        }
      >
        {/* Header */}
        <View style={s.header}>
          <Text style={s.greeting}>{greeting(name)}</Text>
          <View style={[s.connDot, { backgroundColor: isConnected ? WHITE : FAINT }]} />
        </View>

        {/* Device carousel */}
        <FaceCarousel faces={faces} offline={offline} />

        {/* Goal summary card */}
        {goal && (
          <View style={s.goalCard}>
            <View style={s.goalLeft}>
              <Text style={s.sectionLabel}>ACTIVE GOAL</Text>
              <Text style={s.goalStatement} numberOfLines={2}>{goal.statement}</Text>
              <Text style={s.goalDays}>
                {goal.days_remaining > 0 ? `${goal.days_remaining} days remaining` : 'Deadline today'}
              </Text>
            </View>
            <View style={s.goalRing}>
              <RingProgress pct={pct} size={64} stroke={5} />
              <Text style={s.goalPct}>{Math.round(pct * 100)}%</Text>
            </View>
          </View>
        )}

        {/* Non-negotiables */}
        <View style={s.section}>
          <View style={s.sectionHeader}>
            <Text style={s.sectionLabel}>NON-NEGOTIABLES</Text>
            <Text style={s.sectionCount}>{doneCount}/{nonNeg.length}</Text>
          </View>
          {nonNeg.map(h => (
            <TouchableOpacity
              key={h.id}
              style={s.habitRow}
              onPress={() => !h.completed_today && completeMutation.mutate(h.id)}
              activeOpacity={h.completed_today ? 1 : 0.6}
            >
              <View style={[s.checkbox, h.completed_today && s.checkboxDone]}>
                {h.completed_today && <Text style={s.checkmark}>✓</Text>}
              </View>
              <Text style={[s.habitName, h.completed_today && s.habitDone]}>
                {h.name}
              </Text>
            </TouchableOpacity>
          ))}
          {nonNeg.length === 0 && (
            <Text style={s.emptyText}>No non-negotiables set. Add habits to get started.</Text>
          )}
        </View>

        <View style={{ height: 32 }} />
      </ScrollView>

      {/* Nudge modal */}
      <Modal visible={!!activeNudge} transparent animationType="fade">
        <TouchableOpacity style={s.nudgeOverlay} activeOpacity={1} onPress={acknowledgeNudge}>
          <View style={s.nudgeCard}>
            <Text style={s.nudgeCategory}>{activeNudge?.category?.toUpperCase() ?? 'GRAVITY'}</Text>
            <Text style={s.nudgeMessage}>{activeNudge?.message}</Text>
            {activeNudge?.sub_message
              ? <Text style={s.nudgeSub}>{activeNudge.sub_message}</Text>
              : null}
            <TouchableOpacity style={s.nudgeDismiss} onPress={acknowledgeNudge}>
              <Text style={s.nudgeDismissText}>
                {activeNudge?.action_label?.toUpperCase() ?? 'DISMISS'}
              </Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: BG },
  header: {
    flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between',
    paddingTop: 64, paddingHorizontal: 24, paddingBottom: 4,
  },
  greeting:   { ...T.heading, fontSize: 28, flex: 1, marginRight: 12 },
  connDot:    { width: 8, height: 8, borderRadius: 4, marginBottom: 6 },

  goalCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: SURFACE, borderRadius: 16,
    marginHorizontal: 20, marginTop: 16, padding: 20,
  },
  goalLeft:       { flex: 1, marginRight: 16 },
  goalStatement:  { ...T.body, fontSize: 16, fontWeight: '600', marginTop: 6, marginBottom: 6, lineHeight: 22 },
  goalDays:       { ...T.caption },
  goalRing:       { alignItems: 'center', justifyContent: 'center' },
  goalPct:        {
    position: 'absolute',
    fontFamily: 'JetBrainsMono_700Bold',
    fontSize: 13, color: WHITE,
  },

  section:        { marginHorizontal: 20, marginTop: 24 },
  sectionHeader:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionLabel:   { fontSize: 10, letterSpacing: 2, fontWeight: '700', color: DIM },
  sectionCount:   { fontFamily: 'JetBrainsMono_400Regular', fontSize: 12, color: DIM },

  habitRow:       {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: BORDER,
  },
  checkbox:       {
    width: 22, height: 22,
    borderWidth: 1.5, borderColor: FAINT, borderRadius: 6,
    marginRight: 14, justifyContent: 'center', alignItems: 'center',
  },
  checkboxDone:   { backgroundColor: WHITE, borderColor: WHITE },
  checkmark:      { color: BG, fontSize: 12, fontWeight: '700' },
  habitName:      { ...T.body, flex: 1 },
  habitDone:      { color: DIM, textDecorationLine: 'line-through' },
  emptyText:      { ...T.caption, lineHeight: 20 },

  nudgeOverlay:   { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end', padding: 16 },
  nudgeCard:      { backgroundColor: SURFACE2, borderRadius: 20, padding: 28, marginBottom: 8 },
  nudgeCategory:  { fontSize: 10, letterSpacing: 3, color: DIM, marginBottom: 14 },
  nudgeMessage:   { ...T.title, lineHeight: 30, marginBottom: 10 },
  nudgeSub:       { ...T.body, color: DIM, lineHeight: 22, marginBottom: 20 },
  nudgeDismiss:   {
    borderWidth: 1, borderColor: FAINT,
    paddingVertical: 14, alignItems: 'center', borderRadius: 10, marginTop: 4,
  },
  nudgeDismissText: { color: WHITE, fontWeight: '600', letterSpacing: 2, fontSize: 12 },
});
