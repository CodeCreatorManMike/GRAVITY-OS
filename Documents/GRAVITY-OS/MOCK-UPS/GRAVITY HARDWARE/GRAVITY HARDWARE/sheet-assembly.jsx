/* SHEET AS-05 — Device + base seating detail. Side section through the
   lift-out joint: pogo contacts, magnets, tilt, with a zoomed detail bubble. */
function SheetAssembly() {
  const { Note, AngDim, DwgDefs, SheetBacking, ScaleBar, TitleBlock, profilePath } = window;
  const W = 940, H = 640;
  const tilt = -17;
  const pivot = [392, 470];                       // seating contact

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="dwg-svg" preserveAspectRatio="xMidYMid meet">
      <DwgDefs />
      <SheetBacking w={W} h={H} />

      {/* ground line */}
      <line x1={120} y1={556} x2={620} y2={556} className="pt-center" />

      {/* BASE — weighted puck cross-section */}
      <path d="M236,468 Q230,452 256,448 L300,448 L320,470 L470,470 L490,448 L532,448 Q556,452 550,470 L542,540 Q540,556 514,556 L262,556 Q238,556 236,540 Z" className="iso-wall" />
      {/* weighted floor ballast */}
      <rect x="252" y="520" width="280" height="26" className="pt-hatch" />
      <line x1="252" y1="520" x2="532" y2="520" className="pt-line" />
      {/* base PCB */}
      <rect x="300" y="494" width="190" height="7" rx="1" className="ex-pcb" />
      {/* USB-C receptacle (right) */}
      <rect x="506" y="486" width="40" height="20" rx="3" className="pt-glass2" />
      <rect x="534" y="491" width="14" height="10" rx="2" className="pt-faint-fill" />
      {/* TVS/PTC */}
      <rect x="440" y="488" width="22" height="14" rx="1.5" className="ex-ic" />

      {/* DEVICE — tilted, seated in the well */}
      <g transform={`rotate(${tilt} ${pivot[0]} ${pivot[1]})`}>
        <path d={profilePath(300, 300, 300, 128)} className="iso-face" />
        <path d={profilePath(300, 300, 300, 128)} className="pt-line" fill="none" />
        {/* front display band */}
        <rect x="300" y="156" width="9" height="288" className="pt-glass2" />
        {/* faint internals for context */}
        <line x1="372" y1="160" x2="372" y2="440" className="pt-faint" />
        <rect x="378" y="206" width="46" height="190" rx="6" className="ex-batt" opacity="0.5" />
        {/* device pogo spring contacts on back-bottom */}
        <path d="M356,452 v18 M376,452 v18" className="pt-pogo-line" />
        <circle cx="356" cy="470" r="3.4" className="pt-pogo-fill" />
        <circle cx="376" cy="470" r="3.4" className="pt-pogo-fill" />
        {/* magnet in device */}
        <rect x="332" y="448" width="14" height="16" rx="2" className="pt-mag" />
      </g>

      {/* base pogo receptacles + magnet (un-rotated, in well) */}
      <rect x="344" y="470" width="44" height="9" rx="2" className="ex-ic" />
      <rect x="318" y="470" width="16" height="16" rx="2" className="pt-mag" />

      {/* tilt angle */}
      <line x1={pivot[0] - 150} y1={pivot[1]} x2={pivot[0] + 40} y2={pivot[1]} className="pt-center" />
      <AngDim cx={pivot[0] - 120} cy={pivot[1]} r={70} a0={180} a1={180 + 18} label="15–25° TILT" />

      {/* DETAIL bubble — pogo joint */}
      <circle cx={372} cy={466} r={48} className="pt-detail-ring" />
      <line x1={408} y1={440} x2={690} y2={250} className="pt-detail-leader" />
      <g transform="translate(690 130)">
        <rect x="0" y="0" width="210" height="210" rx="4" className="pt-detail-box" />
        <text x="12" y="22" className="vw-dim">DETAIL B · LIFT-OUT JOINT (4:1)</text>
        {/* device contact (top) */}
        <rect x="40" y="44" width="130" height="16" rx="2" className="iso-face" />
        <text x="105" y="40" textAnchor="middle" className="dl-sub">DEVICE BACK</text>
        <path d="M78,60 v22 M132,60 v22" className="pt-pogo-line" />
        {/* spring coils */}
        <path d="M78,64 l6,4 -12,4 12,4 -12,4 6,4" className="pt-pogo-line" fill="none" />
        <path d="M132,64 l6,4 -12,4 12,4 -12,4 6,4" className="pt-pogo-line" fill="none" />
        <circle cx="62" cy="52" r="7" className="pt-mag" />
        {/* base receptacle (bottom) */}
        <rect x="40" y="92" width="130" height="18" rx="2" className="ex-ic" />
        <circle cx="78" cy="92" r="4" className="pt-pogo-fill" />
        <circle cx="132" cy="92" r="4" className="pt-pogo-fill" />
        <circle cx="62" cy="100" r="7" className="pt-mag" />
        <text x="105" y="130" textAnchor="middle" className="dl-sub">BASE RECEPTACLE</text>
        <text x="12" y="158" className="dl-name">VBUS + GND only</text>
        <text x="12" y="174" className="dl-sub">2 spring contacts · ~1 A</text>
        <text x="12" y="190" className="dl-sub">magnets seat + hold tilt</text>
        <text x="12" y="204" className="dl-tag" fill="#e0794a">device runs on battery when lifted</text>
      </g>

      {/* leaders */}
      <Note id="as-usb" x={526} y={496} tx={748} ty={420} side="R" name="USB-C receptacle" sub="power-only · 5.1 kΩ CC" tag="5 V" />
      <Note id="as-floor" x={392} y={533} tx={210} ty={540} side="L" name="Weighted floor + foot ring" sub="stability ballast" />
      <Note id="as-base" x={470} y={497} tx={748} ty={500} side="R" name="Base PCB" sub="small 2-layer input board" />
      <Note id="as-disp" x={326} y={210} tx={188} ty={170} side="L" name="Display face" sub="UI rotates when lifted" />

      <ScaleBar x={40} y={H - 42} />
      <TitleBlock w={W} h={H} no="AS-05" title="BASE — SEATING DETAIL" scale="SECTION + 4:1" sht="SHT 5/6" />
    </svg>
  );
}
window.SheetAssembly = SheetAssembly;
