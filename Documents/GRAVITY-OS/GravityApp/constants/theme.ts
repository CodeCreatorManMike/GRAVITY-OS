// GRAVITY app dark design system
// App = dark mission-control. Device face = warm INK/PAPER (separate).

export const BG        = '#0a0a0a';
export const SURFACE   = '#141414';
export const SURFACE2  = '#1e1e1e';
export const BORDER    = 'rgba(255,255,255,0.08)';
export const WHITE     = '#ffffff';
export const DIM       = 'rgba(255,255,255,0.45)';
export const FAINT     = 'rgba(255,255,255,0.15)';
export const GHOST     = 'rgba(255,255,255,0.06)';

// Device face colours (warm paper palette — used inside DevicePreview only)
export const DEVICE_INK   = '#14130d';
export const DEVICE_PAPER = '#f4f2ea';

// Typography scale
export const T = {
  heading:  { fontSize: 32, fontWeight: '700' as const, color: WHITE, letterSpacing: -0.5 },
  title:    { fontSize: 20, fontWeight: '600' as const, color: WHITE },
  body:     { fontSize: 15, fontWeight: '400' as const, color: WHITE },
  label:    { fontSize: 11, fontWeight: '600' as const, color: DIM, letterSpacing: 1.5 },
  mono:     { fontFamily: 'JetBrainsMono_400Regular', fontSize: 13, color: WHITE },
  monoBold: { fontFamily: 'JetBrainsMono_700Bold', fontSize: 13, color: WHITE },
  caption:  { fontSize: 12, color: DIM },
};

// Spacing
export const S = {
  screen: { paddingHorizontal: 20 },
  card: { borderRadius: 12, padding: 16, backgroundColor: SURFACE },
  row: { paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: BORDER },
};
