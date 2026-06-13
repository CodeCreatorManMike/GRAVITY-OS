/* ============================================================
   GRAVITY — circular e-ink concept builder  (rev 0.4)
   1-bit: ink on paper. No greyscale, no fills (line/arc/dot/glyph).
   Everything lives inside a circular safe-zone; rim text curves.
   ============================================================ */
const C = 180, INK = '#14130d', PAPER = '#f4f2ea', RAD = Math.PI / 180;

const P  = (r, d) => [C + r * Math.sin(d * RAD), C - r * Math.cos(d * RAD)];
const f  = n => (+n).toFixed(2);
function arc(r, a, b, sw = 1) {
  const [x1, y1] = P(r, a), [x2, y2] = P(r, b);
  const large = Math.abs(b - a) > 180 ? 1 : 0;
  return `M${f(x1)} ${f(y1)} A${r} ${r} 0 ${large} ${sw} ${f(x2)} ${f(y2)}`;
}
const chordHW = (y, r) => Math.sqrt(Math.max(0, r * r - (y - C) * (y - C)));

/* primitives ------------------------------------------------- */
function ring(r, sw = 1, dash = null) {
  return `<circle cx="${C}" cy="${C}" r="${r}" fill="none" stroke="${INK}" stroke-width="${sw}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
}
function ticks(r, n, longEvery, len, longLen) {
  let s = '';
  for (let i = 0; i < n; i++) {
    const d = i * 360 / n, L = (i % longEvery === 0) ? longLen : len;
    const [x1, y1] = P(r, d), [x2, y2] = P(r - L, d);
    s += `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${INK}" stroke-width="${i % longEvery === 0 ? 1.3 : 0.7}"/>`;
  }
  return s;
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
function sq(x, y, s, filled) {
  return filled
    ? `<rect x="${f(x)}" y="${f(y)}" width="${s}" height="${s}" rx="1.2" fill="${INK}"/>`
    : `<rect x="${f(x + .55)}" y="${f(y + .55)}" width="${f(s - 1.1)}" height="${f(s - 1.1)}" rx="1" fill="none" stroke="${INK}" stroke-width="0.9"/>`;
}
/* square that rides an arc (rotated to the tangent) */
function arcSq(r, deg, s, filled) {
  const [x, y] = P(r, deg), t = `rotate(${f(deg)} ${f(x)} ${f(y)})`;
  return filled
    ? `<rect x="${f(x - s / 2)}" y="${f(y - s / 2)}" width="${s}" height="${s}" rx="1" transform="${t}" fill="${INK}"/>`
    : `<rect x="${f(x - s / 2 + .5)}" y="${f(y - s / 2 + .5)}" width="${f(s - 1)}" height="${f(s - 1)}" rx="1" transform="${t}" fill="none" stroke="${INK}" stroke-width="0.9"/>`;
}
function brackets(x, y, w, h, k = 9, sw = 1.2) {
  const L = (px, py, dx, dy) => `<path d="M${f(px + dx)} ${f(py)} H${f(px)} V${f(py + dy)}" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
  return L(x, y, k, k) + L(x + w, y, -k, k) + L(x, y + h, k, -k) + L(x + w, y + h, -k, -k);
}
function moon(cx, cy, R, sw = 1.5) {
  const top = `${f(cx)} ${f(cy - R)}`, bot = `${f(cx)} ${f(cy + R)}`;
  return `<path d="M ${top} A ${R} ${R} 0 0 0 ${bot} A ${f(R * 1.65)} ${f(R * 1.65)} 0 0 1 ${top}" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
}
function star(x, y, r = 2.4) {
  return `<path d="M${f(x)} ${f(y - r)} L${f(x)} ${f(y + r)} M${f(x - r)} ${f(y)} L${f(x + r)} ${f(y)}" stroke="${INK}" stroke-width="1"/>`;
}

/* curved rim text ------------------------------------------- */
function curve(id, r, a, b, sw = 0) { return `<path id="${id}" d="${arc(r, a, b, sw)}" fill="none"/>`; }
function onPath(id, str, o = {}) {
  const { s = 10, w = 500, ls = 3, fill = INK, off = '50%', fam = 'inherit' } = o;
  return `<text font-size="${s}" font-weight="${w}" letter-spacing="${ls}" fill="${fill}" font-family="${fam}"><textPath href="#${id}" startOffset="${off}" text-anchor="middle">${str}</textPath></text>`;
}
function topLabel(id, str, o = {}, r = 159, span = 52) { return curve(id, r, 360 - span, span, 1) + onPath(id, str, o); }
function botLabel(id, str, o = {}, r = 152, span = 52) { return curve(id, r, 180 + span, 180 - span, 0) + onPath(id, str, o); }

