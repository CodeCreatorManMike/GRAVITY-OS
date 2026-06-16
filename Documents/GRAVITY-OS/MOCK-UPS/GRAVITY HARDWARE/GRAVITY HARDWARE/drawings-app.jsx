/* GRAVITY drawing set — page shell binding the five sheets. */
const { useState: _useStateApp } = React;
const { SheetGA, SheetOrtho, SheetIso, SheetExplode, SheetAssembly, SheetBackstand } = window;

function Sheet({ code, title, tag, children }) {
  return (
    <section className="sheet">
      <div className="sheet-bar">
        <div className="sheet-bar-l">
          <span className="sheet-code">{code}</span>
          <span className="sheet-title">{title}</span>
        </div>
        <span className="sheet-tag">{tag}</span>
      </div>
      <div className="sheet-body">{children}</div>
    </section>
  );
}

function DrawingsApp() {
  const sheets = [
    ["GA-01", "GENERAL ARRANGEMENT", "DIMENSIONED · Ø & DEPTH"],
    ["OR-02", "ORTHOGRAPHIC ELEVATIONS", "THIRD ANGLE · 4 VIEW"],
    ["IS-03", "ISOMETRIC — 3/4 VIEW", "ILLUSTRATIVE"],
    ["EX-04", "EXPLODED ASSEMBLY", "INTERACTIVE · 6 LAYERS"],
    ["AS-05", "BASE — SEATING DETAIL", "SECTION + DETAIL B"],
    ["ST-06", "FLIP-OUT BACKSTAND", "FREE-STAND · HINGE 4:1"],
  ];
  return (
    <div className="page">
      <header className="masthead">
        <div className="mh-top">
          <div className="mh-mark"><span className="mh-badge">◐</span>GRAVITY</div>
          <div className="mh-rev">REV V1 · DRAWING SET · 2026</div>
        </div>
        <div className="mh-line" />
        <div className="mh-sub">ENGINEERING DRAWING SET — FORM, DIMENSIONS, ORTHOGRAPHIC & EXPLODED VIEWS</div>
        <div className="chips">
          {window.SPEC_META.map((m) => (
            <div className="chip" key={m.k}><span className="chip-k">{m.k}</span><span className="chip-v">{m.v}</span></div>
          ))}
        </div>
        <div className="dwg-index">
          {sheets.map((s) => (
            <a className="dwg-index-row" href={`#${s[0]}`} key={s[0]}>
              <span className="dwg-index-no">{s[0]}</span>
              <span className="dwg-index-t">{s[1]}</span>
              <span className="dwg-index-g">{s[2]}</span>
            </a>
          ))}
          <a className="dwg-index-row dwg-index-back" href="Gravity Hardware Breakdown.html">
            <span className="dwg-index-no">↩</span>
            <span className="dwg-index-t">HARDWARE BREAKDOWN</span>
            <span className="dwg-index-g">CROSS-SECTION · BOM</span>
          </a>
        </div>
      </header>

      <a id="GA-01" /><Sheet code="GA-01" title="General Arrangement" tag="DIMENSIONED"><SheetGA /></Sheet>
      <a id="OR-02" /><Sheet code="OR-02" title="Orthographic Elevations" tag="THIRD ANGLE · FRONT / TOP / RIGHT / REAR"><SheetOrtho /></Sheet>
      <a id="IS-03" /><Sheet code="IS-03" title="Isometric — 3/4 View" tag="ILLUSTRATIVE"><SheetIso /></Sheet>
      <a id="EX-04" /><Sheet code="EX-04" title="Exploded Assembly" tag="INTERACTIVE"><SheetExplode /></Sheet>
      <a id="AS-05" /><Sheet code="AS-05" title="Base — Seating Detail" tag="SECTION + DETAIL B"><SheetAssembly /></Sheet>
      <a id="ST-06" /><Sheet code="ST-06" title="Flip-out Backstand" tag="FREE-STAND · STOWED · HINGE 4:1"><SheetBackstand /></Sheet>

      <footer className="footer">
        <div className="mh-line" />
        <div className="footer-row">
          <span>GRAVITY · V1 DEMO UNIT · DRAWN ≈1:1 · DIMS IN mm · NOT TO SCALE</span>
          <span>SHEETS 1–6 · COMPANION TO HARDWARE BREAKDOWN</span>
        </div>
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<DrawingsApp />);
