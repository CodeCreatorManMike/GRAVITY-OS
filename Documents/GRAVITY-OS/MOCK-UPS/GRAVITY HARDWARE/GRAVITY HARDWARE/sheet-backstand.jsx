/* SHEET ST-06 — Flip-out backstand. Side elevation of the device FREE-STANDING
   off its base on the deployed kickstand, the stand STOWED flush in the back
   shell, and a 4:1 hinge detail. The case is 3D-printed (PETG); the stand is a
   moulded leg on a printed pin that pops out with a fingernail. */
function SheetBackstand() {
  const { Note, AngDim, DwgDefs, SheetBacking, ScaleBar, TitleBlock, profilePath } = window;
  const W = 940, H = 690;

  /* ---- DEPLOYED (free-standing) ---- */
  const tilt = 15;                 // back-lean of the free-standing device
  const P = [250, 470];            // rotation pivot (front-bottom corner)
  const rot = (x, y) => {
    const r = (tilt * Math.PI) / 180, c = Math.cos(r), s = Math.sin(r);
    const dx = x - P[0], dy = y - P[1];
    return [P[0] + dx * c - dy * s, P[1] + dx * s + dy * c];
  };
  // body box: profilePath(250,320,300,150) → front x250 y170..470, back apex 400
  const FB = rot(250, 470);        // front-bottom corner
  const BB = rot(388, 470);        // back-bottom corner (low contact)
  const FT = rot(250, 170);        // front-top corner
  const Hl = rot(388, 300);        // hinge on the back, mid-low
  const groundY = Math.max(FB[1], BB[1]) + 0;
  const SF = [BB[0] + 52, groundY];// stand foot, behind the back edge
  const angFT = (Math.atan2(FT[1] - FB[1], FT[0] - FB[0]) * 180) / Math.PI;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="dwg-svg" preserveAspectRatio="xMidYMid meet">
      <DwgDefs />
      <SheetBacking w={W} h={H} />

      {/* ===================== DEPLOYED / FREE-STANDING ===================== */}
      <text x={250} y={78} className="vw-label" textAnchor="middle">OFF-DOCK · FREE-STANDING</text>
      <text x={250} y={96} className="vw-dim" textAnchor="middle">BACKSTAND DEPLOYED</text>

      {/* ground line */}
      <line x1={96} y1={groundY} x2={470} y2={groundY} className="pt-center" />
      {[120, 150, 180, 210].map((x) => (
        <line key={x} x1={x} y1={groundY} x2={x - 9} y2={groundY + 9} className="pt-faint" />
      ))}

      {/* backstand leg (drawn first; device overlaps the hinge end) */}
      <g>
        <path d={`M${Hl[0]},${Hl[1]} L${SF[0]},${SF[1]}`} className="pt-stand" />
        <path d={`M${Hl[0]},${Hl[1]} L${SF[0]},${SF[1]}`} className="pt-stand-hi" />
        {/* foot pad */}
        <line x1={SF[0] - 11} y1={SF[1]} x2={SF[0] + 7} y2={SF[1]} className="pt-stand" />
      </g>

      {/* device body, leaned back */}
      <g transform={`rotate(${tilt} ${P[0]} ${P[1]})`}>
        <path d={profilePath(250, 320, 300, 150)} className="pt-shell" />
        <path d={profilePath(250, 320, 300, 150)} className="pt-line" fill="none" />
        {/* 2.8" LCD band on the front face (shorter than full face) */}
        <rect x={250} y={228} width="8" height="184" className="pt-glass2" />
        <line x1={259} y1={232} x2={259} y2={408} className="pt-faint" />
        {/* recess the stand folds into */}
        <path d="M384,236 C398,272 398,330 388,360" className="pt-hidden" />
        {/* hinge pivot */}
        <circle cx={388} cy={300} r="4.5" className="pt-mag" />
        <circle cx={388} cy={300} r="1.6" className="pt-pogo-fill" />
      </g>

      {/* free-stand tilt angle (front face vs vertical) */}
      <line x1={FB[0]} y1={FB[1]} x2={FB[0]} y2={FB[1] - 120} className="pt-faint" />
      <AngDim cx={FB[0]} cy={FB[1]} r={92} a0={-90} a1={angFT} label="15–25°" />

      {/* deployed leaders */}
      <Note id="bs-leg" x={(Hl[0] + SF[0]) / 2 + 4} y={(Hl[1] + SF[1]) / 2} tx={486} ty={486} side="R"
        name="Flip-out backstand" sub="moulded PETG leg · fingernail-deploy" tag="NEW" />
      <Note id="bs-disp" x={rot(250, 320)[0] + 6} y={rot(250, 320)[1]} tx={172} ty={250} side="L"
        name="2.8″ LCD faces user" sub="screen tilts up at ~18°" />
      <Note id="bs-foot" x={SF[0]} y={SF[1]} tx={486} ty={560} side="R"
        name="Stand foot + back edge" sub="two-point free-stand · no base needed" />

      {/* ===================== STOWED (flush) ===================== */}
      <text x={648} y={120} className="vw-label" textAnchor="middle">STOWED — FLUSH</text>
      <text x={648} y={138} className="vw-dim" textAnchor="middle">PROFILE · IN BACK SHELL</text>

      <g>
        <path d={profilePath(596, 236, 200, 104)} className="pt-shell" />
        <path d={profilePath(596, 236, 200, 104)} className="pt-line" fill="none" />
        {/* LCD band */}
        <rect x={596} y={175} width="6" height="122" className="pt-glass2" />
        {/* stand stowed flush against the convex back (hidden) */}
        <path d="M686,182 C698,214 698,260 688,292" className="pt-hidden" />
        {/* hinge + fingernail nick */}
        <circle cx={686} cy={184} r="3.4" className="pt-anchor" />
        <path d="M682,294 q7,6 14,0" className="pt-faint" />
        <text x={712} y={210} className="dl-sub">stand</text>
        <text x={712} y={224} className="dl-sub">flush ±0.4</text>
        <text x={648} y={372} className="vw-dim" textAnchor="middle">CLEAN BACK PROFILE PRESERVED</text>
      </g>

      {/* ===================== DETAIL C — hinge (4:1) ===================== */}
      <circle cx={690} cy={236} r={42} className="pt-detail-ring" />
      <line x1={700} y1={274} x2={628} y2={406} className="pt-detail-leader" />
      <g transform="translate(596 398)">
        <rect x="0" y="0" width="300" height="184" rx="4" className="pt-detail-box" />
        <text x="14" y="24" className="vw-dim">DETAIL C · BACKSTAND HINGE (4:1)</text>

        {/* back shell wall + recess pocket the leg nests into */}
        <path d="M150,44 C136,82 136,134 150,168" className="pt-line" fill="none" />
        <path d="M150,56 C134,84 134,128 150,156" className="pt-hidden" fill="none" />

        {/* stand leg, swung partway out of the recess */}
        <g transform="rotate(-28 60 104)">
          <rect x="60" y="97" width="92" height="14" rx="7" className="iso-face" />
          <rect x="60" y="97" width="92" height="14" rx="7" className="pt-line" fill="none" />
        </g>
        {/* hinge pin */}
        <circle cx="60" cy="104" r="9" className="pt-mag" />
        <circle cx="60" cy="104" r="2.6" className="pt-pogo-fill" />
        {/* detent bump */}
        <circle cx="84" cy="120" r="3.4" className="pt-anchor" />
        {/* fingernail pull recess + arrow */}
        <path d="M150,150 q-9,8 -2,18" className="pt-line" fill="none" />
        <path d="M150,150 l13,-3 -3,12" className="pt-stand-hi" fill="none" />

        {/* notes column */}
        <text x="178" y="58" className="dl-name">Printed pin · Ø1.5</text>
        <text x="178" y="74" className="dl-sub">moulded PETG leg</text>
        <text x="178" y="100" className="dl-name">Detent</text>
        <text x="178" y="116" className="dl-sub">holds leg open ~18°</text>
        <text x="178" y="142" className="dl-tag" fill="#e0794a">fingernail pull recess</text>
        <text x="178" y="158" className="dl-sub">no button · no latch</text>
      </g>

      <ScaleBar x={40} y={H - 42} />
      <TitleBlock w={W} h={H} no="ST-06" title="FLIP-OUT BACKSTAND" scale="ELEV + 4:1" sht="SHT 6/6" />
    </svg>
  );
}
window.SheetBackstand = SheetBackstand;