const frame = (font, inner) =>
  `<svg viewBox="0 0 360 360" font-family="${font}" shape-rendering="geometricPrecision" text-rendering="geometricPrecision">
     <rect width="360" height="360" fill="${PAPER}"/>${inner}</svg>`;

/* shared persona data --------------------------------------- */
const WEEK = [
  [1,0,1,1,1,1,1],
  [1,1,0,1,1,0,1],
  [0,1,1,1,1,1,1],
  [1,1,1,0,1,1,1],
  [1,1,1,1,0,1,1],
];
const STREAK14 = [1,1,0,1,1,1,1,1,1,1,1,1,1,1];

/* ============================================================
   DIRECTION A — TERMINAL  (JetBrains Mono)
   ============================================================ */
const MONO = "'JetBrains Mono', monospace";
function scan(y, r = 150, dash = '1.5 4', sw = 1) {
  const hw = chordHW(y, r);
  return `<line x1="${f(C - hw)}" y1="${y}" x2="${f(C + hw)}" y2="${y}" stroke="${INK}" stroke-width="${sw}" stroke-dasharray="${dash}"/>`;
}

function A1() {
  let s = ticks(176, 60, 5, 4, 9);
  s += topLabel('a1t', 'GRAVITY&#8201;OS&#8201;&#183;&#8201;SYS&#8201;OK', { s: 8.5, w: 600, ls: 4, fam: MONO });
  s += T(C, 168, '09:14', { s: 72, w: 600, ls: -1, fam: MONO });
  s += T(C, 206, 'FRI&#8201;12&#8201;JUN&#8201;2026', { s: 12.5, w: 400, ls: 3.5, fam: MONO });
  // 14-day heat ribbon riding a bottom arc
  const n = STREAK14.length, span = 86, r = 128;
  for (let i = 0; i < n; i++) s += arcSq(r, 180 - span / 2 + i * (span / (n - 1)), 8, STREAK14[i]);
  s += botLabel('a1b', '47-DAY&#8201;STREAK', { s: 9, w: 600, ls: 4, fam: MONO });
  return frame(MONO, s);
}

function A2() {
  let s = ticks(176, 60, 15, 3, 8);
  s += topLabel('a2t', '07:42&#8201;//&#8201;MORNING&#8201;BRIEF', { s: 8.5, w: 600, ls: 2.5, fam: MONO });
  s += brackets(86, 72, 188, 46, 9, 1.3);
  s += T(C, 87, 'TOP PRIORITY', { s: 8, w: 600, ls: 4, fam: MONO });
  s += T(C, 106, 'Finish Q3 roadmap', { s: 13, w: 500, ls: .2, fam: MONO });
  s += T(C, 144, 'NON-NEGOTIABLES', { s: 8.5, w: 600, ls: 3.5, fam: MONO });
  ['[x] 16K LONG RUN', '[ ] 2L WATER', '[ ] LIGHTS OUT 22:30'].forEach((t, i) =>
    s += T(C, 168 + i * 21, t, { s: 12, w: 400, ls: .4, fam: MONO }));
  s += botLabel('a2b', '&gt; SHIP BEFORE NOON. ONE BLOCK.', { s: 8.5, w: 500, ls: 1.5, fam: MONO });
  return frame(MONO, s);
}

function A3() {
  let s = ring(176, 1.4, '3 4') + ring(170, 0.7, '1.5 5');
  const chev = (cy, up) => `<path d="M${C-9} ${up?cy+6:cy-6} L${C} ${up?cy-3:cy+3} L${C+9} ${up?cy+6:cy-6}" fill="none" stroke="${INK}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>`;
  s += chev(40, true) + chev(320, false);
  s += topLabel('a3t', '!&#8201;MOVEMENT&#8201;ALERT&#8201;!', { s: 9.5, w: 700, ls: 3, fam: MONO });
  s += T(C, 112, "YOU HAVEN'T MOVED", { s: 12, w: 400, ls: 1.2, fam: MONO });
  s += T(C, 130, 'IN 4 HOURS.', { s: 12, w: 400, ls: 1.2, fam: MONO });
  s += T(C, 190, 'STAND', { s: 50, w: 700, ls: 1, fam: MONO });
  s += T(C, 232, 'UP.', { s: 50, w: 700, ls: 1, fam: MONO });
  s += botLabel('a3b', 'TAP&#8201;SNOOZE&#8201;&#183;&#8201;HOLD&#8201;DISMISS', { s: 8.5, w: 500, ls: 1.5, fam: MONO });
  return frame(MONO, s);
}

