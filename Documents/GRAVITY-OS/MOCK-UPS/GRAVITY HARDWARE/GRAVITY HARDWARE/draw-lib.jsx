/* GRAVITY engineering-drawing primitives — dimension lines, leaders, sheet
   chrome and reusable device geometry. Shares the cross-section drafting
   grammar: cream draw-strokes on dark, orange accent for critical callouts. */

const DRAW = {
  // nominal dims (mm) from the build spec (display revised to 2.8″ LCD)
  od: 116, disp: 71, bezel: 22.5, depth: 50, tilt: 20,
  baseW: 128, baseH: 46,
};
window.DRAW = DRAW;

/* arrow triangle points, tip at (x,y) pointing along ang (rad) */
function triPts(x, y, ang, size) {
  size = size || 8;
  const bx = x - Math.cos(ang) * size, by = y - Math.sin(ang) * size;
  const px = Math.cos(ang + Math.PI / 2), py = Math.sin(ang + Math.PI / 2);
  const w = size * 0.4;
  return `${x},${y} ${bx + px * w},${by + py * w} ${bx - px * w},${by - py * w}`;
}

/* generic linear dimension between two points, arrows pointing outward,
   label centred on the line (rotated to match). cls adds .acc for accent. */
function Dim({ ax, ay, bx, by, label, cls = "", flip = false, gap = 0 }) {
  const ang = Math.atan2(by - ay, bx - ax);
  const mx = (ax + bx) / 2, my = (ay + by) / 2;
  let deg = (ang * 180) / Math.PI;
  if (deg > 90 || deg < -90) deg += 180; // keep text upright
  const off = flip ? 13 : -8;
  return (
    <g className={"dl " + cls}>
      <line x1={ax} y1={ay} x2={bx} y2={by} className="dl-dim" />
      <polygon points={triPts(ax, ay, ang + Math.PI, 8)} className="dl-fill" />
      <polygon points={triPts(bx, by, ang, 8)} className="dl-fill" />
      <text x={mx} y={my} className="dl-txt" textAnchor="middle"
        transform={`rotate(${deg} ${mx} ${my}) translate(0 ${off})`}>{label}</text>
    </g>
  );
}

/* extension line (witness line) */
function Ext({ x1, y1, x2, y2 }) {
  return <line x1={x1} y1={y1} x2={x2} y2={y2} className="dl-ext" />;
}

/* diameter dimension across a circle through its centre at angle deg */
function Dia({ cx, cy, r, angle = -28, label, cls = "", lo = 0 }) {
  const a = (angle * Math.PI) / 180;
  const ax = cx - Math.cos(a) * r, ay = cy - Math.sin(a) * r;
  const bx = cx + Math.cos(a) * r, by = cy + Math.sin(a) * r;
  const lx = cx + Math.cos(a) * r * lo, ly = cy + Math.sin(a) * r * lo;
  return (
    <g className={"dl " + cls}>
      <line x1={ax} y1={ay} x2={bx} y2={by} className="dl-dim" />
      <polygon points={triPts(ax, ay, a + Math.PI, 8)} className="dl-fill" />
      <polygon points={triPts(bx, by, a, 8)} className="dl-fill" />
      <text x={lx} y={ly} className="dl-txt dl-txt-bg" textAnchor="middle"
        transform={`rotate(${angle} ${lx} ${ly}) translate(0 -7)`}>{label}</text>
    </g>
  );
}

/* radial leader callout: dot on feature, knee, then label text block */
function Note({ x, y, tx, ty, side = "R", name, sub, tag, hovered, id, onHover }) {
  const anchor = side === "L" ? "end" : "start";
  const kneeX = tx + (side === "L" ? 26 : -26);
  const on = hovered === id;
  return (
    <g className={"dl-note" + (on ? " on" : "")}
      onMouseEnter={() => onHover && onHover(id)} onMouseLeave={() => onHover && onHover(null)}>
      <polyline points={`${x},${y} ${kneeX},${ty} ${tx},${ty}`} className="dl-leader" />
      <circle cx={x} cy={y} r="3" className="dl-dot" />
      <text x={tx} y={ty - 5} className="dl-name" textAnchor={anchor}>
        {name}{tag && <tspan className="dl-tag">  [{tag}]</tspan>}
      </text>
      {sub && <text x={tx} y={ty + 9} className="dl-sub" textAnchor={anchor}>{sub}</text>}
    </g>
  );
}

/* angular dimension arc between two rays from a vertex */
function AngDim({ cx, cy, r, a0, a1, label }) {
  const r0 = (a0 * Math.PI) / 180, r1 = (a1 * Math.PI) / 180;
  const x0 = cx + Math.cos(r0) * r, y0 = cy + Math.sin(r0) * r;
  const x1 = cx + Math.cos(r1) * r, y1 = cy + Math.sin(r1) * r;
  const large = Math.abs(a1 - a0) > 180 ? 1 : 0;
  const mid = ((a0 + a1) / 2 * Math.PI) / 180;
  const lx = cx + Math.cos(mid) * (r + 16), ly = cy + Math.sin(mid) * (r + 16);
  return (
    <g className="dl">
      <path d={`M${x0},${y0} A${r},${r} 0 ${large} 1 ${x1},${y1}`} className="dl-dim" fill="none" />
      <polygon points={triPts(x0, y0, r0 - Math.PI / 2, 7)} className="dl-fill" />
      <polygon points={triPts(x1, y1, r1 + Math.PI / 2, 7)} className="dl-fill" />
      <text x={lx} y={ly} className="dl-txt" textAnchor="middle" dominantBaseline="middle">{label}</text>
    </g>
  );
}

