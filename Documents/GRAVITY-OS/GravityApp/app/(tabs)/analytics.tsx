/**
 * Analytics tab — habit heatmaps, streak, health snapshot, and AI-generated patterns.
 *
 * Endpoints:
 *   GET /habits/heatmap         → HeatmapHabit[]
 *   GET /analytics/summary      → AnalyticsSummary  (404 = graceful empty state)
 *   GET /analytics/patterns     → { patterns: string[] }  (404 = graceful empty state)
 *   GET /integrations/health/today → HealthSnapshot | null
 */
import {
  View,
  Text,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';
const DOT_FILLED = INK;
const DOT_EMPTY = 'rgba(20,19,13,0.10)';
const DOT_SIZE = 10;
const DOT_GAP = 3;
const WEEKS = 7; // 7 weeks × 7 days = 49 squares per habit

// ---------- types ----------

interface HeatmapDay {
  date: string;      // ISO date "2025-06-15"
  completed: boolean;
}

interface HeatmapHabit {
  habit_id: number;
  habit_name: string;
  days: HeatmapDay[];
}

interface AnalyticsSummary {
  streak: number;
  longest_streak: number;
  completion_rate: number;   // 0–1
  total_completions: number;
}

interface HealthSnapshot {
  date: string;
  steps: number;
  sleep_hours: number;
  sleep_quality: string;
  workout_minutes: number;
  heart_rate_avg: number;
  calories_active: number;
}

interface PatternsResponse {
  patterns: string[];
}

// ---------- helpers ----------

function useFetch<T>(queryKey: string[], path: string, graceful404 = false) {
  const token = useAuthStore(s => s.token);
  return useQuery<T | null>({
    queryKey,
    queryFn: async () => {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (graceful404 && res.status === 404) return null;
      if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
      return res.json() as Promise<T>;
    },
    enabled: !!token,
    retry: (count, err) => {
      // Don't retry 404s
      if (err instanceof Error && err.message.includes('404')) return false;
      return count < 2;
    },
  });
}

/** Pad or trim a habit's days array to exactly WEEKS×7 entries, most-recent-last. */
function normaliseDays(days: HeatmapDay[]): boolean[] {
  const total = WEEKS * 7;
  // Sort ascending
  const sorted = [...days].sort((a, b) => a.date.localeCompare(b.date));
  const filled = sorted.map(d => d.completed);
  if (filled.length >= total) return filled.slice(-total);
  // Pad front with false
  return [...Array(total - filled.length).fill(false), ...filled];
}

function truncate(s: string, max: number): string {
  return s.length <= max ? s : s.slice(0, max - 1) + '…';
}

// ---------- sub-components ----------

function HeatmapRow({ habit }: { habit: HeatmapHabit }) {
  const cells = normaliseDays(habit.days);

  return (
    <View style={styles.heatmapRow}>
      <Text style={styles.heatmapLabel} numberOfLines={1}>
        {truncate(habit.habit_name, 16)}
      </Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.heatmapDots}
      >
        {Array.from({ length: WEEKS }).map((_, w) => (
          <View key={w} style={styles.heatmapWeekCol}>
            {cells.slice(w * 7, w * 7 + 7).map((done, d) => (
              <View
                key={d}
                style={[
                  styles.dot,
                  { backgroundColor: done ? DOT_FILLED : DOT_EMPTY },
                ]}
              />
            ))}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statRow}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
  );
}

function SectionTitle({ children }: { children: string }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

function EmptyState({ message }: { message: string }) {
  return (
    <Text style={styles.emptyText}>{message}</Text>
  );
}

// ---------- main screen ----------

export default function AnalyticsScreen() {
  const token = useAuthStore(s => s.token);

  const {
    data: heatmapData,
    isLoading: heatmapLoading,
    error: heatmapError,
  } = useFetch<HeatmapHabit[]>(['habits_heatmap'], '/habits/heatmap');

  const {
    data: summary,
    isLoading: summaryLoading,
  } = useFetch<AnalyticsSummary>(['analytics_summary'], '/analytics/summary', true);

  const {
    data: patternsResp,
    isLoading: patternsLoading,
  } = useFetch<PatternsResponse>(['analytics_patterns'], '/analytics/patterns', true);

  const {
    data: healthToday,
    isLoading: healthLoading,
  } = useFetch<HealthSnapshot>(['health_today'], '/integrations/health/today', true);

  const isLoading = heatmapLoading || summaryLoading || patternsLoading || healthLoading;

  if (!token) return null;

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator color={INK} />
      </View>
    );
  }

  const habits = heatmapData ?? [];
  const patterns = patternsResp?.patterns ?? [];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Header ── */}
      <View style={styles.header}>
        <Text style={styles.title}>ANALYTICS</Text>
        {summary != null && (
          <View style={styles.streakBadge}>
            <Text style={styles.streakNumber}>{summary.streak}</Text>
            <Text style={styles.streakUnit}>DAY STREAK</Text>
          </View>
        )}
      </View>

      {/* ── Summary stats ── */}
      {summary != null && (
        <View style={styles.section}>
          <SectionTitle>OVERVIEW</SectionTitle>
          <StatRow label="Current streak" value={`${summary.streak} days`} />
          <StatRow label="Longest streak" value={`${summary.longest_streak} days`} />
          <StatRow
            label="Completion rate"
            value={`${Math.round(summary.completion_rate * 100)}%`}
          />
          <StatRow label="Total completions" value={String(summary.total_completions)} />
        </View>
      )}

      {/* ── Heatmaps ── */}
      <View style={styles.section}>
        <SectionTitle>HABIT HEATMAP</SectionTitle>
        {heatmapError ? (
          <EmptyState message="Could not load heatmap data." />
        ) : habits.length === 0 ? (
          <EmptyState message="No habits tracked yet. Add habits to see your consistency here." />
        ) : (
          habits.map(habit => (
            <HeatmapRow key={habit.habit_id} habit={habit} />
          ))
        )}
      </View>

      {/* ── Health snapshot ── */}
      {healthToday != null && (
        <View style={styles.section}>
          <SectionTitle>TODAY'S HEALTH</SectionTitle>
          {healthToday.steps > 0 && (
            <StatRow label="Steps" value={healthToday.steps.toLocaleString()} />
          )}
          {healthToday.sleep_hours > 0 && (
            <StatRow
              label="Sleep"
              value={`${healthToday.sleep_hours}h (${healthToday.sleep_quality})`}
            />
          )}
          {healthToday.calories_active > 0 && (
            <StatRow
              label="Active calories"
              value={`${healthToday.calories_active} kcal`}
            />
          )}
          {healthToday.heart_rate_avg > 0 && (
            <StatRow
              label="Avg heart rate"
              value={`${healthToday.heart_rate_avg} bpm`}
            />
          )}
        </View>
      )}

      {/* ── Patterns ── */}
      {patterns.length > 0 && (
        <View style={styles.section}>
          <SectionTitle>PATTERNS</SectionTitle>
          {patterns.map((p, i) => (
            <View key={i} style={styles.patternRow}>
              <View style={styles.patternBorder} />
              <Text style={styles.patternText}>"{p}"</Text>
            </View>
          ))}
        </View>
      )}

      {/* Spacer for tab bar */}
      <View style={{ height: 20 }} />
    </ScrollView>
  );
}