function A4() {
  const end = 360 * 0.62;
  let s = ticks(176, 48, 4, 4, 8);
  s += `<path d="${arc(160, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`;
  s += `<path d="${arc(160, 0, end)}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`;
  const [ex, ey] = P(160, end);
  s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="4.5" fill="${PAPER}" stroke="${INK}" stroke-width="2"/>`;
  s += topLabel('a4t', 'GOAL&#8201;//&#8201;6&#8201;MONTHS', { s: 8.5, w: 600, ls: 3, fam: MONO });
  s += T(C, 150, '62%', { s: 54, w: 700, ls: -1, fam: MONO });
  s += T(C, 176, 'HALF MARATHON', { s: 12, w: 500, ls: 2, fam: MONO });
  s += T(C, 195, 'T-94 DAYS', { s: 9, w: 400, ls: 1.5, fam: MONO });
  const subs = [['[x] LONG RUN', '16/16K'], ['[~] STRENGTH', '2/3'], ['[ ] SLEEP 7H', '5/7']];
  const lx = C - 80, rx = C + 80;
  subs.forEach((r, i) => {
    const y = 222 + i * 20;
    s += T(lx, y, r[0], { s: 10, w: 400, fam: MONO, a: 'start' });
    s += `<line x1="${lx + 78}" y1="${y - 3}" x2="${rx - 28}" y2="${y - 3}" stroke="${INK}" stroke-width="0.8" stroke-dasharray="1 3"/>`;
    s += T(rx, y, r[1], { s: 10, w: 500, fam: MONO, a: 'end' });
  });
  return frame(MONO, s);
}

function A5() {
  let s = ticks(176, 60, 30, 3, 7);
  s += topLabel('a5t', 'WEEK&#8201;24&#8201;//&#8201;LAST&#8201;7&#8201;DAYS', { s: 8.5, w: 600, ls: 2.5, fam: MONO });
  const days = ['S','S','M','T','W','T','F'], habits = ['MOVE','READ','FOCUS','SLEEP','CALM'];
  const cz = 18, gap = 6.5, cols = 7, rows = 5;
  const gw = cols * cz + (cols - 1) * gap;          // 18*7 + 6*6.5 = 165
  const gh = rows * cz + (rows - 1) * gap;          // 18*5 + 4*6.5 = 116
  const gx = C - gw / 2 + 14, gy = 200 - gh / 2;    // shift right for habit labels, vertically centred
  for (let c = 0; c < cols; c++) s += T(gx + c * (cz + gap) + cz / 2, gy - 10, days[c], { s: 9.5, w: c === 6 ? 700 : 400, fam: MONO });
  const tcx = gx + 6 * (cz + gap);
  s += brackets(tcx - 4, gy - 4.5, cz + 8, gh + 9, 6, 1.3);
  for (let r = 0; r < rows; r++) {
    const ry = gy + r * (cz + gap);
    s += T(gx - 9, ry + cz / 2 + 3.4, habits[r], { s: 8, w: 500, ls: .3, fam: MONO, a: 'end' });
    for (let c = 0; c < cols; c++) s += sq(gx + c * (cz + gap), ry, cz, WEEK[r][c]);
  }
  s += botLabel('a5b', '30&#8201;/&#8201;35&#8201;DONE&#8201;&#183;&#8201;86%', { s: 9.5, w: 600, ls: 1.5, fam: MONO });
  return frame(MONO, s);
}

function A6() {
  const rem = 24 + 18 / 60, total = 90, fracRem = rem / total, end = 360 * fracRem;
  let s = ticks(176, 60, 5, 3, 8);
  s += `<path d="${arc(160, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`;
  s += `<path d="${arc(160, 0, end)}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`;
  const [ex, ey] = P(160, end);
  s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="4.5" fill="${PAPER}" stroke="${INK}" stroke-width="2"/>`;
  s += topLabel('a6t', 'FOCUS&#8201;//&#8201;SESSION&#8201;02', { s: 8.5, w: 600, ls: 3, fam: MONO });
  s += T(C, 158, '24:18', { s: 52, w: 600, ls: -1, fam: MONO });
  s += T(C, 184, 'REMAINING', { s: 9, w: 400, ls: 4, fam: MONO });
  s += `<rect x="${C-58}" y="200" width="116" height="22" rx="2" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="3 3"/>`;
  s += T(C, 215, 'DND ACTIVE', { s: 9, w: 600, ls: 2, fam: MONO });
  s += T(C, 246, 'Q3 roadmap deck', { s: 11, w: 400, ls: .3, fam: MONO });
  s += botLabel('a6b', 'TAP&#8201;PAUSE&#8201;&#183;&#8201;HOLD&#8201;END', { s: 8.5, w: 500, ls: 1.5, fam: MONO });
  return frame(MONO, s);
}

function A7() {
  let s = ticks(176, 60, 30, 3, 6);
  s += topLabel('a7t', '22:08&#8201;//&#8201;WIND&#8201;DOWN', { s: 8.5, w: 600, ls: 3, fam: MONO });
  s += moon(C, 86, 16, 1.5);
  s += star(C - 30, 74) + star(C + 28, 92, 2) + star(C + 36, 66, 1.8);
  s += T(C, 146, 'LIGHTS OUT', { s: 11, w: 500, ls: 3, fam: MONO });
  s += T(C, 178, 'IN 22 MIN', { s: 30, w: 700, ls: 1, fam: MONO });
  s += scan(198, 120);
  s += T(C, 218, 'ALARM 06:30 &#183; 8H 22M', { s: 10, w: 400, ls: 1, fam: MONO });
  ['[x] SCREENS DOWN', '[ ] STRETCH'].forEach((t, i) =>
    s += T(C, 244 + i * 19, t, { s: 10, w: 400, ls: .4, fam: MONO }));
  s += botLabel('a7b', 'TOMORROW&#8201;&#183;&#8201;16K&#8201;LONG&#8201;RUN', { s: 8, w: 500, ls: 1.5, fam: MONO });
  return frame(MONO, s);
}

/* ============================================================
   DIRECTION B — ORBITAL  (Space Grotesk)
   ============================================================ */
const GEO = "'Space Grotesk', sans-serif";

function B1() {
  let s = ring(176, 1) + ring(150, 0.8) + ring(118, 0.7, '1 5');
  [0,90,180,270].forEach(d => { const [x1,y1]=P(176,d),[x2,y2]=P(168,d); s+=`<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${INK}" stroke-width="1.4"/>`; });
  const deg = (9 + 14/60) / 24 * 360;
  s += `<path d="${arc(150, 0, deg)}" fill="none" stroke="${INK}" stroke-width="2.2"/>`;
  s += `<path d="${arc(150, deg, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 5"/>`;
  const [px, py] = P(150, deg);
  s += `<circle cx="${f(px)}" cy="${f(py)}" r="4.5" fill="${INK}"/><circle cx="${f(px)}" cy="${f(py)}" r="8.5" fill="none" stroke="${INK}" stroke-width="1"/>`;
  s += T(C, 178, '9:14', { s: 58, w: 300, fam: GEO, ls: -1 });
  s += T(C, 208, 'Friday 12 June', { s: 13, w: 400, fam: GEO, ls: 2 });
  s += botLabel('b1b', '47 DAY STREAK', { s: 9.5, ls: 4, fam: GEO }, 134, 46);
  s += topLabel('b1t', 'GRAVITY', { s: 9, ls: 8, fam: GEO }, 162, 30);
  return frame(GEO, s);
}

