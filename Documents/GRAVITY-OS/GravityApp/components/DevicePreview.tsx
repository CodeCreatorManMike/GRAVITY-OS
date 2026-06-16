/**
 * DevicePreview — circular preview of a single GRAVITY face card.
 *
 * Renders the 5 face types from backend/schemas/face.py:
 *   goal_arc | task_list | habit_heatmap | timer | study_progress
 *
 * Pure React Native: View + Text + Animated only. No SVG, no canvas.
 * INK/PAPER palette matches physical display.
 */
import { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';

const INK = '#14130d';
const PAPER = '#f4f2ea';

// ── Face schema types (mirror backend/schemas/face.py) ──────────────────────

export interface GoalArcFace {
  type: 'goal_arc';
  label: string;
  pct: number;
  days_left: number;
  on_track: boolean;
  sub_label?: string;
}

export interface TaskItem {
  title: string;
  done: boolean;
  active: boolean;
}

export interface TaskListFace {
  type: 'task_list';
  tasks: TaskItem[];
  done_count: number;
  total_count: number;
  next_label?: string;
}

export interface HabitRow {
  name: string;
  days: boolean[];
}

export interface HabitHeatmapFace {
  type: 'habit_heatmap';
  habits: HabitRow[];
  streak: number;
  week_label?: string;
}

export interface TimerFace {
  type: 'timer';
  label?: string;
  duration_seconds: number;
  remaining_seconds: number;
  running: boolean;
}

export interface StudyProgressFace {
  type: 'study_progress';
  subject: string;
  pct: number;
  current_lesson: number;
  total_lessons: number;
  target_grade?: string;
  streak_days?: number;
}

export type FaceCard =
  | GoalArcFace
  | TaskListFace
  | HabitHeatmapFace
  | TimerFace
  | StudyProgressFace;

// ── Props ─────────────────────────────────────────────────────────────────────

interface DevicePreviewProps {
  face: FaceCard | null;
  size?: number;
  offline?: boolean;
}

// ── Scale helper ──────────────────────────────────────────────────────────────

function sc(size: number) {
  const b = size / 280;
  return {
    xl: Math.round(52 * b),
    lg: Math.round(38 * b),
    md: Math.round(16 * b),
    sm: Math.round(12 * b),
    xs: Math.round(10 * b),
    micro: Math.round(8 * b),
  };
}

// ── Arc progress (two half-ring clip trick, no SVG) ───────────────────────────

function ProgressArc({ pct, size, border }: { pct: number; size: number; border: number }) {
  const degrees = Math.max(0, Math.min(1, pct)) * 360;
  const half = size / 2;
  const rightDeg = Math.min(degrees, 180);
  const leftDeg = Math.max(0, degrees - 180);

  return (
    <View style={{ position: 'absolute', width: size, height: size }}>
      <View style={{ position: 'absolute', width: size, height: size, overflow: 'hidden' }}>
        <View style={{ position: 'absolute', right: 0, width: half, height: size, overflow: 'hidden' }}>
          <View style={{
            position: 'absolute', left: -half, width: size, height: size,
            borderRadius: size / 2, borderWidth: border, borderColor: INK,
            transform: [{ rotate: `${rightDeg - 180}deg` }],
          }} />
        </View>
      </View>
      {leftDeg > 0 && (
        <View style={{ position: 'absolute', width: size, height: size, overflow: 'hidden' }}>
          <View style={{ position: 'absolute', left: 0, width: half, height: size, overflow: 'hidden' }}>
            <View style={{
              position: 'absolute', left: 0, width: size, height: size,
              borderRadius: size / 2, borderWidth: border, borderColor: INK,
              transform: [{ rotate: `${leftDeg}deg` }],
            }} />
          </View>
        </View>
      )}
    </View>
  );
}

// ── Face renderers ────────────────────────────────────────────────────────────

function GoalArcRenderer({ face, s, size }: { face: GoalArcFace; s: ReturnType<typeof sc>; size: number }) {
  const ringSize = size * 0.86;
  const border = size * 0.055;
  const pct = Math.max(0, Math.min(100, face.pct));

  return (
    <>
      <View style={{ position: 'absolute', width: ringSize, height: ringSize, borderRadius: ringSize / 2, borderWidth: border, borderColor: 'rgba(20,19,13,0.1)' }} />
      <ProgressArc pct={pct / 100} size={ringSize} border={border} />
      <Text style={[styles.topLabel, { fontSize: s.xs, color: INK }]} numberOfLines={1}>{face.label.toUpperCase()}</Text>
      <Text style={[styles.bigNum, { fontSize: s.xl, color: INK }]}>{Math.round(pct)}%</Text>
      <Text style={[styles.subLabel, { fontSize: s.micro, color: INK }]}>{face.days_left}D LEFT</Text>
      {face.sub_label ? (
        <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]} numberOfLines={1}>{face.sub_label}</Text>
      ) : (
        <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]}>{face.on_track ? 'ON TRACK' : 'AT RISK'}</Text>
      )}
    </>
  );
}

function TaskListRenderer({ face, s }: { face: TaskListFace; s: ReturnType<typeof sc> }) {
  return (
    <>
      <Text style={[styles.topLabel, { fontSize: s.xs, color: INK }]}>
        {face.done_count}/{face.total_count} DONE
      </Text>
      <View style={styles.taskList}>
        {face.tasks.slice(0, 5).map((t, i) => (
          <View key={i} style={styles.taskRow}>
            <Text style={{ fontSize: s.sm, color: INK, marginRight: 5 }}>{t.done ? '✓' : t.active ? '▶' : '○'}</Text>
            <Text
              style={{ fontSize: s.sm, color: INK, flex: 1, opacity: t.done ? 0.35 : 1 }}
              numberOfLines={1}
            >
              {t.title}
            </Text>
          </View>
        ))}
      </View>
      {face.next_label ? (
        <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]} numberOfLines={1}>{face.next_label}</Text>
      ) : null}
    </>
  );
}

