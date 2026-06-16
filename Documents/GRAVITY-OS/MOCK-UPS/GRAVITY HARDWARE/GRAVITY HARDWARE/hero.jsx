/* GRAVITY finished-object mockup — the matte-black puck in its base, plus the
   round 2.8″ LCD "glance" face rendered in the real Space Mono circular grammar. */

// The e-ink glance screen (reusable). r ~ 200 in a 0..440 box.
function EinkFace({ size = 360, x, y }) {
  const cx = 220, cy = 220, R = 196;
  // perimeter ticks
  const ticks = [];
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2 - Math.PI / 2;
    const long = i % 6 === 0;
    const r1 = R - (long ? 13 : 7);
    ticks.push(
      <line key={i} x1={cx + Math.cos(a) * r1} y1={cy + Math.sin(a) * r1}
        x2={cx + Math.cos(a) * R} y2={cy + Math.sin(a) * R}
        stroke="#15140f" strokeWidth={long ? 1.4 : 0.8} opacity={long ? 0.7 : 0.32} />
    );
  }
  // progress arc 0.64
  const prog = 0.64;
  const arcR = R - 4;
  const a0 = -Math.PI / 2;
  const a1 = a0 + prog * Math.PI * 2;
  const large = prog > 0.5 ? 1 : 0;
  const ax0 = cx + Math.cos(a0) * arcR, ay0 = cy + Math.sin(a0) * arcR;
  const ax1 = cx + Math.cos(a1) * arcR, ay1 = cy + Math.sin(a1) * arcR;
  const dotx = ax1, doty = ay1;

  return (
    <svg viewBox="0 0 440 440" width={size} height={size} x={x} y={y} className="eink-face">
      <defs>
        <radialGradient id="paperG" cx="42%" cy="36%" r="75%">
          <stop offset="0%" stopColor="#F3EFE4" />
          <stop offset="70%" stopColor="#ECE7DA" />
          <stop offset="100%" stopColor="#DED8C8" />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={R + 4} fill="url(#paperG)" />
      <circle cx={cx} cy={cy} r={R + 4} fill="none" stroke="#15140f" strokeOpacity="0.10" strokeWidth="1" />
      {ticks}
      {/* progress arc */}
      <path d={`M${ax0},${ay0} A${arcR},${arcR} 0 ${large} 1 ${ax1},${ay1}`}
        fill="none" stroke="#15140f" strokeWidth="5" strokeLinecap="round" />
      <circle cx={dotx} cy={doty} r="5.5" fill="#E0794A" />
      {/* top rim text */}
      <text x={cx} y="64" textAnchor="middle" className="ef-rim">GRAVITY OS v1.0.2</text>
      {/* centre dominant */}
      <text x={cx} y={cy + 6} textAnchor="middle" className="ef-big">14</text>
      <text x={cx} y={cy + 44} textAnchor="middle" className="ef-mid">DAYS ON TRACK</text>
      {/* mid-ring supporting */}
      <text x={cx} y={cy - 58} textAnchor="middle" className="ef-sup">WELCOME BACK, MICHAEL</text>
      {/* bottom rim context */}
      <text x={cx} y={cy + 118} textAnchor="middle" className="ef-ctx">NON-NEGOTIABLES · 3 / 3</text>
      <text x={cx} y="392" textAnchor="middle" className="ef-rim">▸ STREAK PROTECTED · SILENT</text>
    </svg>
  );
}
window.EinkFace = EinkFace;

// The whole device, seated and tilted in its base.
function HeroObject() {
  return (
    <svg viewBox="0 0 560 660" className="hero-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <radialGradient id="shellG" cx="38%" cy="30%" r="85%">
          <stop offset="0%" stopColor="#26262a" />
          <stop offset="46%" stopColor="#121214" />
          <stop offset="100%" stopColor="#050506" />
        </radialGradient>
        <radialGradient id="bezelG" cx="40%" cy="32%" r="80%">
          <stop offset="0%" stopColor="#2c2c30" />
          <stop offset="100%" stopColor="#08080a" />
        </radialGradient>
        <linearGradient id="baseG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#202024" />
          <stop offset="100%" stopColor="#0a0a0c" />
        </linearGradient>
        <radialGradient id="floorG" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(0,0,0,0.55)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0)" />
        </radialGradient>
      </defs>

      {/* floor shadow */}
      <ellipse cx="280" cy="612" rx="190" ry="30" fill="url(#floorG)" />

      {/* base puck */}
      <g>
        <path d="M150,556 Q150,520 196,516 L364,516 Q410,520 410,556 L404,594 Q400,612 372,612 L188,612 Q160,612 156,594 Z"
          fill="url(#baseG)" stroke="rgba(255,255,255,0.07)" strokeWidth="1" />
        {/* top rim light */}
        <path d="M196,517 L364,517" stroke="rgba(255,255,255,0.10)" strokeWidth="1.5" />
        {/* seating well */}
        <ellipse cx="280" cy="524" rx="116" ry="16" fill="#050506" />
        <ellipse cx="280" cy="522" rx="116" ry="15" fill="none" stroke="rgba(255,255,255,0.05)" />
      </g>

      {/* device, tilted back ~9deg, seated in well */}
      <g transform="rotate(-7 280 300)">
        {/* outer shell ring */}
        <circle cx="280" cy="262" r="216" fill="url(#shellG)" />
        <circle cx="280" cy="262" r="216" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
        {/* bezel */}
        <circle cx="280" cy="262" r="208" fill="url(#bezelG)" />
        {/* inner bezel ring around the smaller 2.8″ LCD */}
        <circle cx="280" cy="262" r="132" fill="#060607" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
        {/* screen — 2.8″ round LCD */}
        <EinkFace size={252} x={154} y={136} />
        {/* status dot (single accent) */}
        <circle cx="280" cy="462" r="3" fill="#E0794A" opacity="0.9" />
      </g>
    </svg>
  );
}
window.HeroObject = HeroObject;