function B2() {
  let s = ring(176, 1, '1 4') + ring(150, 0.8);
  s += topLabel('b2t', 'MORNING &#183; 07:42', { s: 9, ls: 5, fam: GEO });
  const sy = 78;
  s += `<line x1="${C - 24}" y1="${sy}" x2="${C + 24}" y2="${sy}" stroke="${INK}" stroke-width="1.2"/>`;
  s += `<path d="M${C - 13} ${sy} A13 13 0 0 0 ${C + 13} ${sy}" fill="none" stroke="${INK}" stroke-width="1.4"/>`;
  s += T(C, 120, 'TOP TODAY', { s: 8.5, w: 600, ls: 5, fam: GEO });
  s += T(C, 148, 'Finish the Q3', { s: 19, w: 500, fam: GEO });
  s += T(C, 172, 'roadmap deck', { s: 19, w: 500, fam: GEO });
  ['16K long run', '2L water', 'lights out 22:30'].forEach((it, i) => {
    const y = 204 + i * 22;
    s += `<circle cx="${C - 74}" cy="${y - 3.5}" r="3.3" fill="none" stroke="${INK}" stroke-width="1.1"/>`;
    if (i === 0) s += `<circle cx="${C - 74}" cy="${y - 3.5}" r="1.4" fill="${INK}"/>`;
    s += T(C - 62, y, it, { s: 11.5, w: 400, ls: .3, fam: GEO, a: 'start' });
  });
  s += botLabel('b2b', 'ONE DEEP BLOCK BEFORE NOON', { s: 8.5, ls: 2.5, fam: GEO });
  return frame(GEO, s);
}

