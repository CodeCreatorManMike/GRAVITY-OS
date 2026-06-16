/* SHEET EX-04 — Exploded view. Layers spread along the front→back assembly
   axis; toggle to collapse/expand, hover a part to highlight. */
const { useState: _useStateEx } = React;

function discFace(cx, cy, rx, ry) {
  // simplified foreshortened LCD UI face
  const ticks = [];
  for (let i = 0; i < 36; i++) {
    const a = (i / 36) * Math.PI * 2 - Math.PI / 2;
    const long = i % 3 === 0;
    const r1 = 1 - (long ? 0.09 : 0.05);
    ticks.push(<line key={i} x1={cx + Math.cos(a) * rx * r1} y1={cy + Math.sin(a) * ry * r1}
      x2={cx + Math.cos(a) * rx} y2={cy + Math.sin(a) * ry} stroke="#15140f" strokeWidth={long ? 1.1 : 0.6} opacity={long ? 0.55 : 0.28} />);
  }
  return (
    <g>
      <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="url(#dpaper)" />
      {ticks}
      <text x={cx} y={cy + 14} textAnchor="middle" fill="#15140f" fontFamily="'Space Mono',monospace" fontWeight="700" fontSize="46">14</text>
      <text x={cx} y={cy + 38} textAnchor="middle" fill="#15140f" fontFamily="'Space Mono',monospace" fontSize="11" letterSpacing="3" opacity="0.6">DAYS</text>
    </g>
  );
}

