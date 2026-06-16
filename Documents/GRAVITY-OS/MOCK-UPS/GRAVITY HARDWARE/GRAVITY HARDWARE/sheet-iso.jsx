/* SHEET IS-03 — Isometric / 3-quarter technical view. Extruded disc with a
   foreshortened live face, seated tilted in its base, leader callouts. */
function isoDisc(cx, cy, rx, ry, vx, vy) {
  const va = Math.atan2(vy, vx);
  const t1 = va + Math.PI / 2, t2 = va - Math.PI / 2;
  const e = (t) => [cx + rx * Math.cos(t), cy + ry * Math.sin(t)];
  const p1 = e(t1), p2 = e(t2);
  const p1b = [p1[0] + vx, p1[1] + vy], p2b = [p2[0] + vx, p2[1] + vy];
  const wall = `M${p1[0]},${p1[1]} A${rx},${ry} 0 0 1 ${p2[0]},${p2[1]} ` +
    `L${p2b[0]},${p2b[1]} A${rx},${ry} 0 0 0 ${p1b[0]},${p1b[1]} Z`;
  return { wall, p1, p2, p1b, p2b };
}

function SheetIso() {
  const { Note, AngDim, DwgDefs, SheetBacking, ScaleBar, TitleBlock } = window;
  const W = 940, H = 640;
  // base ellipse
  const bcx = 430, bcy = 472, brx = 150, bry = 52, baseH = 40;
  // device face ellipse (tilted disc), extruded back-up-right
  const dcx = 430, dcy = 300, rx = 150, ry = 168;
  const vx = 26, vy = -52;                    // depth recession vector
  const tilt = -14;
  const disc = isoDisc(dcx, dcy, rx, ry, vx, vy);
  const brx2 = rx - rx * (DRAW.bezel / DRAW.od) * 2;
  const bry2 = ry - ry * (DRAW.bezel / DRAW.od) * 2;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="dwg-svg" preserveAspectRatio="xMidYMid meet">
      <DwgDefs />
      <SheetBacking w={W} h={H} />

      {/* ground shadow */}
      <ellipse cx={bcx + 6} cy={bcy + baseH + 8} rx={brx + 18} ry={28} className="iso-shadow" />

      {/* BASE puck (elliptical cylinder) */}
      <path d={`M${bcx - brx},${bcy} A${brx},${bry} 0 0 0 ${bcx + brx},${bcy} L${bcx + brx},${bcy + baseH} A${brx},${bry} 0 0 1 ${bcx - brx},${bcy + baseH} Z`} className="iso-wall" />
      <ellipse cx={bcx} cy={bcy} rx={brx} ry={bry} className="iso-top" />
      <ellipse cx={bcx} cy={bcy} rx={brx} ry={bry} className="pt-line" fill="none" />
      {/* seating well */}
      <ellipse cx={bcx} cy={bcy - 2} rx={brx * 0.66} ry={bry * 0.6} className="iso-well" />
      <ellipse cx={bcx} cy={bcy - 4} rx={brx * 0.66} ry={bry * 0.6} className="pt-faint" fill="none" />
      {/* USB-C on base rim (right/back) */}
      <rect x={bcx + brx - 30} y={bcy + baseH * 0.42} width="22" height="9" rx="2" className="pt-glass2" />

      {/* DEVICE — tilted, seated */}
      <g transform={`rotate(${tilt} ${dcx} ${bcy})`}>
        {/* extruded body (convex back) */}
        <path d={disc.wall} className="iso-wall" />
        {/* back contour hints */}
        <path d={`M${disc.p1[0] + vx * 0.5},${disc.p1[1] + vy * 0.5} A${rx * 0.9},${ry * 0.9} 0 0 1 ${disc.p2[0] + vx * 0.5},${disc.p2[1] + vy * 0.5}`} className="pt-faint" fill="none" />
        {/* shell ring + bezel */}
        <ellipse cx={dcx} cy={dcy} rx={rx} ry={ry} className="iso-face" />
        <ellipse cx={dcx} cy={dcy} rx={rx} ry={ry} className="pt-line" fill="none" />
        <ellipse cx={dcx} cy={dcy} rx={brx2} ry={bry2} className="pt-line" fill="none" />
        {/* foreshortened live face */}
        <g transform={`translate(${dcx - brx2},${dcy - bry2}) scale(${(2 * brx2) / 440},${(2 * bry2) / 440})`}>
          {window.EinkFace && <window.EinkFace size={440} x={0} y={0} />}
        </g>
      </g>

      {/* tilt angle */}
      <line x1={bcx - 96} y1={bcy} x2={bcx + 120} y2={bcy} className="pt-center" />
      <AngDim cx={bcx - 60} cy={bcy} r={56} a0={180} a1={180 + 18} label="15–25°" />

      {/* leaders */}
      <Note id="is-disp" x={dcx - 36} y={dcy - 30} tx={188} ty={150} side="L"
        name="2.8″ round LCD" sub="backlit TFT · glanceable" tag="GLANCE" />
      <Note id="is-bez" x={dcx + brx2 + 8} y={dcy - 70} tx={748} ty={150} side="R"
        name="Bezel + front shell" sub="8–12 mm soft-touch" />
      <Note id="is-back" x={disc.p1b[0] - 6} y={disc.p1b[1] + 30} tx={748} ty={250} side="R"
        name="Convex back shell" sub="cupped-palm · seamless" />
      <Note id="is-base" x={bcx + brx - 40} y={bcy + baseH * 0.5} tx={748} ty={470} side="R"
        name="Weighted base + USB-C" sub="power-only · tilts 15–25°" tag="5 V" />
      <Note id="is-form" x={dcx - rx + 18} y={dcy + 40} tx={188} ty={300} side="L"
        name="Ø116 circular puck" sub="faces user · not a sphere" />

      <ScaleBar x={40} y={H - 42} />
      <TitleBlock w={W} h={H} no="IS-03" title="ISOMETRIC — 3/4 VIEW" scale="ILLUSTRATIVE" sht="SHT 3/6" />
    </svg>
  );
}
window.SheetIso = SheetIso;