function B3() {
  let s = '';
  [148, 116, 84, 52].forEach((r, i) => s += ring(r, 1.6 - i * 0.28, `${2 + i * 2} ${4 + i * 3}`));
  s += dot(C, C, 3.4, true);
  s += `<line x1="${C}" y1="${C}" x2="${P(150, 318)[0]}" y2="${P(150, 318)[1]}" stroke="${INK}" stroke-width="1" stroke-dasharray="2 4"/>`;
  s += T(C, 158, '4 HOURS STILL', { s: 9.5, w: 600, ls: 4, fam: GEO });
  s += T(C, 190, 'Stand up', { s: 34, w: 500, fam: GEO });
  s += topLabel('b3t', 'MOVEMENT ALERT', { s: 9, ls: 6, fam: GEO });
  s += botLabel('b3b', 'TAP TO SNOOZE &#183; HOLD TO CLEAR', { s: 8, ls: 2, fam: GEO });
  return frame(GEO, s);
}

function B4() {
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
  s += T(C, 32, 'GOAL', { s: 7.5, w: 600, ls: 2, fam: GEO });
  s += T(C, 58, 'TRAIN', { s: 7.5, w: 600, ls: 2, fam: GEO });
  s += T(C, 84, 'SLEEP', { s: 7.5, w: 600, ls: 2, fam: GEO });
  return frame(GEO, s);
}

function B5() {
  let s = '';
  const radii = [50, 72, 94, 116, 138], init = ['M','R','F','S','C'], days = ['S','S','M','T','W','T','F'];
  radii.forEach(r => s += ring(r, 0.7, '1 4'));
  for (let c = 0; c < 7; c++) {
    const d = c * 360 / 7, [x1, y1] = P(38, d), [x2, y2] = P(146, d);
    s += `<line x1="${f(x1)}" y1="${f(y1)}" x2="${f(x2)}" y2="${f(y2)}" stroke="${INK}" stroke-width="${c===6?1.4:0.6}"${c===6?'':' stroke-dasharray="1 4"'}/>`;
    const [lx, ly] = P(163, d);
    s += T(lx, ly + 3, days[c], { s: 9, w: c===6?700:400, fam: GEO });
  }
  for (let r = 0; r < 5; r++) for (let c = 0; c < 7; c++) {
    const [x, y] = P(radii[r], c * 360 / 7);
    s += dot(x, y, 3.4, WEEK[r][c], 1);
  }
  radii.forEach((r, i) => s += T(C - 11, 180 - r + 3, init[i], { s: 8, w: 600, ls: .5, fam: GEO, a: 'end' }));
  s += T(C, C - 3, 'WK', { s: 7.5, w: 600, ls: 1, fam: GEO });
  s += T(C, C + 8, '24', { s: 9, w: 500, fam: GEO });
  return frame(GEO, s);
}

function B6() {
  const fracRem = (24 + 18 / 60) / 90, end = 360 * fracRem;
  let s = ring(176, 1, '1 5') + ring(150, 0.8);
  // depleting ring: remaining is bold, spent is dotted
  s += `<path d="${arc(150, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 5"/>`;
  s += `<path d="${arc(150, 0, end)}" fill="none" stroke="${INK}" stroke-width="3.2" stroke-linecap="round"/>`;
  const [px, py] = P(150, end);
  s += `<circle cx="${f(px)}" cy="${f(py)}" r="4.5" fill="${INK}"/>`;
  s += T(C, 184, '24:18', { s: 46, w: 300, fam: GEO, ls: -1 });
  s += T(C, 210, 'remaining', { s: 11, w: 400, ls: 3, fam: GEO });
  s += topLabel('b6t', 'DEEP WORK', { s: 9, ls: 6, fam: GEO });
  s += botLabel('b6b', 'SESSION 02 &#183; Q3 DECK', { s: 8.5, ls: 2.5, fam: GEO });
  return frame(GEO, s);
}

