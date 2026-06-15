/* GRAVITY cross-section — schematic side section, front face LEFT.
   Renders a persistent device/base envelope frame, then the active layer's
   detailed geometry solid + scientific-diagram leader labels. Passed layers ghost. */
const { useMemo: _useMemo } = React;

function csWrap(str, n) {
  if (!str) return [];
  const words = str.split(" ");
  const lines = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).trim().length > n) { if (cur) lines.push(cur); cur = w; }
    else cur = (cur ? cur + " " : "") + w;
  }
  if (cur) lines.push(cur);
  return lines;
}

// running 1-based number for a component (idx within layer li)
function csNum(layers, li, i) {
  let n = 0;
  for (let k = 0; k < li; k++) n += layers[k].components.length;
  return n + i + 1;
}

function CrossSection({ activeLayer, fullSection, hovered, onHover }) {
  const G = window.GEO;
  const layers = window.GRAVITY_LAYERS;

  // device envelope path (front flat left, convex back right)
  const devPath =
    "M462,200 L462,648 Q462,686 500,686 L656,686 Q726,686 740,568 " +
    "C757,488 757,360 740,280 Q726,162 656,162 L500,162 Q462,162 462,200 Z";
  const basePath =
    "M486,716 Q470,716 473,744 L480,812 Q482,834 508,834 L676,834 " +
    "Q704,834 706,808 L711,744 Q713,716 696,716 Z";

  const cutX = [462, 476, 516, 547, null]; // section plane per layer

  // ---- geometry per layer (solid detail) -------------------------------
  function layerGeo(li) {
    switch (li) {
      case 0:
        return (
          <g>
            <path d={devPath} className="cs-fill-shell" />
            <path d={basePath} className="cs-fill-shell" />
            {/* display face indication */}
            <path d="M468,206 L468,642" className="cs-screen" />
            <path d="M472,210 L472,638" className="cs-screen-2" />
            {/* convex back hint */}
            <path d="M724,300 C736,360 736,470 724,548" className="cs-hint" />
            {/* soft-touch back grain ticks */}
            {[330, 380, 430, 480].map((y) => (
              <path key={y} d={`M712,${y} q14,${y < 424 ? 6 : -6} 22,0`} className="cs-hint" />
            ))}
          </g>
        );
      case 1:
        return (
          <g>
            <rect x="462" y="200" width="14" height="448" rx="7" className="cs-fill hatch-a" />
            <rect x="478" y="204" width="18" height="440" rx="4" className="cs-fill cs-paper" />
            {/* FPC fold ribbons */}
            <path d="M487,206 C512,196 540,196 540,210" className="cs-fpc" />
            <path d="M487,642 C512,652 540,652 540,636" className="cs-fpc" />
            {/* ALS light-pipe */}
            <rect x="463" y="580" width="12" height="18" rx="2" className="cs-fill cs-accent-fill" />
            {/* lamination ticks */}
            {[260, 340, 420, 500].map((y) => (
              <line key={y} x1="478" y1={y} x2="496" y2={y} className="cs-tick" />
            ))}
          </g>
        );
      case 2:
        return (
          <g>
            {/* PCB plane */}
            <rect x="540" y="196" width="7" height="456" rx="2" className="cs-fill-pcb" />
            {/* ESP32 module (tall, at board edge / top) */}
            <rect x="516" y="200" width="24" height="62" rx="2" className="cs-fill cs-module" />
            <rect x="519" y="204" width="18" height="10" rx="1" className="cs-hint-fill" />
            {/* antenna keep-out hint */}
            <path d="M516,206 h-12 v50 h12" className="cs-keepout" />
            {/* small ICs */}
            {[[516, 276, 24, 18], [516, 336, 24, 16], [516, 396, 24, 16], [516, 456, 24, 18], [516, 520, 24, 18]].map((r, i) => (
              <rect key={i} x={r[0]} y={r[1]} width={r[2]} height={r[3]} rx="1.5" className="cs-fill cs-ic" />
            ))}
            {/* prog header pads */}
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <rect key={i} x={528 + i * 2.6} y="236" width="1.6" height="6" className="cs-pad" />
            ))}
            {/* speaker */}
            <rect x="512" y="586" width="30" height="58" rx="3" className="cs-fill cs-spk" />
            <circle cx="527" cy="615" r="16" className="cs-spk-cone" />
            <circle cx="527" cy="615" r="6" className="cs-spk-cone" />
            {/* connectors at board edge */}
            <rect x="540" y="650" width="14" height="10" rx="1" className="cs-fill cs-ic" />
          </g>
        );
      case 3:
        return (
          <g>
            {/* battery */}
            <rect x="553" y="252" width="98" height="312" rx="6" className="cs-fill cs-batt" />
            <text x="602" y="414" className="cs-batt-label" textAnchor="middle">LiPo</text>
            <text x="602" y="432" className="cs-batt-sub" textAnchor="middle">1500 mAh</text>
            {/* power ICs on board lower */}
            {[[516, 482, 24, 18], [516, 546, 24, 20]].map((r, i) => (
              <rect key={i} x={r[0]} y={r[1]} width={r[2]} height={r[3]} rx="1.5" className="cs-fill cs-ic" />
            ))}
            {/* buck inductor */}
            <rect x="522" y="572" width="12" height="10" rx="2" className="cs-fill cs-module" />
            {/* pogo contacts on board back, pointing down to base */}
            <path d="M548,664 v22 M564,664 v22" className="cs-pogo" />
            <circle cx="548" cy="688" r="3" className="cs-anchor-dot-s" />
            <circle cx="564" cy="688" r="3" className="cs-anchor-dot-s" />
          </g>
        );
      case 4:
        return (
          <g>
            <path d={basePath} className="cs-fill-base" />
            {/* pogo receptacles (top) */}
            <path d="M548,716 v-8 M564,716 v-8" className="cs-pogo" />
            <rect x="543" y="716" width="26" height="8" rx="2" className="cs-fill cs-ic" />
            {/* base PCB */}
            <rect x="500" y="742" width="176" height="6" rx="1" className="cs-fill-pcb" />
            {/* USB-C receptacle (right edge) */}
            <rect x="672" y="752" width="40" height="22" rx="3" className="cs-fill cs-module" />
            <rect x="700" y="757" width="14" height="12" rx="2" className="cs-hint-fill" />
            {/* TVS + PTC */}
            <rect x="612" y="758" width="20" height="14" rx="1.5" className="cs-fill cs-ic" />
            {/* magnets */}
            <rect x="488" y="726" width="14" height="22" rx="2" className="cs-fill cs-mag" />
            {/* weighted floor */}
            <rect x="485" y="812" width="206" height="20" rx="3" className="cs-fill hatch-a" />
            {[505, 545, 585, 625, 665].map((x) => (
              <line key={x} x1={x} y1="814" x2={x} y2="830" className="cs-tick" />
            ))}
          </g>
        );
      default:
        return null;
    }
  }

  // ghost outline for passed layers (simplified)
  function ghostGeo(li) {
    switch (li) {
      case 0: return <g><path d={devPath} className="cs-ghost-line" /><path d={basePath} className="cs-ghost-line" /></g>;
      case 1: return <rect x="462" y="200" width="34" height="448" rx="6" className="cs-ghost-line" />;
      case 2: return <g><rect x="516" y="196" width="31" height="456" rx="2" className="cs-ghost-line" /><rect x="512" y="586" width="30" height="58" rx="3" className="cs-ghost-line" /></g>;
      case 3: return <rect x="553" y="252" width="98" height="312" rx="6" className="cs-ghost-line" />;
      case 4: return <path d={basePath} className="cs-ghost-line" />;
      default: return null;
    }
  }

  // ---- leader labels for the active layer ------------------------------
  const labels = _useMemo(() => {
    if (fullSection) return [];
    const comps = layers[activeLayer].components.map((c, i) => ({ ...c, i }));
    const out = [];
    ["L", "R"].forEach((side) => {
      const items = comps.filter((c) => c.side === side).sort((a, b) => a.anchor[1] - b.anchor[1]);
      const n = items.length;
      const top = G.label.topY, bot = G.label.botY;
      items.forEach((c, k) => {
        const slotY = n === 1 ? (top + bot) / 2 : top + ((bot - top) * (k + 0.5)) / n;
        out.push({ ...c, side, slotY });
      });
    });
    return out;
  }, [activeLayer, fullSection]);

  const Lx = G.label.leftX, Rx = G.label.rightX;

  return (
    <svg viewBox={`0 0 ${G.vb.w} ${G.vb.h}`} className="cs-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <pattern id="hatchA" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
          <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(215,210,196,0.30)" strokeWidth="0.8" />
        </pattern>
        <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
          <path d="M32 0 L0 0 0 32" fill="none" stroke="rgba(255,255,255,0.035)" strokeWidth="1" />
        </pattern>
      </defs>

      {/* grid + registration */}
      <rect x="0" y="0" width={G.vb.w} height={G.vb.h} fill="url(#grid)" />
      {[[20, 20], [G.vb.w - 20, 20], [20, G.vb.h - 20], [G.vb.w - 20, G.vb.h - 20]].map((p, i) => (
        <g key={i} className="cs-reg">
          <line x1={p[0] - 9} y1={p[1]} x2={p[0] + 9} y2={p[1]} />
          <line x1={p[0]} y1={p[1] - 9} x2={p[0]} y2={p[1] + 9} />
        </g>
      ))}

      {/* persistent faint envelope */}
      <path d={devPath} className="cs-frame" />
      <path d={basePath} className="cs-frame" />
      {/* centre axis */}
      <line x1="462" y1="424" x2="756" y2="424" className="cs-axis" />

      {/* layers */}
      {layers.map((_, li) => {
        if (fullSection) return <g key={li} className="cs-layer-solid">{layerGeo(li)}</g>;
        if (li < activeLayer) return <g key={li} className="cs-layer-ghost">{ghostGeo(li)}</g>;
        if (li === activeLayer) return <g key={li} className="cs-layer-active">{layerGeo(li)}</g>;
        return null;
      })}

      {/* section plane */}
      {!fullSection && cutX[activeLayer] != null && (
        <g className="cs-plane">
          <line x1={cutX[activeLayer]} y1="120" x2={cutX[activeLayer]} y2="704" />
          <path d={`M${cutX[activeLayer] - 6},120 L${cutX[activeLayer] + 6},120 L${cutX[activeLayer]},132 Z`} className="cs-plane-tri" />
          <text x={cutX[activeLayer] + 10} y="128" className="cs-plane-tag">
            SECTION PLANE · {layers[activeLayer].depthMm} mm
          </text>
        </g>
      )}
      {!fullSection && activeLayer === 4 && (
        <text x="724" y="700" className="cs-plane-tag" textAnchor="end">⟂ LIFT-OUT INTERFACE</text>
      )}

      {/* full-section numbered markers */}
      {fullSection && layers.map((L, li) =>
        L.components.map((c, i) => {
          const num = csNum(layers, li, i);
          const hov = hovered === `${li}-${i}`;
          return (
            <g key={`${li}-${i}`} className={"cs-marker" + (hov ? " on" : "")}
               onMouseEnter={() => onHover && onHover(`${li}-${i}`)}
               onMouseLeave={() => onHover && onHover(null)}>
              <circle cx={c.anchor[0]} cy={c.anchor[1]} r="9" className="cs-marker-bg" />
              <text x={c.anchor[0]} y={c.anchor[1] + 3.5} className="cs-marker-num" textAnchor="middle">{num}</text>
            </g>
          );
        })
      )}

      {/* leader labels */}
      {labels.map((c) => {
        const ax = c.anchor[0], ay = c.anchor[1];
        const isL = c.side === "L";
        const textX = isL ? Lx : Rx;
        const kneeX = isL ? Lx + 70 : Rx - 70;
        const stubX = isL ? Lx + 8 : Rx - 8;
        const fnLines = csWrap(c.fn, 40);
        const hov = hovered === `${activeLayer}-${c.i}`;
        return (
          <g key={c.i} className={"cs-label" + (hov ? " on" : "")}
             onMouseEnter={() => onHover && onHover(`${activeLayer}-${c.i}`)}
             onMouseLeave={() => onHover && onHover(null)}>
            <polyline points={`${ax},${ay} ${kneeX},${c.slotY} ${stubX},${c.slotY}`} className="cs-leader" />
            <circle cx={ax} cy={ay} r="3.2" className="cs-anchor-dot" />
            <text x={textX} y={c.slotY - 6} className="cs-lname" textAnchor={isL ? "end" : "start"}>
              {c.name}{c.tag ? "  " : ""}
              {c.tag && <tspan className="cs-tag">[{c.tag}]</tspan>}
            </text>
            {c.mpn && (
              <text x={textX} y={c.slotY + 8} className="cs-lmpn" textAnchor={isL ? "end" : "start"}>{c.mpn}</text>
            )}
            {fnLines.map((ln, k) => (
              <text key={k} x={textX} y={c.slotY + (c.mpn ? 22 : 9) + k * 11} className="cs-lfn" textAnchor={isL ? "end" : "start"}>{ln}</text>
            ))}
            {c.bus && (
              <text x={textX} y={c.slotY + (c.mpn ? 22 : 9) + fnLines.length * 11} className="cs-lbus" textAnchor={isL ? "end" : "start"}>{c.bus}</text>
            )}
          </g>
        );
      })}

      {/* title block */}
      <g className="cs-title">
        <rect x={G.vb.w - 268} y={G.vb.h - 96} width="248" height="76" rx="2" className="cs-title-box" />
        <text x={G.vb.w - 256} y={G.vb.h - 74} className="cs-title-h">GRAVITY · V1 DEMO UNIT</text>
        <text x={G.vb.w - 256} y={G.vb.h - 58} className="cs-title-s">SECTION A–A · FRONT FACE LEFT</text>
        <text x={G.vb.w - 256} y={G.vb.h - 42} className="cs-title-s">SCHEMATIC · NOT TO SCALE</text>
        <text x={G.vb.w - 28} y={G.vb.h - 42} className="cs-title-s" textAnchor="end">SHT 1/1</text>
      </g>
    </svg>
  );
}
window.CrossSection = CrossSection;
window.csNum = csNum;