function SheetExplode() {
  const { Note, DwgDefs, SheetBacking, ScaleBar, TitleBlock } = window;
  const [exploded, setExploded] = _useStateEx(true);
  const [hov, setHov] = _useStateEx(null);
  const W = 940, H = 740;
  const cx = 388, cy = 360, rx = 132, ry = 150;
  const ex = 48, ey = -70;                       // per-step explode vector
  const off = (i) => exploded ? [(i - 2.5) * ex, (i - 2.5) * ey] : [i * 5, i * -5];

  // each layer: index along axis, drawer, label
  const layers = [
    { i: 0, id: "ov", name: "Touch overlay", sub: "capacitive film · I²C", tag: "RISK", side: "L",
      draw: () => (<g><ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="ex-glass" /><ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="pt-line" fill="none" /></g>) },
    { i: 1, id: "sh", name: "Front shell + bezel", sub: "ABS/PETG · ~22 mm", side: "L",
      draw: () => (<g><ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="ex-shell" /><ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="pt-line" fill="none" /><ellipse cx={cx} cy={cy} rx={rx - 22} ry={ry - 25} className="pt-line" fill="none" /></g>) },
    { i: 2, id: "ep", name: "2.8″ round LCD", sub: "TFT · backlit · SPI", tag: "GLANCE", side: "L",
      draw: () => (<g>{discFace(cx, cy, rx - 24, ry - 27)}<ellipse cx={cx} cy={cy} rx={rx - 24} ry={ry - 27} className="pt-line" fill="none" /></g>) },
    { i: 3, id: "pcb", name: "Main PCB + sensors", sub: "ESP32-S3 · 2-layer Ø75–85", tag: "MCU", side: "R",
      draw: () => (<g>
        <ellipse cx={cx} cy={cy} rx={rx - 14} ry={ry - 16} className="ex-pcb" />
        <ellipse cx={cx} cy={cy} rx={rx - 14} ry={ry - 16} className="pt-line" fill="none" />
        <rect x={cx - 30} y={cy - ry + 34} width="60" height="26" rx="2" className="ex-ic" />
        {[[-46, 12], [22, 6], [-50, 48], [30, 44]].map((p, k) => <rect key={k} x={cx + p[0]} y={cy + p[1]} width="26" height="18" rx="1.5" className="ex-ic" />)}
        <rect x={cx - 8} y={cy + ry - 52} width="16" height="10" rx="1" className="pt-pogo-fill" />
      </g>) },
    { i: 4, id: "bat", name: "LiPo battery", sub: "1500 mAh · JST-SH", tag: "60 nA", side: "R",
      draw: () => (<g><ellipse cx={cx} cy={cy} rx={rx - 30} ry={ry - 34} className="ex-batt" /><ellipse cx={cx} cy={cy} rx={rx - 30} ry={ry - 34} className="pt-line" fill="none" /><text x={cx} y={cy - 2} textAnchor="middle" className="ex-batt-l">LiPo</text><text x={cx} y={cy + 16} textAnchor="middle" className="ex-batt-s">1500 mAh</text></g>) },
    { i: 5, id: "bk", name: "Convex back shell", sub: "soft-touch · cupped-palm", side: "R",
      draw: () => (<g>
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="ex-shell" />
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="pt-line" fill="none" />
        {[0.7, 0.45, 0.22].map((k, n) => <ellipse key={n} cx={cx} cy={cy} rx={rx * k} ry={ry * k} className="pt-faint" fill="none" />)}
      </g>) },
  ];

  const axis = () => {
    const a = off(-0.4), b = off(6.2);
    return (
      <g className="ex-axis" style={{ opacity: exploded ? 1 : 0 }}>
        <line x1={cx + a[0]} y1={cy + a[1]} x2={cx + b[0]} y2={cy + b[1]} className="ex-axis-line" />
        <text x={cx + b[0] + 6} y={cy + b[1] - 6} className="ex-axis-tag">BACK</text>
        <text x={cx + a[0] - 6} y={cy + a[1] + 18} className="ex-axis-tag" textAnchor="end">FRONT</text>
      </g>
    );
  };

  // base (separate, below)
  const bOff = exploded ? [10, 250] : [16, 150];

  return (
    <div>
      <div className="sheet-tools">
        <span className="sheet-tools-l">ASSEMBLY STACK · FRONT → BACK · 6 LAYERS + BASE</span>
        <button className={"toggle" + (exploded ? " on" : "")} onClick={() => setExploded((v) => !v)}>
          <span className="toggle-box" />{exploded ? "COLLAPSE" : "EXPLODE"}
        </button>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="dwg-svg" preserveAspectRatio="xMidYMid meet">
        <DwgDefs />
        <SheetBacking w={W} h={H} />
        {axis()}

        {/* base */}
        <g style={{ transform: `translate(${bOff[0]}px,${bOff[1]}px)`, transition: "transform .6s cubic-bezier(.4,0,.2,1)" }}>
          <g className={"ex-layer" + (hov === "base" ? " on" : "")} onMouseEnter={() => setHov("base")} onMouseLeave={() => setHov(null)}>
            <path d={`M${cx - 132},${cy} A132,46 0 0 0 ${cx + 132},${cy} L${cx + 132},${cy + 38} A132,46 0 0 1 ${cx - 132},${cy + 38} Z`} className="ex-shell" />
            <ellipse cx={cx} cy={cy} rx="132" ry="46" className="iso-top" />
            <ellipse cx={cx} cy={cy} rx="132" ry="46" className="pt-line" fill="none" />
            <ellipse cx={cx} cy={cy - 2} rx="86" ry="28" className="iso-well" />
            {exploded && <Note id="base" x={cx + 120} y={cy + 20} tx={748} ty={cy + 10} side="R" name="Weighted base" sub="USB-C 5 V · pogo · tilt" hovered={hov} onHover={setHov} />}
          </g>
        </g>

        {/* stacked layers */}
        {layers.map((L) => {
          const o = off(L.i);
          const tx = L.side === "L" ? 168 : W - 168;
          const ty = cy + o[1];
          return (
            <g key={L.id} style={{ transform: `translate(${o[0]}px,${o[1]}px)`, transition: "transform .6s cubic-bezier(.4,0,.2,1)" }}>
              <g className={"ex-layer" + (hov === L.id ? " on" : "")} onMouseEnter={() => setHov(L.id)} onMouseLeave={() => setHov(null)}>
                {L.draw()}
              </g>
            </g>
          );
        })}
        {/* labels (outside transformed groups so leaders reach true exploded pos) */}
        {exploded && layers.map((L) => {
          const o = off(L.i);
          const tx = L.side === "L" ? 188 : 748;
          return (
            <Note key={L.id} id={L.id} x={cx + o[0] + (L.side === "L" ? -rx + 14 : rx - 14)} y={cy + o[1]}
              tx={tx} ty={cy + o[1]} side={L.side} name={L.name} sub={L.sub} tag={L.tag}
              hovered={hov} onHover={setHov} />
          );
        })}

        <ScaleBar x={40} y={H - 42} />
        <TitleBlock w={W} h={H} no="EX-04" title="EXPLODED ASSEMBLY" scale="ILLUSTRATIVE" sht="SHT 4/6" />
      </svg>
    </div>
  );
}
window.SheetExplode = SheetExplode;