function B7() {
  let s = ring(176, 1, '1 5') + ring(150, 0.8, '1 4');
  // bedtime arc — time-until ring
  const deg = 360 * 0.78;
  s += `<path d="${arc(150, 0, deg)}" fill="none" stroke="${INK}" stroke-width="2" stroke-dasharray="2 4"/>`;
  s += moon(C, C - 6, 26, 1.6);
  // scattered stars on the field
  [[C-58,96],[C+62,108],[C+74,150],[C-72,150],[C+40,72],[C-44,210],[C+60,232]].forEach(([x,y],i)=> s += star(x, y, i%2?2.4:1.8));
  s += T(C, 196, 'Wind down', { s: 24, w: 400, fam: GEO });
  s += T(C, 220, '22 minutes to lights out', { s: 10, w: 400, ls: 1, fam: GEO });
  s += topLabel('b7t', 'GOOD EVENING', { s: 9, ls: 6, fam: GEO });
  s += botLabel('b7b', 'ALARM 06:30 &#183; 8H 22M', { s: 8.5, ls: 2.5, fam: GEO });
  return frame(GEO, s);
}

/* ============================================================
   DIRECTION C — MINIMAL TYPE  (Sora)
   ============================================================ */
const SORA = "'Sora', sans-serif";

function C1() {
  let s = `<line x1="${C}" y1="22" x2="${C}" y2="32" stroke="${INK}" stroke-width="1.4"/>`;
  s += T(C, 186, '9:14', { s: 84, w: 200, fam: SORA, ls: -2 });
  s += T(C, 224, 'fri 12 jun', { s: 12, w: 300, ls: 6, fam: SORA });
  s += dot(C - 13, 290, 2.3, true);
  s += T(C + 4, 294, '47', { s: 13, w: 400, ls: 2, fam: SORA, a: 'start' });
  return frame(SORA, s);
}

function C2() {
  let s = T(C, 96, 'TODAY', { s: 10, w: 500, ls: 8, fam: SORA });
  s += T(C, 146, 'Finish the Q3', { s: 26, w: 400, fam: SORA, ls: -.3 });
  s += T(C, 177, 'roadmap deck.', { s: 26, w: 400, fam: SORA, ls: -.3 });
  s += `<line x1="${C - 26}" y1="202" x2="${C + 26}" y2="202" stroke="${INK}" stroke-width="1"/>`;
  s += T(C, 232, 'long run &#183; 2L water &#183; lights 22:30', { s: 10.5, w: 300, ls: 1.2, fam: SORA });
  s += T(C, 260, 'One deep block before noon.', { s: 12.5, w: 300, fam: SORA, style: 'font-style:italic' });
  return frame(SORA, s);
}

function C3() {
  let s = `<line x1="${C}" y1="64" x2="${C}" y2="120" stroke="${INK}" stroke-width="1"/>`;
  s += T(C, 144, '4 hours still', { s: 11, w: 300, ls: 4, fam: SORA });
  s += T(C, 202, 'Stand.', { s: 58, w: 400, fam: SORA, ls: -1 });
  s += `<line x1="${C}" y1="244" x2="${C}" y2="288" stroke="${INK}" stroke-width="1"/>`;
  s += T(C, 310, 'tap to snooze', { s: 9.5, w: 300, ls: 3, fam: SORA });
  return frame(SORA, s);
}

function C4() {
  let s = `<path d="${arc(162, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="0.6" stroke-dasharray="1 5"/>`;
  s += `<path d="${arc(162, 0, 360 * .62)}" fill="none" stroke="${INK}" stroke-width="1.6" stroke-linecap="round"/>`;
  const [ex, ey] = P(162, 360 * .62);
  s += dot(ex, ey, 2.6, true);
  s += T(C, 118, 'HALF MARATHON', { s: 10, w: 500, ls: 6, fam: SORA });
  s += T(C, 186, '62%', { s: 74, w: 300, fam: SORA, ls: -2 });
  s += T(C, 216, '94 days left', { s: 11, w: 300, ls: 2, fam: SORA });
  s += T(C, 262, 'long run &#10003;   strength 2/3   sleep 5/7', { s: 10, w: 300, ls: .5, fam: SORA });
  return frame(SORA, s);
}

function C5() {
  let s = T(C, 60, 'THIS WEEK', { s: 10, w: 500, ls: 8, fam: SORA });
  const days = ['s','s','m','t','w','t','f'], habits = ['move','read','focus','sleep','calm'];
  const cols = 7, rows = 5, gx0 = 134, gy0 = 116, dx = 19, dy = 20.5;
  for (let c = 0; c < cols; c++) s += T(gx0 + c * dx, gy0 - 14, days[c], { s: 8.5, w: c===6?600:300, ls: 1, fam: SORA });
  for (let r = 0; r < rows; r++) {
    s += T(gx0 - 26, gy0 + r * dy + 3, habits[r], { s: 8.5, w: 300, ls: 1, fam: SORA, a: 'end' });
    for (let c = 0; c < cols; c++) s += dot(gx0 + c * dx, gy0 + r * dy, 3.1, WEEK[r][c], 1);
  }
  s += T(C, 296, '30 of 35 &#183; 86%', { s: 11, w: 300, ls: 2, fam: SORA });
  return frame(SORA, s);
}

