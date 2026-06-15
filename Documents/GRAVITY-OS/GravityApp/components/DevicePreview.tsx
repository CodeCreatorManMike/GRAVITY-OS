/**
 * DevicePreview — circular 280×280 (default) preview of a single GRAVITY device screen.
 *
 * Pure React Native: View + Text + Animated only. No SVG, no canvas.
 * Mirrors the e-ink aesthetic of the physical 480×480 circular display.
 */
import { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';

const INK = '#14130d';
const PAPER = '#f4f2ea';

// ---------- types ----------

interface ScreenData {
  type: string;
  data: Record<string, unknown>;
}

interface DevicePreviewProps {
  screen: ScreenData | null;
  size?: number;
}

// ---------- helpers ----------

function useTime(): string {
  const [time, setTime] = useState(() => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  });
  useEffect(() => {
    const id = setInterval(() => {
      const now = new Date();
      setTime(`${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`);
    }, 30_000);
    return () => clearInterval(id);
  }, []);
  return time;
}

function asString(v: unknown, fallback = ''): string {
  return typeof v === 'string' ? v : fallback;
}

function asNumber(v: unknown, fallback = 0): number {
  return typeof v === 'number' ? v : fallback;
}

function asStringArray(v: unknown): string[] {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : [];
}

// ---------- screen renderers ----------

/** A1 — Ambient: streak + live clock */
function ScreenA1({ data, s }: { data: Record<string, unknown>; s: ReturnType<typeof makeScales> }) {
  const time = useTime();
  const streak = asNumber(data.streak, 0);

  return (
    <>
      <Text style={[styles.topLabel, { fontSize: s.tiny, color: INK }]}>{time}</Text>
      <Text style={[styles.bigNumber, { fontSize: s.huge, color: INK, lineHeight: s.huge * 1.05 }]}>
        {streak}
      </Text>
      <Text style={[styles.subLabel, { fontSize: s.micro, color: INK }]}>DAY STREAK</Text>
    </>
  );
}

/** A2 — Morning Brief: top task + nonneg checklist */
function ScreenA2({ data, s }: { data: Record<string, unknown>; s: ReturnType<typeof makeScales> }) {
  const task = asString(data.task, '—');
  const nonneg = asStringArray(data.nonneg);
  const completed = asStringArray(data.nonneg_completed);

  return (
    <>
      <Text style={[styles.topLabel, { fontSize: s.tiny, color: INK }]}>TODAY</Text>
      <Text
        style={[styles.centreText, { fontSize: s.medium, color: INK, lineHeight: s.medium * 1.3 }]}
        numberOfLines={2}
      >
        {task}
      </Text>
      <View style={styles.checklist}>
        {nonneg.slice(0, 5).map((item) => {
          const done = completed.includes(item);
          return (
            <View key={item} style={styles.checkRow}>
              <Text style={[styles.checkGlyph, { fontSize: s.micro, color: INK }]}>
                {done ? '✓' : '○'}
              </Text>
              <Text
                style={[
                  styles.checkLabel,
                  { fontSize: s.micro, color: INK, opacity: done ? 0.35 : 0.85 },
                ]}
                numberOfLines={1}
              >
                {item}
              </Text>
            </View>
          );
        })}
      </View>
    </>
  );
}

/** A3 — Nudge: centred message */
function ScreenA3({ data, s }: { data: Record<string, unknown>; s: ReturnType<typeof makeScales> }) {
  const message = asString(data.message, '—');

  return (
    <>
      <Text
        style={[styles.centreText, { fontSize: s.medium, color: INK, lineHeight: s.medium * 1.35 }]}
        numberOfLines={4}
      >
        {message}
      </Text>
      <Text style={[styles.bottomLabel, { fontSize: s.micro, color: INK }]}>TAP TO DISMISS</Text>
    </>
  );
}

/**
 * A4 — Goal Progress: large pct + arc border simulation.
 *
 * Arc approach: the outer ring is split into two half-circle views rotated to
 * form a progress arc — no SVG, pure View borderRadius trick.
 */
