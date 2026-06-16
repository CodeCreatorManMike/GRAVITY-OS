/* SHEET GA-01 — General Arrangement. Front elevation + edge-on profile with
   full dimensional callouts (Ø, depth, bezel) and projection alignment. */
function SheetGA() {
  const { Dim, Ext, Dia, Note, DwgDefs, SheetBacking, ScaleBar, TitleBlock, DeviceFront, profilePath } = window;
  const W = 940, H = 620;
  const cx = 300, cy = 318, R = 174;        // front elevation
  const dr = R - R * (DRAW.bezel / DRAW.od) * 2;
  const pfx = 632, depth = 150, apex = pfx + depth; // profile (front flat left)
  const t = R;                               // profile half-height == front R

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="dwg-svg" preserveAspectRatio="xMidYMid meet">
      <DwgDefs />
      <SheetBacking w={W} h={H} />

      {/* projection alignment between the two views */}
      <line x1={cx + R} y1={cy - R} x2={apex + 18} y2={cy - R} className="pt-proj" />
      <line x1={cx + R} y1={cy + R} x2={apex + 18} y2={cy + R} className="pt-proj" />
      <line x1={cx + R + 24} y1={cy} x2={apex + 56} y2={cy} className="pt-center" />

      {/* FRONT ELEVATION */}
      <DeviceFront cx={cx} cy={cy} R={R} screen={false} />
      <text x={cx} y={cy + R + 40} className="vw-label" textAnchor="middle">FRONT ELEVATION</text>

      {/* outer Ø + display Ø */}
      <Dia cx={cx} cy={cy} r={R} angle={-32} label="Ø116" cls="acc" lo={0.5} />
      <Dia cx={cx} cy={cy} r={dr} angle={34} label="Ø71" lo={-0.52} />
      {/* overall width (top) */}
      <Ext x1={cx - R} y1={cy - R} x2={cx - R} y2={106} />
      <Ext x1={cx + R} y1={cy - R} x2={cx + R} y2={106} />
      <Dim ax={cx - R} ay={114} bx={cx + R} by={114} label="116  (110–120)" />
      {/* overall height (left) */}
      <Ext x1={cx - R} y1={cy - R} x2={92} y2={cy - R} />
      <Ext x1={cx - R} y1={cy + R} x2={92} y2={cy + R} />
      <Dim ax={100} ay={cy - R} bx={100} by={cy + R} label="116" />
      {/* bezel callout */}
      <Note id="ga-bez" x={cx} y={cy - R + 7} tx={cx + 4} ty={168} side="R"
        name="Bezel band" sub="~22 mm · matte soft-touch" />
      {/* display callout */}
      <Note id="ga-disp" x={cx - dr * 0.72} y={cy + dr * 0.72} tx={188} ty={cy + R - 6} side="L"
        name="2.8″ round LCD" sub="Ø71 active · backlit TFT" />

      {/* PROFILE / SIDE */}
      <path d={profilePath(pfx, cy, R * 2, depth)} className="pt-shell" />
      <path d={profilePath(pfx, cy, R * 2, depth)} className="pt-line" fill="none" />
      {/* front stack band (display assembly thickness) */}
      <line x1={pfx + 9} y1={cy - t + 3} x2={pfx + 9} y2={cy + t - 3} className="pt-faint" />
      <rect x={pfx} y={cy - t} width="9" height={t * 2} className="pt-glass2" />
      <text x={(pfx + apex) / 2} y={cy + R + 40} className="vw-label" textAnchor="middle">PROFILE A–A</text>

      {/* depth dim (bottom) */}
      <Ext x1={pfx} y1={cy + t} x2={pfx} y2={H - 96} />
      <Ext x1={apex} y1={cy} x2={apex} y2={H - 96} />
      <Dim ax={pfx} ay={H - 104} bx={apex} by={H - 104} label="50  (45–55)" cls="acc" />
      {/* front face + back notes */}
      <Note id="ga-front" x={pfx + 4} y={cy - t * 0.55} tx={pfx - 10} ty={150} side="L"
        name="Display face" sub="flat · faces user" />
      <Note id="ga-back" x={apex - 4} y={cy - t * 0.3} tx={788} ty={150} side="R"
        name="Convex back" sub="cupped-palm · no ports" />

      <ScaleBar x={40} y={H - 44} />
      <TitleBlock w={W} h={H} no="GA-01" title="GENERAL ARRANGEMENT" scale="≈1:1" sht="SHT 1/6" />
    </svg>
  );
}
window.SheetGA = SheetGA;
