/* ============================================================
   GRAVITY — Disc Helpers + Mirror Faces  (for the companion app)
   A self-contained, render-safe subset of the device grammar so
   the iOS app can show the actual e-ink paper disc — "what's on
   your Gravity right now" — without the device gallery auto-
   injecting itself. 1-bit: ink on paper, line / arc / dot only.
   ============================================================ */
const C = 180, INK = '#14130d', PAPER = '#f4f2ea', RAD = Math.PI / 180;

const P = (r, d) => [C + r * Math.sin(d * RAD), C - r * Math.cos(d * RAD)];
const f = n => (+n).toFixed(2);
function arc(r, a, b, sw = 1) {
  const [x1, y1] = P(r, a), [x2, y2] = P(r, b);
  const large = Math.abs(b - a) > 180 ? 1 : 0;
  return `M${f(x1)} ${f(y1)} A${r} ${r} 0 ${large} ${sw} ${f(x2)} ${f(y2)}`;
}
function ring(r, sw = 1, dash = null) {
  return `<circle cx="${C}" cy="${C}" r="${r}" fill="none" stroke="${INK}" stroke-width="${sw}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
}
function T(x, y, str, o = {}) {
  const { s = 12, w = 400, a = 'middle', ls = 0, fam = 'inherit', fill = INK, bl = 'alphabetic', op = 1, style = '' } = o;
  return `<text x="${f(x)}" y="${f(y)}" font-size="${s}" font-weight="${w}" text-anchor="${a}" letter-spacing="${ls}" font-family="${fam}" fill="${fill}" dominant-baseline="${bl}" opacity="${op}" style="${style}">${str}</text>`;
}
function dot(x, y, r, filled = true, sw = 1.1) {
  return filled
    ? `<circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="${INK}"/>`
    : `<circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
}
function moon(cx, cy, R, sw = 1.5) {
  const top = `${f(cx)} ${f(cy - R)}`, bot = `${f(cx)} ${f(cy + R)}`;
  return `<path d="M ${top} A ${R} ${R} 0 0 0 ${bot} A ${f(R * 1.65)} ${f(R * 1.65)} 0 0 1 ${top}" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
}
function star(x, y, r = 2.4) {
  return `<path d="M${f(x)} ${f(y - r)} L${f(x)} ${f(y + r)} M${f(x - r)} ${f(y)} L${f(x + r)} ${f(y)}" stroke="${INK}" stroke-width="1"/>`;
}
function check(cx, cy, k = 2.6, sw = 1.4) {
  return `<path d="M${f(cx - k)} ${f(cy)} l${f(k * 0.75)} ${f(k * 0.85)} l${f(k * 1.35)} -${f(k * 1.6)}" fill="none" stroke="${INK}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round"/>`;
}
function progArc(r, pct, sw = 5) {
  const end = 360 * pct, [ex, ey] = P(r, end);
  return `<path d="${arc(r, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`
    + `<path d="${arc(r, 0, end)}" fill="none" stroke="${INK}" stroke-width="${sw}" stroke-linecap="round"/>`
    + `<circle cx="${f(ex)}" cy="${f(ey)}" r="4.2" fill="${PAPER}" stroke="${INK}" stroke-width="2"/>`;
}

/* curved rim text — auto-unique ids so faces can repeat safely */
let _cid = 0;
function curve(id, r, a, b, sw = 0) { return `<path id="${id}" d="${arc(r, a, b, sw)}" fill="none"/>`; }
function onPath(id, str, o = {}) {
  const { s = 10, w = 500, ls = 3, fill = INK, off = '50%', fam = 'inherit' } = o;
  return `<text font-size="${s}" font-weight="${w}" letter-spacing="${ls}" fill="${fill}" font-family="${fam}"><textPath href="#${id}" startOffset="${off}" text-anchor="middle">${str}</textPath></text>`;
}
function topLabel(_id, str, o = {}, r = 159, span = 52) { const id = 'tl' + (_cid++); return curve(id, r, 360 - span, span, 1) + onPath(id, str, o); }
function botLabel(_id, str, o = {}, r = 152, span = 52) { const id = 'bl' + (_cid++); return curve(id, r, 180 + span, 180 - span, 0) + onPath(id, str, o); }

const GEO = "'Space Grotesk', sans-serif";
const MONO = "'JetBrains Mono', monospace";
const SORA = "'Sora', sans-serif";

const frame = (font, inner) =>
  `<svg viewBox="0 0 360 360" font-family="${font}" shape-rendering="geometricPrecision" text-rendering="geometricPrecision">
     <rect width="360" height="360" fill="${PAPER}"/>${inner}</svg>`;