function ScreenA4({ data, s, size }: { data: Record<string, unknown>; s: ReturnType<typeof makeScales>; size: number }) {
  const pct = Math.min(1, Math.max(0, asNumber(data.pct, 0)));
  const label = asString(data.label, '');
  const daysLeft = asNumber(data.days_left, 0);
  const pctDisplay = `${Math.round(pct * 100)}%`;

  // Arc drawn as two masked half-rings.
  // We use a thick-bordered circle clip trick:
  // - A full ring (opacity ~0.1) as the track
  // - A progress indicator via border opacity based on progress
  const ringSize = size * 0.88;
  const ringBorder = size * 0.055;

  return (
    <>
      {/* Track ring */}
      <View
        style={{
          position: 'absolute',
          width: ringSize,
          height: ringSize,
          borderRadius: ringSize / 2,
          borderWidth: ringBorder,
          borderColor: `rgba(20,19,13,0.1)`,
        }}
      />
      {/* Progress ring — rotate to fill proportionally */}
      <ProgressArc pct={pct} size={ringSize} border={ringBorder} />

      <Text style={[styles.topLabel, { fontSize: s.tiny, color: INK }]} numberOfLines={1}>
        {label}
      </Text>
      <Text style={[styles.bigNumber, { fontSize: s.large, color: INK, lineHeight: s.large * 1.1 }]}>
        {pctDisplay}
      </Text>
      <Text style={[styles.subLabel, { fontSize: s.micro, color: INK }]}>
        {daysLeft} DAYS LEFT
      </Text>
    </>
  );
}

/**
 * Arc progress rendered as two clipped half-ring Views.
 * For pct ≤ 0.5: only the right half is shown (rotated).
 * For pct > 0.5: right half full + left half partially shown.
 */
function ProgressArc({ pct, size, border }: { pct: number; size: number; border: number }) {
  const halfSize = size / 2;
  // Degrees: 0–360
  const degrees = pct * 360;

  // Right half fills first (0→180°), then left half (180→360°)
  const rightDeg = Math.min(degrees, 180);
  const leftDeg = Math.max(0, degrees - 180);

  return (
    <View style={{ position: 'absolute', width: size, height: size }}>
      {/* Container clips each half */}
      {/* Right half — rotates from 0 to 180 */}
      <View
        style={{
          position: 'absolute',
          width: size,
          height: size,
          overflow: 'hidden',
        }}
      >
        <View
          style={{
            position: 'absolute',
            right: 0,
            width: halfSize,
            height: size,
            overflow: 'hidden',
          }}
        >
          <Animated.View
            style={{
              position: 'absolute',
              left: -halfSize,
              width: size,
              height: size,
              borderRadius: size / 2,
              borderWidth: border,
              borderColor: INK,
              transform: [{ rotate: `${rightDeg - 180}deg` }],
            }}
          />
        </View>
      </View>

      {/* Left half — only rendered when pct > 0.5 */}
      {leftDeg > 0 && (
        <View
          style={{
            position: 'absolute',
            width: size,
            height: size,
            overflow: 'hidden',
          }}
        >
          <View
            style={{
              position: 'absolute',
              left: 0,
              width: halfSize,
              height: size,
              overflow: 'hidden',
            }}
          >
            <Animated.View
              style={{
                position: 'absolute',
                left: 0,
                width: size,
                height: size,
                borderRadius: size / 2,
                borderWidth: border,
                borderColor: INK,
                transform: [{ rotate: `${leftDeg}deg` }],
              }}
            />
          </View>
        </View>
      )}
    </View>
  );
}

/** A5 — Heatmap: 5×7 grid of squares */
function ScreenA5({ s, size }: { data: Record<string, unknown>; s: ReturnType<typeof makeScales>; size: number }) {
  // Static placeholder grid — actual data would need date-range logic
  const rows = 5;
  const cols = 7;
  const dotSize = Math.floor(size * 0.07);
  const gap = Math.floor(size * 0.025);

  // Pseudo-random fill for visual representation (seeded by day of week)
  const today = new Date().getDay();
  const filled = (r: number, c: number) => (r * 7 + c + today) % 3 !== 0;

  return (
    <>
      <Text style={[styles.topLabel, { fontSize: s.tiny, color: INK }]}>THIS WEEK</Text>
      <View style={styles.gridContainer}>
        {Array.from({ length: rows }).map((_, r) => (
          <View key={r} style={[styles.gridRow, { gap }]}>
            {Array.from({ length: cols }).map((_, c) => (
              <View
                key={c}
                style={{
                  width: dotSize,
                  height: dotSize,
                  backgroundColor: filled(r, c) ? INK : 'rgba(20,19,13,0.12)',
                }}
              />
            ))}
          </View>
        ))}
      </View>
    </>
  );
}