/* shared defs: grid + hatch */
function DwgDefs() {
  return (
    <defs>
      <pattern id="dgrid" width="28" height="28" patternUnits="userSpaceOnUse">
        <path d="M28 0 L0 0 0 28" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
      </pattern>
      <pattern id="dhatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
        <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(215,210,196,0.28)" strokeWidth="0.7" />
      </pattern>
      <radialGradient id="dpaper" cx="42%" cy="36%" r="75%">
        <stop offset="0%" stopColor="#F3EFE4" /><stop offset="70%" stopColor="#ECE7DA" />
        <stop offset="100%" stopColor="#DED8C8" />
      </radialGradient>
    </defs>
  );
}

/* registration corners + faint grid backing the whole sheet svg */
function SheetBacking({ w, h }) {
  const m = 16;
  return (
    <g>
      <rect x="0" y="0" width={w} height={h} fill="url(#dgrid)" />
      {[[m, m], [w - m, m], [m, h - m], [w - m, h - m]].map((p, i) => (
        <g key={i}>
          <line x1={p[0] - 8} y1={p[1]} x2={p[0] + 8} y2={p[1]} className="dl-reg" />
          <line x1={p[0]} y1={p[1] - 8} x2={p[0]} y2={p[1] + 8} className="dl-reg" />
        </g>
      ))}
    </g>
  );
}

/* scale bar: nominal "drawn at" indicator */
function ScaleBar({ x, y, label = "0  10  20  30  40  50 mm" }) {
  const seg = 13.6; // ~mm at the page scale used in svgs
  return (
    <g className="dl-scalebar">
      <line x1={x} y1={y} x2={x + seg * 5} y2={y} className="dl-dim" />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <g key={i}>
          <line x1={x + seg * i} y1={y - 4} x2={x + seg * i} y2={y + 4} className="dl-dim" />
          {i % 2 === 1 && i < 5 && <rect x={x + seg * (i - 1)} y={y} width={seg} height="4" className="dl-fill" opacity="0.5" />}
        </g>
      ))}
      <text x={x} y={y + 16} className="dl-scale-txt">{label}</text>
    </g>
  );
}

/* drawing title block, bottom-right of a sheet svg */
function TitleBlock({ w, h, no, title, scale = "1:1", proj = "THIRD ANGLE", sht }) {
  const bw = 300, bh = 64, x = w - bw - 18, y = h - bh - 16;
  return (
    <g className="dl-title">
      <rect x={x} y={y} width={bw} height={bh} className="dl-title-box" />
      <line x1={x} y1={y + 26} x2={x + bw} y2={y + 26} className="dl-title-div" />
      <line x1={x + 188} y1={y} x2={x + 188} y2={y + bh} className="dl-title-div" />
      <text x={x + 12} y={y + 17} className="dl-title-h">GRAVITY · V1 DEMO UNIT</text>
      <text x={x + 12} y={y + 44} className="dl-title-t">{title}</text>
      <text x={x + 12} y={y + 57} className="dl-title-s">{proj} · NOT TO SCALE</text>
      <text x={x + 198} y={y + 17} className="dl-title-s">DWG {no}</text>
      <text x={x + 198} y={y + 44} className="dl-title-s">SCALE {scale}</text>
      <text x={x + 198} y={y + 57} className="dl-title-s">{sht}</text>
    </g>
  );
}

/* ---- reusable device geometry ----------------------------------------- */

/* front elevation: shell ring + bezel + round display (optional LCD UI face) */
function DeviceFront({ cx, cy, R, screen = false, center = true, sn = 1 }) {
  const bez = R * (DRAW.bezel / DRAW.od) * 2; // bezel band width
  const dr = R - bez;
  return (
    <g>
      {center && (
        <g className="pt-center-g">
          <line x1={cx - R - 22} y1={cy} x2={cx + R + 22} y2={cy} className="pt-center" />
          <line x1={cx} y1={cy - R - 22} x2={cx} y2={cy + R + 22} className="pt-center" />
        </g>
      )}
      <circle cx={cx} cy={cy} r={R} className="pt-shell" />
      <circle cx={cx} cy={cy} r={R - 2.5} className="pt-faint" fill="none" />
      <circle cx={cx} cy={cy} r={dr} className="pt-line" fill="none" />
      {screen && window.EinkFace ? (
        <window.EinkFace size={(dr - 1) * 2} x={cx - (dr - 1)} y={cy - (dr - 1)} />
      ) : (
        <circle cx={cx} cy={cy} r={dr - 1} className="pt-glass" />
      )}
    </g>
  );
}

/* edge-on profile: flat front (left), convex back (right). returns path d */
function profilePath(x, y, h, depth) {
  const t = h / 2;
  return `M${x},${y - t} L${x},${y + t} ` +
    `C${x + depth * 0.92},${y + t} ${x + depth},${y + t * 0.55} ${x + depth},${y} ` +
    `C${x + depth},${y - t * 0.55} ${x + depth * 0.92},${y - t} ${x},${y - t} Z`;
}

Object.assign(window, {
  triPts, Dim, Ext, Dia, Note, AngDim, DwgDefs, SheetBacking, ScaleBar,
  TitleBlock, DeviceFront, profilePath,
});
