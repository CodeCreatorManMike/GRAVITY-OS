/* SHEET OR-02 — Orthographic elevations in third-angle projection:
   FRONT (centre, live LCD face), TOP plan, RIGHT side profile, REAR. */
function planPath(cx, pcy, w, d) {
  const hw = w / 2, hd = d / 2, by = pcy + hd, ty = pcy - hd;
  return `M${cx - hw},${by} L${cx + hw},${by} ` +
    `C${cx + hw},${ty + hd * 0.6} ${cx + hw * 0.55},${ty} ${cx},${ty} ` +
    `C${cx - hw * 0.55},${ty} ${cx - hw},${ty + hd * 0.6} ${cx - hw},${by} Z`;
}

function SheetOrtho() {
  const { Dim, Ext, DwgDefs, SheetBacking, ScaleBar, TitleBlock, DeviceFront, profilePath } = window;
  const W = 940, H = 600;
  const R = 100;
  const fcx = 258, fcy = 318;                       // FRONT
  const sx = fcx + R + 58, depth = R * 2 * (DRAW.depth / DRAW.od); // RIGHT profile
  const bcx = sx + depth + 80 + R;                  // REAR (clears bottom-right title block)
  const pcy = fcy - R - 66, pd = depth;             // TOP plan

  // back dome contour rings (offset toward upper-left light)
  const rings = [0.86, 0.66, 0.43, 0.2].map((k, i) => ({
    r: R * k, ox: -R * 0.06 * (1 - k), oy: -R * 0.06 * (1 - k), key: i,
  }));

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="dwg-svg" preserveAspectRatio="xMidYMid meet">
      <DwgDefs />
      <SheetBacking w={W} h={H} />

      {/* projection alignment lines (faint) */}
      <line x1={fcx - R} y1={fcy - R} x2={fcx - R} y2={pcy + pd / 2 + 4} className="pt-proj" />
      <line x1={fcx + R} y1={fcy - R} x2={fcx + R} y2={pcy + pd / 2 + 4} className="pt-proj" />
      <line x1={fcx + R} y1={fcy - R} x2={bcx + R + 8} y2={fcy - R} className="pt-proj" />
      <line x1={fcx + R} y1={fcy + R} x2={bcx + R + 8} y2={fcy + R} className="pt-proj" />

      {/* TOP PLAN */}
      <path d={planPath(fcx, pcy, R * 2, pd)} className="pt-shell" />
      <path d={planPath(fcx, pcy, R * 2, pd)} className="pt-line" fill="none" />
      <line x1={fcx - R + 7} y1={pcy + pd / 2 - 6} x2={fcx + R - 7} y2={pcy + pd / 2 - 6} className="pt-faint" />
      <line x1={fcx} y1={pcy - pd / 2 - 16} x2={fcx} y2={pcy + pd / 2 + 16} className="pt-center" />
      <text x={fcx} y={pcy - pd / 2 - 24} className="vw-label" textAnchor="middle">TOP</text>

      {/* FRONT (live face) */}
      <DeviceFront cx={fcx} cy={fcy} R={R} screen={true} />
      <text x={fcx} y={fcy + R + 36} className="vw-label" textAnchor="middle">FRONT</text>
      <text x={fcx} y={fcy + R + 54} className="vw-dim" textAnchor="middle">Ø116 · LCD Ø71</text>

      {/* RIGHT SIDE / PROFILE */}
      <path d={profilePath(sx, fcy, R * 2, depth)} className="pt-shell" />
      <path d={profilePath(sx, fcy, R * 2, depth)} className="pt-line" fill="none" />
      <rect x={sx} y={fcy - R} width="8" height={R * 2} className="pt-glass2" />
      <line x1={sx + 8} y1={fcy - R + 3} x2={sx + 8} y2={fcy + R - 3} className="pt-faint" />
      <line x1={sx - 18} y1={fcy} x2={sx + depth + 20} y2={fcy} className="pt-center" />
      <text x={sx + depth / 2} y={fcy + R + 36} className="vw-label" textAnchor="middle">RIGHT</text>
      <text x={sx + depth / 2} y={fcy + R + 54} className="vw-dim" textAnchor="middle">DEPTH 50</text>

      {/* REAR */}
      <g>
        <circle cx={bcx} cy={fcy} r={R} className="pt-shell" />
        <circle cx={bcx} cy={fcy} r={R - 3} className="pt-hidden" fill="none" />
        {rings.map((rg) => (
          <circle key={rg.key} cx={bcx + rg.ox} cy={fcy + rg.oy} r={rg.r} className="pt-faint" fill="none" />
        ))}
        {/* soft-touch grain ticks */}
        {[-0.5, -0.16, 0.16, 0.5].map((k, i) => (
          <path key={i} d={`M${bcx - 26},${fcy + R * k} q26,${k < 0 ? 8 : -8} 52,0`} className="pt-faint" fill="none" />
        ))}
        {/* parting seam + pogo */}
        <line x1={bcx - 26} y1={fcy} x2={bcx + 26} y2={fcy} className="pt-center" />
        <line x1={bcx} y1={fcy - 26} x2={bcx} y2={fcy + 26} className="pt-center" />
        {/* flip-out backstand — stowed flush, recessed channel (hidden) */}
        <rect x={bcx - 11} y={fcy + R * 0.2} width="22" height={R * 0.62} rx="9" className="pt-hidden" fill="none" />
        <path d={`M${bcx - 7},${fcy + R * 0.2 + R * 0.62 - 4} q7,6 14,0`} className="pt-faint" fill="none" />
        <circle cx={bcx - 30} cy={fcy + R * 0.62} r="5" className="pt-pogo" />
        <circle cx={bcx + 30} cy={fcy + R * 0.62} r="5" className="pt-pogo" />
        <text x={bcx} y={fcy + R + 36} className="vw-label" textAnchor="middle">REAR</text>
        <text x={bcx} y={fcy + R + 54} className="vw-dim" textAnchor="middle">2× POGO · STOWED BACKSTAND</text>
      </g>

      <ScaleBar x={40} y={H - 42} />
      <TitleBlock w={W} h={H} no="OR-02" title="ORTHOGRAPHIC ELEVATIONS" scale="≈1:1" sht="SHT 2/6" />
    </svg>
  );
}
window.SheetOrtho = SheetOrtho;