function HabitHeatmapRenderer({ face, s, size }: { face: HabitHeatmapFace; s: ReturnType<typeof sc>; size: number }) {
  const dotSize = Math.floor(size * 0.065);
  const gap = Math.floor(size * 0.02);

  return (
    <>
      <Text style={[styles.topLabel, { fontSize: s.xs, color: INK }]}>{face.week_label ?? 'THIS WEEK'}</Text>
      <View style={styles.heatmapGrid}>
        {face.habits.slice(0, 5).map((h, r) => (
          <View key={r} style={[styles.heatmapRow, { gap }]}>
            {h.days.slice(0, 7).map((filled, c) => (
              <View key={c} style={{ width: dotSize, height: dotSize, backgroundColor: filled ? INK : 'rgba(20,19,13,0.12)' }} />
            ))}
          </View>
        ))}
      </View>
      <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]}>{face.streak}D STREAK</Text>
    </>
  );
}

function TimerRenderer({ face, s, size }: { face: TimerFace; s: ReturnType<typeof sc>; size: number }) {
  const ringSize = size * 0.86;
  const border = size * 0.055;
  const pct = face.duration_seconds > 0 ? face.remaining_seconds / face.duration_seconds : 0;
  const mins = Math.floor(face.remaining_seconds / 60);
  const secs = face.remaining_seconds % 60;

  return (
    <>
      <View style={{ position: 'absolute', width: ringSize, height: ringSize, borderRadius: ringSize / 2, borderWidth: border, borderColor: 'rgba(20,19,13,0.1)' }} />
      <ProgressArc pct={pct} size={ringSize} border={border} />
      <Text style={[styles.topLabel, { fontSize: s.xs, color: INK }]}>{(face.label ?? 'FOCUS').toUpperCase()}</Text>
      <Text style={[styles.bigNum, { fontSize: s.lg, color: INK }]}>
        {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
      </Text>
      <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]}>{face.running ? 'RUNNING' : 'PAUSED'}</Text>
    </>
  );
}

function StudyProgressRenderer({ face, s, size }: { face: StudyProgressFace; s: ReturnType<typeof sc>; size: number }) {
  const ringSize = size * 0.86;
  const border = size * 0.055;
  const pct = Math.max(0, Math.min(100, face.pct));

  return (
    <>
      <View style={{ position: 'absolute', width: ringSize, height: ringSize, borderRadius: ringSize / 2, borderWidth: border, borderColor: 'rgba(20,19,13,0.1)' }} />
      <ProgressArc pct={pct / 100} size={ringSize} border={border} />
      <Text style={[styles.topLabel, { fontSize: s.xs, color: INK }]} numberOfLines={1}>{face.subject.toUpperCase()}</Text>
      <Text style={[styles.bigNum, { fontSize: s.xl, color: INK }]}>{Math.round(pct)}%</Text>
      <Text style={[styles.subLabel, { fontSize: s.micro, color: INK }]}>
        {face.current_lesson}/{face.total_lessons} LESSONS
      </Text>
      {face.target_grade ? (
        <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]}>TARGET {face.target_grade}</Text>
      ) : null}
    </>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function DevicePreview({ face, size = 280, offline = false }: DevicePreviewProps) {
  const s = sc(size);
  const inner = size - 4;

  const renderFace = () => {
    if (!face) {
      return (
        <Text style={{ fontSize: s.micro, color: INK, opacity: 0.3, letterSpacing: 1 }}>
          {offline ? 'OFFLINE' : 'NO SIGNAL'}
        </Text>
      );
    }

    switch (face.type) {
      case 'goal_arc':     return <GoalArcRenderer face={face} s={s} size={inner} />;
      case 'task_list':    return <TaskListRenderer face={face} s={s} />;
      case 'habit_heatmap': return <HabitHeatmapRenderer face={face} s={s} size={inner} />;
      case 'timer':        return <TimerRenderer face={face} s={s} size={inner} />;
      case 'study_progress': return <StudyProgressRenderer face={face} s={s} size={inner} />;
      default:             return <Text style={{ fontSize: s.micro, color: INK, opacity: 0.4 }}>{(face as any).type}</Text>;
    }
  };

  return (
    <View style={{
      width: size, height: size, borderRadius: size / 2,
      backgroundColor: PAPER,
      borderWidth: offline ? 1 : 2,
      borderColor: offline ? 'rgba(20,19,13,0.3)' : INK,
      overflow: 'hidden',
      justifyContent: 'center',
      alignItems: 'center',
      opacity: offline ? 0.6 : 1,
    }}>
      {renderFace()}
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  topLabel: {
    position: 'absolute', top: '17%',
    textAlign: 'center', fontWeight: '600', letterSpacing: 2, opacity: 0.55,
  },
  bottomLabel: {
    position: 'absolute', bottom: '15%',
    textAlign: 'center', fontWeight: '600', letterSpacing: 1.5, opacity: 0.45,
  },
  bigNum: {
    fontWeight: '700', letterSpacing: -1, textAlign: 'center',
  },
  subLabel: {
    textAlign: 'center', fontWeight: '600', letterSpacing: 2, marginTop: 4,
  },
  taskList: {
    width: '72%', marginTop: 6,
  },
  taskRow: {
    flexDirection: 'row', alignItems: 'center', marginBottom: 4,
  },
  heatmapGrid: {
    marginTop: 8, alignItems: 'center', gap: 3,
  },
  heatmapRow: {
    flexDirection: 'row', alignItems: 'center',
  },
});
