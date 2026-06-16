import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';
import { BG, SURFACE, WHITE, DIM, FAINT, BORDER, T } from '../../constants/theme';

interface Habit {
  id: number;
  name: string;
  is_non_negotiable: boolean;
  completed_today: boolean;
  category: string | null;
}

function todayDate() {
  const d = new Date();
  return `${d.toLocaleString('default', { weekday: 'long' })}, ${d.toLocaleString('default', { month: 'long' })} ${d.getDate()}`;
}

export default function TodayScreen() {
  const token        = useAuthStore(s => s.token);
  const queryClient  = useQueryClient();

  const { data: habits, isLoading, refetch } = useQuery<Habit[]>({
    queryKey: ['habits'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/habits`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
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

  const all          = habits ?? [];
  const morning      = all.filter(h => h.is_non_negotiable);
  const afternoon    = all.filter(h => !h.is_non_negotiable);
  const totalDone    = all.filter(h => h.completed_today).length;
  const totalCount   = all.length;
  const completionPct = totalCount > 0 ? Math.round((totalDone / totalCount) * 100) : 0;

  return (
    <ScrollView
      style={s.container}
      contentContainerStyle={s.content}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={DIM} />}
    >
      {/* Header */}
      <View style={s.header}>
        <Text style={s.heading}>Today</Text>
        <Text style={s.date}>{todayDate()}</Text>
      </View>

      {/* Progress summary */}
      <View style={s.summaryCard}>
        <View style={s.summaryLeft}>
          <Text style={s.summaryPct}>{completionPct}%</Text>
          <Text style={s.summaryLabel}>COMPLETE</Text>
        </View>
        <View style={s.summaryBar}>
          <View style={s.barTrack}>
            <View style={[s.barFill, { width: `${completionPct}%` }]} />
          </View>
          <Text style={s.barMeta}>{totalDone} of {totalCount} done</Text>
        </View>
      </View>

      {/* Morning — non-negotiables */}
      {morning.length > 0 && (
        <Section
          title="MORNING"
          habits={morning}
          onComplete={(id) => completeMutation.mutate(id)}
        />
      )}

      {/* Afternoon — other habits */}
      {afternoon.length > 0 && (
        <Section
          title="AFTERNOON"
          habits={afternoon}
          onComplete={(id) => completeMutation.mutate(id)}
        />
      )}

      {all.length === 0 && !isLoading && (
        <View style={s.empty}>
          <Text style={s.emptyTitle}>Nothing scheduled</Text>
          <Text style={s.emptyBody}>Add habits from the settings to start building your day.</Text>
        </View>
      )}
    </ScrollView>
  );
}

function Section({
  title, habits, onComplete,
}: { title: string; habits: Habit[]; onComplete: (id: number) => void }) {
  const done = habits.filter(h => h.completed_today).length;
  return (
    <View style={s.section}>
      <View style={s.sectionHeader}>
        <Text style={s.sectionTitle}>{title}</Text>
        <Text style={s.sectionCount}>{done}/{habits.length}</Text>
      </View>
      {habits.map(h => (
        <TouchableOpacity
          key={h.id}
          style={s.row}
          onPress={() => !h.completed_today && onComplete(h.id)}
          activeOpacity={h.completed_today ? 1 : 0.65}
        >
          <View style={[s.checkbox, h.completed_today && s.checkboxDone]}>
            {h.completed_today && <Text style={s.checkmark}>✓</Text>}
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[s.habitName, h.completed_today && s.habitDone]}>
              {h.name}
            </Text>
            {h.category && (
              <Text style={s.habitTag}>{h.category.toUpperCase()}</Text>
            )}
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  container:     { flex: 1, backgroundColor: BG },
  content:       { paddingBottom: 48 },
  header:        { paddingTop: 64, paddingHorizontal: 24, paddingBottom: 20 },
  heading:       { ...T.heading, marginBottom: 4 },
  date:          { fontSize: 13, color: DIM },

  summaryCard:   {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#141414', borderRadius: 16,
    marginHorizontal: 20, padding: 20, marginBottom: 28, gap: 20,
  },
  summaryLeft:   { alignItems: 'center', minWidth: 60 },
  summaryPct:    { fontFamily: 'JetBrainsMono_700Bold', fontSize: 32, color: WHITE, lineHeight: 36 },
  summaryLabel:  { fontSize: 9, letterSpacing: 2, color: DIM, fontWeight: '600', marginTop: 2 },
  summaryBar:    { flex: 1 },
  barTrack:      { height: 4, backgroundColor: FAINT, borderRadius: 2, marginBottom: 8 },
  barFill:       { height: 4, backgroundColor: WHITE, borderRadius: 2 },
  barMeta:       { fontSize: 12, color: DIM },

  section:       { marginHorizontal: 20, marginBottom: 28 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionTitle:  { fontSize: 10, letterSpacing: 2, color: DIM, fontWeight: '700' },
  sectionCount:  { fontFamily: 'JetBrainsMono_400Regular', fontSize: 12, color: DIM },

  row:           {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: BORDER,
  },
  checkbox:      {
    width: 24, height: 24, borderWidth: 1.5,
    borderColor: FAINT, borderRadius: 7,
    marginRight: 14, justifyContent: 'center', alignItems: 'center',
  },
  checkboxDone:  { backgroundColor: WHITE, borderColor: WHITE },
  checkmark:     { color: BG, fontSize: 13, fontWeight: '700' },
  habitName:     { ...T.body, fontSize: 16 },
  habitDone:     { color: DIM, textDecorationLine: 'line-through' },
  habitTag:      { fontSize: 10, letterSpacing: 1.5, color: FAINT, marginTop: 3, fontWeight: '600' },

  empty:         { paddingHorizontal: 24, paddingTop: 48, alignItems: 'center' },
  emptyTitle:    { ...T.title, marginBottom: 10 },
  emptyBody:     { ...T.body, color: DIM, textAlign: 'center', lineHeight: 22 },
});