function C6() {
  let s = `<path d="${arc(160, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="0.6" stroke-dasharray="1 5"/>`;
  const fracRem = (24 + 18 / 60) / 90;
  s += `<path d="${arc(160, 0, 360 * fracRem)}" fill="none" stroke="${INK}" stroke-width="1.6" stroke-linecap="round"/>`;
  const [ex, ey] = P(160, 360 * fracRem);
  s += dot(ex, ey, 2.6, true);
  s += T(C, 118, 'FOCUS', { s: 10, w: 500, ls: 9, fam: SORA });
  s += T(C, 192, '24:18', { s: 64, w: 200, fam: SORA, ls: -2 });
  s += T(C, 226, 'q3 roadmap deck', { s: 11, w: 300, ls: 1, fam: SORA });
  return frame(SORA, s);
}

function C7() {
  let s = moon(C, 118, 30, 1.4);
  s += star(C - 46, 96, 2.2) + star(C + 50, 130, 1.8) + star(C + 40, 84, 1.6);
  s += T(C, 214, 'Wind down.', { s: 38, w: 300, fam: SORA, ls: -1 });
  s += T(C, 250, 'lights out 22:30', { s: 11, w: 300, ls: 2, fam: SORA });
  return frame(SORA, s);
}

/* ============================================================
   DATA + RENDER
   ============================================================ */
