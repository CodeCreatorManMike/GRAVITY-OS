/* GRAVITY hardware breakdown — page shell + interactive section */
const { useState, useRef, useCallback, useEffect } = React;
const { CrossSection, HeroObject, EinkFace, csNum } = window;

function Badge({ children }) {
  return <span className="badge">{children}</span>;
}

function SecHead({ code, title, tag, children }) {
  return (
    <div className="sec-head">
      <div className="sec-head-row">
        <Badge>{code}</Badge>
        <h2 className="sec-title">{title}</h2>
        <span className="sec-tag">{tag}</span>
      </div>
      {children && <p className="sec-blurb">{children}</p>}
    </div>
  );
}

/* ---- THE OBJECT ---- */
function ObjectSection() {
  const callouts = [
    ["FORM", "Circular puck · slightly larger than a HomePod Mini. It faces the user — not a sphere."],
    ["FINISH", "Matte-black ABS / PETG, soft-touch coat. Convex back fits a cupped palm."],
    ["BACK", "Completely clean — no buttons, no ports, no visible electronics."],
    ["BASE", "Seats into a weighted base at a 15–25° tilt. Lifts out for handheld use; UI rotates to match."],
  ];
  return (
    <section className="section">
      <SecHead code="O" title="The Object" tag="CONCEPT · WHAT THE CUSTOMER SEES">
        A circular black-and-white e-ink object that sits on a desk or bedside table. Silent by default,
        glanceable in under a second. All AI runs in the cloud — the device is a calm display terminal.
      </SecHead>

      <div className="object-grid">
        <div className="hero-card">
          <div className="card-corner tl">GRAVITY</div>
          <div className="card-corner tr">FRONT · SEATED</div>
          <HeroObject />
          <div className="card-corner bl">MATTE BLACK · V1</div>
          <div className="card-corner br">Ø 110–120 mm</div>
        </div>

        <div className="object-side">
          <div className="spec-list">
            {callouts.map(([k, v]) => (
              <div className="spec-item" key={k}>
                <div className="spec-k">{k}</div>
                <div className="spec-v">{v}</div>
              </div>
            ))}
          </div>
          <div className="glance-note">
            <div className="glance-face"><EinkFace size={188} /></div>
            <div className="glance-text">
              <div className="glance-h">THE GLANCE</div>
              <p>Pure black/white e-ink in <b>Space Mono</b>. One dominant thing in the centre, supporting
                data in the mid-ring, ambient status on the perimeter. No animation, no colour, no icons —
                terminal restraint. A silent screen after a good day is the product working.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---- THE SECTION (interactive) ---- */
function DepthSlider({ activeLayer, setLayer, disabled }) {
  const layers = window.GRAVITY_LAYERS;
  const trackRef = useRef(null);
  const dragging = useRef(false);

  const setFromX = useCallback((clientX) => {
    const el = trackRef.current; if (!el) return;
    const r = el.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (clientX - r.left) / r.width));
    setLayer(Math.round(frac * (layers.length - 1)));
  }, [setLayer, layers.length]);

  useEffect(() => {
    const move = (e) => { if (dragging.current) setFromX(e.clientX); };
    const up = () => { dragging.current = false; };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
  }, [setFromX]);

  const pct = (activeLayer / (layers.length - 1)) * 100;

  return (
    <div className={"slider" + (disabled ? " is-disabled" : "")}>
      <div className="slider-label">
        <span>SECTION DEPTH</span>
        <span className="slider-hint">DRAG TO SLICE →</span>
      </div>
      <div className="slider-track" ref={trackRef}
        onPointerDown={(e) => { if (disabled) return; dragging.current = true; setFromX(e.clientX); }}>
        <div className="slider-fill" style={{ width: pct + "%" }} />
        {layers.map((L, i) => (
          <button key={i} className={"stop" + (i === activeLayer ? " on" : "") + (i < activeLayer ? " passed" : "")}
            style={{ left: (i / (layers.length - 1)) * 100 + "%" }}
            onClick={(e) => { e.stopPropagation(); if (!disabled) setLayer(i); }}>
            <span className="stop-dot" />
            <span className="stop-code">{L.code}</span>
          </button>
        ))}
        <div className="thumb" style={{ left: pct + "%" }} />
      </div>
    </div>
  );
}