// ---------- styles ----------

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: PAPER,
    justifyContent: 'center',
    alignItems: 'center',
  },
  container: {
    flex: 1,
    backgroundColor: PAPER,
  },
  content: {
    paddingBottom: 60,
  },

  // Header
  header: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 20,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: 12,
    letterSpacing: 3,
    fontWeight: '700',
    color: INK,
  },
  streakBadge: {
    alignItems: 'flex-end',
  },
  streakNumber: {
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: -0.5,
    color: INK,
  },
  streakUnit: {
    fontSize: 9,
    letterSpacing: 1.5,
    color: INK,
    opacity: 0.5,
    marginTop: 1,
  },

  // Section
  section: {
    marginHorizontal: 20,
    marginBottom: 24,
    borderTopWidth: 1,
    borderTopColor: `rgba(20,19,13,0.12)`,
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 10,
    letterSpacing: 2,
    fontWeight: '600',
    color: INK,
    marginBottom: 14,
  },

  // Stat rows
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(20,19,13,0.06)',
  },
  statLabel: {
    fontSize: 13,
    color: INK,
    opacity: 0.6,
  },
  statValue: {
    fontSize: 13,
    fontWeight: '600',
    color: INK,
  },

  // Heatmap
  heatmapRow: {
    marginBottom: 14,
  },
  heatmapLabel: {
    fontSize: 11,
    color: INK,
    opacity: 0.7,
    letterSpacing: 0.5,
    marginBottom: 5,
    fontWeight: '500',
  },
  heatmapDots: {
    flexDirection: 'row',
    gap: DOT_GAP,
  },
  heatmapWeekCol: {
    flexDirection: 'column',
    gap: DOT_GAP,
  },
  dot: {
    width: DOT_SIZE,
    height: DOT_SIZE,
  },

  // Patterns
  patternRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  patternBorder: {
    width: 2,
    backgroundColor: INK,
    opacity: 0.25,
    marginRight: 12,
    borderRadius: 1,
  },
  patternText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 21,
    color: INK,
    opacity: 0.75,
    fontStyle: 'italic',
  },

  // Empty state
  emptyText: {
    fontSize: 13,
    lineHeight: 21,
    color: INK,
    opacity: 0.45,
  },
});