const directions = [
  {
    badge: 'A', name: 'Terminal', font: 'JetBrains Mono',
    phil: 'A 1980s flight computer. <b>Monospace, a perimeter tick-gauge, scanline dividers and bracketed readouts.</b> Rim text curves along the bezel; every value is labelled like a system register booting.',
    screens: [
      { id: 'A1', name: 'Ambient / Idle', svg: A1, note: 'Tick-gauge bezel + curved system banner frame the disc. Time owns the centre; the 14-day streak curves along a lower arc, hugging the glass.', reads: ['Time', 'Date', 'Streak'] },
      { id: 'A2', name: 'Morning Brief', svg: A2, note: 'Curved header, a bracketed priority readout, a centred checklist that tapers with the circle, and a curved focus prompt on the base.', reads: ['Top task', 'Non-neg.', 'Focus'] },
      { id: 'A3', name: 'Active Nudge', svg: A3, note: 'Dashed alert ring + chevrons; the alert title and dismiss controls ride the rim so the centre is pure verb — "STAND UP".', reads: ['STAND UP', 'Reason', 'Dismiss'] },
      { id: 'A4', name: 'Goal Progress', svg: A4, note: 'A heavy arc tracks 62% on the perimeter scale. Centre states number + goal; dotted-leader subtasks read like a manifest.', reads: ['62%', 'Goal', 'Subtasks'] },
      { id: 'A5', name: 'Weekly Heatmap', svg: A5, note: 'A deliberate computer grid — filled = done, outline = missed — wrapped in curved rim labels. Today\'s column is bracketed.', reads: ['Pattern', 'Today', 'Total'] },
      { id: 'A6', name: 'Focus Timer', svg: A6, note: 'A 90-minute deep block depleting on the bezel. Time-remaining dominates; DND state and the task sit quietly beneath.', reads: ['Time left', 'DND', 'Task'] },
      { id: 'A7', name: 'Wind-down', svg: A7, note: 'Night mode: a moon glyph + stars up top, the sleep window centred, a 2-item ritual, and tomorrow\'s first thing curved on the base.', reads: ['Lights out', 'Sleep window', 'Tomorrow'] },
    ],
  },
  {
    badge: 'B', name: 'Orbital', font: 'Space Grotesk',
    phil: 'A radar / orrery. <b>Concentric rings, arcs and orbiting dots; labels curve along the rim.</b> Data lives on rings around a calm centre — the circle is a coordinate system, never a box.',
    screens: [
      { id: 'B1', name: 'Ambient / Idle', svg: B1, note: 'A dot orbits the day on the outer ring (now 9:14). The calm centre holds the time; streak and brand curve along the rim.', reads: ['Time', 'Date', 'Day-arc'] },
      { id: 'B2', name: 'Morning Brief', svg: B2, note: 'Priority rests in the still centre under a sunrise mark; non-negotiables are a ring-bulleted list; the focus line curves along the base.', reads: ['Priority', 'Tasks', 'Focus'] },
      { id: 'B3', name: 'Active Nudge', svg: B3, note: 'Radar "ping" rings pulse from a centre dot — motion implied without animation. "Stand up" sits at the calm core.', reads: ['Stand up', 'Reason', 'Dismiss'] },
      { id: 'B4', name: 'Goal Progress', svg: B4, note: 'Three concentric rings — goal, training, sleep — each an outline track with a bold arc and endpoint node. The % anchors the core.', reads: ['62%', 'Goal', 'Sub-rings'] },
      { id: 'B5', name: 'Weekly Heatmap', svg: B5, note: 'A polar grid: 7 day-spokes × 5 habit-rings, dots at the crossings, keyed by initials. Today\'s spoke is solid; the field reads at distance.', reads: ['Field', 'Today', 'Habits'] },
      { id: 'B6', name: 'Focus Timer', svg: B6, note: 'The outer ring depletes as the session burns down; the endpoint dot is the "hand". The calm centre is just the time left.', reads: ['Time left', 'Ring', 'Session'] },
      { id: 'B7', name: 'Wind-down', svg: B7, note: 'A crescent at the core with stars scattered across the rings; a dashed arc counts down to bedtime. Quiet, dim, nocturnal.', reads: ['Wind down', 'Minutes', 'Alarm'] },
    ],
  },
  {
    badge: 'C', name: 'Minimal Type', font: 'Sora',
    phil: 'An e-ink editorial page. <b>Almost no graphics — beautifully set type and a single strong element per screen.</b> Maximal negative space; the circle breathes and one idea lands.',
    screens: [
      { id: 'C1', name: 'Ambient / Idle', svg: C1, note: 'Just the time, enormous and light, with a hairline orientation tick. Date whispers below; the streak is a single dot + number.', reads: ['Time', 'Date', 'Streak'] },
      { id: 'C2', name: 'Morning Brief', svg: C2, note: 'The priority is the headline, set like a magazine deck. A short rule separates it from quiet non-negotiables and an italic focus line.', reads: ['Headline', 'Non-neg.', 'Focus'] },
      { id: 'C3', name: 'Active Nudge', svg: C3, note: 'One imperative word. The thin lines above and below act like a held breath — the single visual element. Reason and action stay tiny.', reads: ['Stand.', 'Reason', 'Action'] },
      { id: 'C4', name: 'Goal Progress', svg: C4, note: 'The number is the hero. A single fine perimeter arc is the only graphic; subtasks sit in one quiet typeset line below.', reads: ['62%', 'Goal', 'Subtasks'] },
      { id: 'C5', name: 'Weekly Heatmap', svg: C5, note: 'A refined dot matrix with generous air. Filled = done, ring = missed. Today\'s column is weighted; the rate sums it up.', reads: ['Matrix', 'Today', 'Rate'] },
      { id: 'C6', name: 'Focus Timer', svg: C6, note: 'Time as typography. One hairline arc shows the session draining; the task is a single quiet line. Nothing else competes.', reads: ['Time left', 'Arc', 'Task'] },
      { id: 'C7', name: 'Wind-down', svg: C7, note: 'A single crescent and a soft instruction. The most editorial screen — a held image and two words to end the day on.', reads: ['Moon', 'Wind down.', 'Lights out'] },
    ],
  },
];

const main = document.getElementById('main');
directions.forEach(d => {
  const sec = document.createElement('section');
  sec.className = 'dir';
  let cards = '';
  d.screens.forEach((sc, i) => {
    const reads = sc.reads.map((r, j) => `<span><i>${j + 1}</i><b>${r}</b></span>`).join('');
    cards += `<figure class="card">
      <div class="statelabel"><span class="num">${d.badge}${i + 1}</span><span class="nm">${sc.name}</span></div>
      <div class="disc-wrap">${sc.svg()}</div>
      <figcaption><p>${sc.note}</p><div class="reads">${reads}</div></figcaption>
    </figure>`;
  });
  sec.innerHTML = `
    <div class="dirhead"><span class="badge">${d.badge}</span><h2>${d.name}</h2><span class="font">${d.font}</span></div>
    <p class="dirphil">${d.phil}</p>
    <div class="row">${cards}</div>`;
  main.appendChild(sec);
});