/* ---- mirror faces (what the device is showing) ------------ */
function faceIdle() {
  let s = ring(176, 1) + ring(150, 0.8) + ring(118, 0.7, '1 5');
  [0, 90, 180, 270].forEach(d => { const [x1, y1] = P(176, d), [x2, y2] = P(168, d); s += `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${INK}" stroke-width="1.4"/>`; });
  const deg = (9 + 14 / 60) / 24 * 360;
  s += `<path d="${arc(150, 0, deg)}" fill="none" stroke="${INK}" stroke-width="2.2"/>`;
  s += `<path d="${arc(150, deg, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 5"/>`;
  const [px, py] = P(150, deg);
  s += `<circle cx="${f(px)}" cy="${f(py)}" r="4.5" fill="${INK}"/>`;
  s += T(C, 178, '9:14', { s: 58, w: 300, fam: GEO, ls: -1 });
  s += T(C, 208, 'Friday 12 June', { s: 13, w: 400, fam: GEO, ls: 2 });
  s += botLabel(0, '47 DAY STREAK', { s: 9.5, ls: 4, fam: GEO }, 134, 46);
  s += topLabel(0, 'GRAVITY', { s: 9, ls: 8, fam: GEO }, 162, 30);
  return frame(GEO, s);
}
function faceGoal() {
  const rings = [[150, 0.62], [124, 0.70], [98, 0.71]];
  let s = '';
  rings.forEach(([r, p]) => {
    const end = 360 * p;
    s += `<path d="${arc(r, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="0.9" stroke-dasharray="1.5 4"/>`;
    s += `<path d="${arc(r, 0, end)}" fill="none" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`;
    const [ex, ey] = P(r, end);
    s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="3.6" fill="${PAPER}" stroke="${INK}" stroke-width="1.6"/>`;
  });
  s += T(C, 174, '62%', { s: 42, w: 500, fam: GEO, ls: -1 });
  s += T(C, 198, 'HALF MARATHON', { s: 10, w: 600, ls: 3, fam: GEO });
  s += T(C, 214, '94 days left', { s: 10, w: 400, ls: 1, fam: GEO });
  return frame(GEO, s);
}
function faceTodo() {
  let s = progArc(158, 0.4, 4);
  s += topLabel(0, 'TODAY &#183; 5 TASKS', { s: 8.5, w: 600, ls: 3, fam: GEO });
  const items = [['Standup notes', 1], ['Reply to Sam', 1], ['Q3 roadmap deck', 0], ['Gym at 18:00', 0], ['Book flights', 0]];
  const cx = C - 70;
  items.forEach(([t, done], i) => {
    const y = 128 + i * 23;
    s += `<circle cx="${cx}" cy="${y - 3.5}" r="5" fill="none" stroke="${INK}" stroke-width="1.2"/>`;
    if (done) s += check(cx, y - 3.5, 2.6, 1.3);
    s += T(cx + 14, y, t, { s: 11.5, w: done ? 400 : 500, ls: .2, fam: GEO, a: 'start', op: done ? .55 : 1, style: done ? 'text-decoration:line-through' : '' });
  });
  s += botLabel(0, '2 OF 5 DONE', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}
function faceFocus() {
  const fracRem = (24 + 18 / 60) / 90, end = 360 * fracRem;
  let s = ring(176, 1, '1 5') + ring(150, 0.8);
  s += `<path d="${arc(150, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 5"/>`;
  s += `<path d="${arc(150, 0, end)}" fill="none" stroke="${INK}" stroke-width="3.2" stroke-linecap="round"/>`;
  const [px, py] = P(150, end);
  s += `<circle cx="${f(px)}" cy="${f(py)}" r="4.5" fill="${INK}"/>`;
  s += T(C, 184, '24:18', { s: 46, w: 300, fam: GEO, ls: -1 });
  s += T(C, 210, 'remaining', { s: 11, w: 400, ls: 3, fam: GEO });
  s += topLabel(0, 'DEEP WORK', { s: 9, ls: 6, fam: GEO });
  s += botLabel(0, 'SESSION 02 &#183; Q3 DECK', { s: 8.5, ls: 2.5, fam: GEO });
  return frame(GEO, s);
}
function faceSleep() {
  let s = ring(176, 1, '1 5') + ring(150, 0.8, '1 4');
  s += `<path d="${arc(150, 0, 360 * 0.78)}" fill="none" stroke="${INK}" stroke-width="2" stroke-dasharray="2 4"/>`;
  s += moon(C, C - 6, 26, 1.6);
  [[C - 58, 96], [C + 62, 108], [C + 74, 150], [C - 72, 150], [C + 40, 72], [C - 44, 210]].forEach(([x, y], i) => s += star(x, y, i % 2 ? 2.4 : 1.8));
  s += T(C, 196, 'Wind down', { s: 24, w: 400, fam: GEO });
  s += T(C, 220, '22 minutes to lights out', { s: 10, w: 400, ls: 1, fam: GEO });
  s += topLabel(0, 'GOOD EVENING', { s: 9, ls: 6, fam: GEO });
  s += botLabel(0, 'ALARM 06:30 &#183; 8H 22M', { s: 8.5, ls: 2.5, fam: GEO });
  return frame(GEO, s);
}
function faceWeather() {
  let s = ring(176, 1, '1 6');
  s += topLabel(0, 'TODAY &#183; LONDON', { s: 8.5, w: 600, ls: 4, fam: GEO });
  let sun = `<circle cx="${C}" cy="104" r="16" fill="none" stroke="${INK}" stroke-width="1.5"/>`;
  for (let i = 0; i < 8; i++) { const a = i * 45 * RAD; sun += `<line x1="${f(C + Math.cos(a) * 19.5)}" y1="${f(104 + Math.sin(a) * 19.5)}" x2="${f(C + Math.cos(a) * 24)}" y2="${f(104 + Math.sin(a) * 24)}" stroke="${INK}" stroke-width="1.5" stroke-linecap="round"/>`; }
  s += sun;
  s += T(C, 182, '14&#176;', { s: 54, w: 400, fam: GEO, ls: -1 });
  s += T(C, 208, 'Partly cloudy', { s: 12, w: 400, ls: 1, fam: GEO });
  s += botLabel(0, 'RAIN FROM 18:00', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}
