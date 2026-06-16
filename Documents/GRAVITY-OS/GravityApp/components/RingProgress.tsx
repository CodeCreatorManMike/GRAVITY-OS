import Svg, { Circle } from 'react-native-svg';

interface Props {
  pct: number;       // 0–1
  size?: number;
  stroke?: number;
  color?: string;
  track?: string;
}

export function RingProgress({
  pct,
  size = 80,
  stroke = 6,
  color = '#ffffff',
  track = 'rgba(255,255,255,0.1)',
}: Props) {
  const clamped = Math.min(1, Math.max(0, pct));
  const r = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  const dashOffset = circumference * (1 - clamped);

  return (
    <Svg width={size} height={size} style={{ transform: [{ rotate: '-90deg' }] }}>
      <Circle cx={cx} cy={cy} r={r} stroke={track} strokeWidth={stroke} fill="none" />
      {clamped > 0 && (
        <Circle
          cx={cx} cy={cy} r={r}
          stroke={color} strokeWidth={stroke} fill="none"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
        />
      )}
    </Svg>
  );
}