/** A7 — Wind-down: moon glyph, lights-out time, tomorrow task */
function ScreenA7({ data, s }: { data: Record<string, unknown>; s: ReturnType<typeof makeScales> }) {
  const lightsOut = asString(data.lights_out, '—');
  const tomorrowTask = asString(data.tomorrow_task, '—');

  return (
    <>
      <Text style={[styles.moonGlyph, { fontSize: s.large, color: INK }]}>◑</Text>
      <Text style={[styles.subLabel, { fontSize: s.small, color: INK, marginBottom: 4 }]}>
        LIGHTS OUT {lightsOut}
      </Text>
      <Text style={[styles.subLabel, { fontSize: s.micro, color: INK, opacity: 0.6 }]} numberOfLines={1}>
        TOMORROW: {tomorrowTask}
      </Text>
    </>
  );
}

/** Fallback for unknown screen types */
function ScreenUnknown({ type, s }: { type: string; s: ReturnType<typeof makeScales> }) {
  return (
    <Text style={[styles.centreText, { fontSize: s.micro, color: INK, opacity: 0.4 }]}>
      {type}
    </Text>
  );
}

// ---------- scale factory ----------

function makeScales(size: number) {
  const base = size / 280;
  return {
    huge: Math.round(72 * base),
    large: Math.round(48 * base),
    medium: Math.round(18 * base),
    small: Math.round(13 * base),
    tiny: Math.round(10 * base),
    micro: Math.round(9 * base),
  };
}

// ---------- main component ----------

export default function DevicePreview({ screen, size = 280 }: DevicePreviewProps) {
  const s = makeScales(size);
  const inner = size - 4; // slight inset so border doesn't clip content

  const renderContent = () => {
    if (!screen) {
      return (
        <Text style={[styles.centreText, { fontSize: s.micro, color: INK, opacity: 0.3 }]}>
          NO SIGNAL
        </Text>
      );
    }

    const { type, data } = screen;

    switch (type) {
      case 'A1': return <ScreenA1 data={data} s={s} />;
      case 'A2': return <ScreenA2 data={data} s={s} />;
      case 'A3': return <ScreenA3 data={data} s={s} />;
      case 'A4': return <ScreenA4 data={data} s={s} size={inner} />;
      case 'A5': return <ScreenA5 data={data} s={s} size={inner} />;
      case 'A7': return <ScreenA7 data={data} s={s} />;
      default:   return <ScreenUnknown type={type} s={s} />;
    }
  };

  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: PAPER,
        borderWidth: 2,
        borderColor: INK,
        overflow: 'hidden',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {renderContent()}
    </View>
  );
}

// ---------- shared styles ----------

const styles = StyleSheet.create({
  topLabel: {
    position: 'absolute',
    top: '18%',
    textAlign: 'center',
    fontWeight: '600',
    letterSpacing: 2,
    opacity: 0.55,
  },
  bottomLabel: {
    position: 'absolute',
    bottom: '16%',
    textAlign: 'center',
    fontWeight: '600',
    letterSpacing: 1.5,
    opacity: 0.4,
  },
  subLabel: {
    textAlign: 'center',
    fontWeight: '600',
    letterSpacing: 2,
    marginTop: 4,
  },
  bigNumber: {
    fontWeight: '700',
    letterSpacing: -1,
    textAlign: 'center',
  },
  centreText: {
    textAlign: 'center',
    fontWeight: '500',
    paddingHorizontal: '12%',
  },
  moonGlyph: {
    textAlign: 'center',
    marginBottom: 12,
  },
  checklist: {
    marginTop: 8,
    width: '70%',
  },
  checkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 3,
  },
  checkGlyph: {
    marginRight: 5,
    fontWeight: '600',
  },
  checkLabel: {
    flex: 1,
    fontWeight: '400',
  },
  gridContainer: {
    marginTop: 10,
    alignItems: 'center',
    gap: 4,
  },
  gridRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
