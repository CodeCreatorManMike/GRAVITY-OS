import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';
import { RingProgress } from '../../components/RingProgress';
import { BG, SURFACE, SURFACE2, WHITE, DIM, FAINT, BORDER, T, S } from '../../constants/theme';

interface Goal {
  id: number;
  statement: string;
  likelihood_score: number;
  days_remaining: number;
  target_date: string;
  status: string;
}

interface GoalHistory {
  id: number;
  statement: string;
  status: string;
  likelihood_score: number;
  completed_at: string | null;
  target_date: string;
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })} ${d.getFullYear()}`;
}

export default function GoalsScreen() {
  const token  = useAuthStore(s => s.token);
  const router = useRouter();

  const { data: goal, isLoading: goalLoading, refetch: refetchGoal } = useQuery<Goal>({
    queryKey: ['goal'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/goals`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
  });

  const { data: history, isLoading: histLoading, refetch: refetchHist } = useQuery<GoalHistory[]>({
    queryKey: ['goals_history'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/goals/history`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
  });

  const pct = goal ? goal.likelihood_score : 0;
  const pctInt = Math.round(pct * 100);

  return (
    <ScrollView
      style={s.container}
      contentContainerStyle={s.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={goalLoading || histLoading}
          onRefresh={() => { refetchGoal(); refetchHist(); }}
          tintColor={DIM}
        />
      }
    >
      {/* Header */}
      <View style={s.header}>
        <Text style={s.heading}>Goals</Text>
        <TouchableOpacity onPress={() => router.push('/goal-edit' as any)} style={s.editBtn}>
          <Text style={s.editBtnText}>+ NEW</Text>
        </TouchableOpacity>
      </View>

      {/* Active goal hero */}
      {goal ? (
        <View style={s.heroCard}>
          <Text style={s.heroLabel}>ACTIVE</Text>
          <Text style={s.heroStatement}>{goal.statement}</Text>

          {/* Ring + stats row */}
          <View style={s.statsRow}>
            <View style={s.ringWrap}>
              <RingProgress pct={pct} size={110} stroke={7} />
              <View style={s.ringCenter}>
                <Text style={s.ringPct}>{pctInt}</Text>
                <Text style={s.ringUnit}>%</Text>
              </View>
            </View>
            <View style={s.statsRight}>
              <View style={s.statItem}>
                <Text style={s.statValue}>{goal.days_remaining}</Text>
                <Text style={s.statLabel}>DAYS LEFT</Text>
              </View>
              <View style={s.statDivider} />
              <View style={s.statItem}>
                <Text style={s.statValue}>{fmtDate(goal.target_date)}</Text>
                <Text style={s.statLabel}>TARGET</Text>
              </View>
            </View>
          </View>

          {/* Likelihood bar */}
          <View style={s.barTrack}>
            <View style={[s.barFill, { width: `${pctInt}%` }]} />
          </View>
          <Text style={s.barLabel}>
            {pctInt >= 70 ? 'On track' : pctInt >= 40 ? 'Needs attention' : 'At risk'}
          </Text>
        </View>
      ) : !goalLoading && (
        <View style={s.emptyHero}>
          <Text style={s.emptyTitle}>No active goal</Text>
          <Text style={s.emptyBody}>Set a goal and Gravity will track your likelihood of achieving it.</Text>
          <TouchableOpacity style={s.addBtn} onPress={() => router.push('/goal-edit' as any)}>
            <Text style={s.addBtnText}>SET A GOAL</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* History */}
      {(history?.length ?? 0) > 0 && (
        <View style={s.historySection}>
          <Text style={s.sectionLabel}>PREVIOUS GOALS</Text>
          {(history ?? []).map(g => (
            <View key={g.id} style={s.histRow}>
              <View style={{ flex: 1 }}>
                <Text style={s.histStatement} numberOfLines={2}>{g.statement}</Text>
                <Text style={s.histMeta}>
                  {g.status.toUpperCase()} · {g.completed_at ? fmtDate(g.completed_at) : fmtDate(g.target_date)}
                </Text>
              </View>
              <View style={s.histRing}>
                <RingProgress pct={g.likelihood_score} size={36} stroke={3} color="rgba(255,255,255,0.5)" />
                <Text style={s.histPct}>{Math.round(g.likelihood_score * 100)}</Text>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container:       { flex: 1, backgroundColor: BG },
  content:         { paddingBottom: 48 },
  header:          {
    flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between',
    paddingTop: 64, paddingHorizontal: 24, paddingBottom: 20,
  },
  heading:         { ...T.heading },
  editBtn:         {
    borderWidth: 1, borderColor: FAINT,
    borderRadius: 8, paddingHorizontal: 14, paddingVertical: 8,
  },
  editBtnText:     { color: WHITE, fontSize: 11, letterSpacing: 1.5, fontWeight: '600' },

  heroCard:        {
    backgroundColor: SURFACE, borderRadius: 20,
    marginHorizontal: 20, padding: 24, marginBottom: 24,
  },
  heroLabel:       { fontSize: 10, letterSpacing: 2, color: DIM, fontWeight: '700', marginBottom: 10 },
  heroStatement:   { ...T.title, fontSize: 18, lineHeight: 26, marginBottom: 24 },

  statsRow:        { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  ringWrap:        { position: 'relative', width: 110, height: 110, alignItems: 'center', justifyContent: 'center' },
  ringCenter:      { position: 'absolute', alignItems: 'center' },
  ringPct:         { fontFamily: 'JetBrainsMono_700Bold', fontSize: 28, color: WHITE, lineHeight: 32 },
  ringUnit:        { fontSize: 12, color: DIM, marginTop: -2 },
  statsRight:      { flex: 1, paddingLeft: 24, gap: 16 },
  statItem:        {},
  statValue:       { fontFamily: 'JetBrainsMono_400Regular', fontSize: 14, color: WHITE, marginBottom: 2 },
  statLabel:       { fontSize: 9, letterSpacing: 2, color: DIM, fontWeight: '600' },
  statDivider:     { height: 1, backgroundColor: BORDER },

  barTrack:        { height: 3, backgroundColor: FAINT, borderRadius: 2, marginBottom: 8 },
  barFill:         { height: 3, backgroundColor: WHITE, borderRadius: 2 },
  barLabel:        { fontSize: 11, color: DIM },

  emptyHero:       {
    margin: 20, padding: 32, backgroundColor: SURFACE, borderRadius: 20, alignItems: 'center',
  },
  emptyTitle:      { ...T.title, marginBottom: 10 },
  emptyBody:       { ...T.body, color: DIM, textAlign: 'center', lineHeight: 22, marginBottom: 24 },
  addBtn:          {
    borderWidth: 1, borderColor: FAINT,
    borderRadius: 10, paddingHorizontal: 24, paddingVertical: 12,
  },
  addBtnText:      { color: WHITE, fontSize: 11, letterSpacing: 2, fontWeight: '600' },

  historySection:  { paddingHorizontal: 20 },
  sectionLabel:    { fontSize: 10, letterSpacing: 2, color: DIM, fontWeight: '700', marginBottom: 14 },
  histRow:         {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: BORDER,
  },
  histStatement:   { ...T.body, fontSize: 14, marginBottom: 4 },
  histMeta:        { fontSize: 11, color: DIM, letterSpacing: 0.5 },
  histRing:        { alignItems: 'center', justifyContent: 'center', marginLeft: 12 },
  histPct:         {
    position: 'absolute',
    fontFamily: 'JetBrainsMono_400Regular',
    fontSize: 9, color: DIM,
  },
});