function Manifest({ activeLayer, fullSection, hovered, setHovered }) {
  const layers = window.GRAVITY_LAYERS;

  const renderRow = (c, li, i) => {
    const num = csNum(layers, li, i);
    const key = `${li}-${i}`;
    return (
      <div key={key} className={"mf-row" + (hovered === key ? " on" : "")}
        onMouseEnter={() => setHovered(key)} onMouseLeave={() => setHovered(null)}>
        <div className="mf-num">{String(num).padStart(2, "0")}</div>
        <div className="mf-body">
          <div className="mf-name">{c.name}{c.tag && <span className="mf-tag">{c.tag}</span>}</div>
          {c.mpn && <div className="mf-mpn">{c.mpn}</div>}
          <div className="mf-fn">{c.fn}</div>
        </div>
        {c.bus && <div className="mf-bus">{c.bus}</div>}
      </div>
    );
  };

  if (fullSection) {
    return (
      <div className="manifest">
        <div className="mf-head">
          <div className="mf-head-code">ALL</div>
          <div className="mf-head-title">FULL BILL OF MATERIALS</div>
        </div>
        <div className="mf-blurb">Every annotated component across all five layers. Hover a row to locate it on the section.</div>
        <div className="mf-scroll">
          {layers.map((L, li) => (
            <div key={li} className="mf-group">
              <div className="mf-group-h"><span>{L.code}</span> {L.title}</div>
              {L.components.map((c, i) => renderRow(c, li, i))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  const L = layers[activeLayer];
  return (
    <div className="manifest">
      <div className="mf-head">
        <div className="mf-head-code">{L.code}</div>
        <div className="mf-head-title">{L.title}</div>
      </div>
      <div className="mf-blurb">{L.blurb}</div>
      <div className="mf-count">{L.components.length} COMPONENTS</div>
      <div className="mf-scroll">
        {L.components.map((c, i) => renderRow(c, activeLayer, i))}
      </div>
    </div>
  );
}

function SectionStage() {
  const layers = window.GRAVITY_LAYERS;
  const [activeLayer, setActiveLayer] = useState(0);
  const [fullSection, setFullSection] = useState(false);
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    const onKey = (e) => {
      if (fullSection) return;
      if (e.key === "ArrowRight") setActiveLayer((l) => Math.min(layers.length - 1, l + 1));
      if (e.key === "ArrowLeft") setActiveLayer((l) => Math.max(0, l - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullSection, layers.length]);

  return (
    <section className="section">
      <SecHead code="S" title="The Section" tag="INTERACTIVE · A–A">
        The unit cut in half, front face pointing left. Drag the depth slider to slice through the device
        layer by layer — each layer lights up with its components, part numbers and buses. Or open the full
        annotated section.
      </SecHead>

      <div className="stage-grid">
        <div className="drawing-card">
          <div className="dc-bar">
            <span className="dc-bar-l">SECTION A–A · {fullSection ? "FULL ANNOTATED" : `LAYER ${layers[activeLayer].code} · ${layers[activeLayer].title}`}</span>
            <button className={"toggle" + (fullSection ? " on" : "")} onClick={() => setFullSection((v) => !v)}>
              <span className="toggle-box" />{fullSection ? "EXIT FULL SECTION" : "SHOW FULL SECTION"}
            </button>
          </div>
          <div className="dc-stage">
            <CrossSection activeLayer={activeLayer} fullSection={fullSection} hovered={hovered} onHover={setHovered} />
          </div>
          <div className="dc-controls">
            <button className="nav-btn" disabled={fullSection || activeLayer === 0}
              onClick={() => setActiveLayer((l) => Math.max(0, l - 1))}>← PREV</button>
            <DepthSlider activeLayer={activeLayer} setLayer={setActiveLayer} disabled={fullSection} />
            <button className="nav-btn" disabled={fullSection || activeLayer === layers.length - 1}
              onClick={() => setActiveLayer((l) => Math.min(layers.length - 1, l + 1))}>NEXT →</button>
          </div>
        </div>

        <Manifest activeLayer={activeLayer} fullSection={fullSection} hovered={hovered} setHovered={setHovered} />
      </div>
    </section>
  );
}

function App() {
  return (
    <div className="page">
      <header className="masthead">
        <div className="mh-top">
          <div className="mh-mark"><span className="mh-badge">◐</span>GRAVITY</div>
          <div className="mh-rev">REV V1 · DEMO UNIT · 2026</div>
        </div>
        <div className="mh-line" />
        <div className="mh-sub">HARDWARE BREAKDOWN — INDUSTRIAL DESIGN, EVERY INTERNAL COMPONENT, FRONT TO BACK</div>
        <div className="chips">
          {window.SPEC_META.map((m) => (
            <div className="chip" key={m.k}><span className="chip-k">{m.k}</span><span className="chip-v">{m.v}</span></div>
          ))}
        </div>
      </header>

      <ObjectSection />
      <SectionStage />

      <footer className="footer">
        <div className="mh-line" />
        <div className="footer-row">
          <span>GRAVITY · ESP32-S3-WROOM-1-N16R8 · 2-LAYER PCB · KiCad 8</span>
          <span>SECTION SCHEMATIC · NOT TO SCALE · BUILD AT STAGE 4</span>
        </div>
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
