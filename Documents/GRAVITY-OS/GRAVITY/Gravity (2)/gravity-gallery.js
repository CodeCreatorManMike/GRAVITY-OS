/* ============================================================
   GRAVITY — Expanded Gallery  (rev 0.6)
   Quantity pass: more main screens, lots of to-do lists, and a
   components sheet. Same 1-bit circular grammar — ink on paper,
   no greyscale, no fills beyond line / arc / dot / glyph.
   Loads after gravity-build.js + gravity-library.js and reuses
   their globals (C, INK, PAPER, P, f, arc, ring, ticks, T, dot,
   sq, arcSq, brackets, moon, star, scan, topLabel, botLabel,
   frame, MONO, GEO, SORA, WEEK, STREAK14, progArc, check, bell,
   droplet, sun, tri).
   ============================================================ */

/* generic (off-centre) arc/ring helpers for component layouts */
const gP = (cx, cy, r, d) => [cx + r * Math.sin(d * RAD), cy - r * Math.cos(d * RAD)];
function gArc(cx, cy, r, a, b, sw = 1) {
  const [x1, y1] = gP(cx, cy, r, a), [x2, y2] = gP(cx, cy, r, b);
  const large = Math.abs(b - a) > 180 ? 1 : 0;
  return `M${f(x1)} ${f(y1)} A${r} ${r} 0 ${large} ${sw} ${f(x2)} ${f(y2)}`;
}
function gRing(cx, cy, r, sw = 1, dash = null) {
  return `<circle cx="${f(cx)}" cy="${f(cy)}" r="${r}" fill="none" stroke="${INK}" stroke-width="${sw}"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
}

/* a reusable checklist column ------------------------------- */
function taskList(items, o = {}) {
  const { top = 124, gap = 23, cx = C - 74, font = GEO, size = 11.5 } = o;
  let s = '';
  items.forEach(([t, state], i) => {
    const y = top + i * gap, by = y - 3.5;
    const done = state === 'done', active = state === 'active', over = state === 'over';
    s += `<circle cx="${f(cx)}" cy="${f(by)}" r="5" fill="none" stroke="${INK}" stroke-width="${over ? 1.6 : 1.2}"/>`;
    if (done) s += check(cx, by, 2.6, 1.3);
    else if (active) s += `<circle cx="${f(cx)}" cy="${f(by)}" r="1.7" fill="${INK}"/>`;
    else if (over) s += T(cx, by + 3.2, '!', { s: 9, w: 700, fam: font });
    s += T(cx + 14, y, t, { s: size, w: done ? 400 : 500, ls: .2, fam: font, a: 'start', op: done ? .5 : 1, style: done ? 'text-decoration:line-through' : '' });
  });
  return s;
}

/* ============================================================
   SECTION D — TASKS & LISTS  (Orbital house · Space Grotesk)
   ============================================================ */

/* D1 — Today, mixed states */
function D1() {
  let s = progArc(158, 2 / 6, 4);
  s += topLabel('d1t', 'TODAY &#183; 6 TASKS', { s: 8.5, w: 600, ls: 3, fam: GEO });
  s += taskList([
    ['Standup notes', 'done'], ['Reply to Sam', 'done'],
    ['Q3 roadmap deck', 'active'], ['Gym at 18:00', 'open'],
    ['Book flights', 'open'], ['Call dentist', 'open'],
  ], { top: 122, gap: 22 });
  s += botLabel('d1b', '2 OF 6 DONE &#183; 1 IN PROGRESS', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* D2 — Grouped by time of day */
function D2() {
  let s = ring(176, 1, '1 5');
  s += topLabel('d2t', 'SCHEDULE &#183; WED', { s: 8.5, w: 600, ls: 3, fam: GEO });
  s += T(C - 74, 100, 'MORNING', { s: 8, w: 600, ls: 3, fam: GEO, a: 'start' });
  s += taskList([['Inbox to zero', 'done'], ['Deep work block', 'active']], { top: 120, gap: 21 });
  s += T(C - 74, 168, 'AFTERNOON', { s: 8, w: 600, ls: 3, fam: GEO, a: 'start' });
  s += taskList([['1:1 with Sam', 'open'], ['Review PRs', 'open']], { top: 188, gap: 21 });
  s += botLabel('d2b', 'NEXT &#183; DEEP WORK 09:30', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* D3 — All done / inbox zero */
function D3() {
  let s = progArc(158, 1, 5);
  s += topLabel('d3t', 'TODAY', { s: 9, w: 600, ls: 9, fam: GEO });
  s += gRing(C, 150, 26, 1.6);
  s += check(C, 150, 8, 2.2);
  [[C - 44, 118], [C + 46, 132], [C + 40, 96], [C - 40, 168], [C + 52, 176]].forEach(([x, y], i) => s += star(x, y, i % 2 ? 2.4 : 1.8));
  s += T(C, 206, 'All clear', { s: 26, w: 500, fam: GEO });
  s += T(C, 230, '6 of 6 done today', { s: 11, w: 400, ls: 1, fam: GEO });
  s += botLabel('d3b', 'NOTHING ELSE DUE', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* D4 — One priority + subtasks + due arc */
function D4() {
  const rem = 0.55, end = 360 * rem;
  let s = `<path d="${arc(160, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 5"/>`;
  s += `<path d="${arc(160, 0, end)}" fill="none" stroke="${INK}" stroke-width="4" stroke-linecap="round"/>`;
  const [ex, ey] = P(160, end);
  s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="4" fill="${PAPER}" stroke="${INK}" stroke-width="1.8"/>`;
  s += topLabel('d4t', 'TOP PRIORITY', { s: 8.5, w: 600, ls: 5, fam: GEO });
  s += T(C, 124, 'Ship Q3 deck', { s: 22, w: 500, fam: GEO });
  s += taskList([
    ['Final numbers', 'done'], ['Exec summary', 'active'], ['Send to Sam', 'open'],
  ], { top: 158, gap: 22, cx: C - 58, size: 11 });
  s += botLabel('d4b', 'DUE 17:00 &#183; 2H 40M LEFT', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* D5 — Groceries */
function D5() {
  let s = progArc(158, 3 / 8, 4);
  s += topLabel('d5t', 'GROCERIES &#183; 8', { s: 8.5, w: 600, ls: 4, fam: GEO });
  s += taskList([
    ['Milk', 'done'], ['Eggs', 'done'], ['Sourdough', 'done'],
    ['Coffee beans', 'open'], ['Spinach', 'open'], ['Lemons', 'open'],
  ], { top: 116, gap: 22, size: 11.5 });
  s += botLabel('d5b', '3 OF 8 IN THE BASKET', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* D6 — Packing list w/ progress */
function D6() {
  let s = progArc(158, 4 / 7, 5);
  s += topLabel('d6t', 'PACKING &#183; LISBON', { s: 8.5, w: 600, ls: 3, fam: GEO });
  s += T(C, 134, '4 / 7', { s: 36, w: 500, fam: GEO, ls: -1 });
  s += T(C, 158, 'packed', { s: 10.5, w: 400, ls: 2, fam: GEO });
  for (let i = 0; i < 7; i++) {
    const [x, y] = P(132, 180 - 40 + i * (80 / 6));
    s += dot(x, y, 4, i < 4, 1.3);
  }
  s += T(C, 196, 'Next: charger, passport', { s: 10, w: 400, ls: .3, fam: GEO });
  s += botLabel('d6b', 'LEAVE FRI &#183; 06:00', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* D7 — Errands w/ times (dotted leaders) */
function D7() {
  let s = ring(176, 1, '1 6');
  s += topLabel('d7t', 'ERRANDS', { s: 9, w: 600, ls: 8, fam: GEO });
  const rows = [['Pharmacy', '10:00'], ['Post office', '11:30'], ['Dry cleaner', '13:00'], ['Hardware', '15:30']];
  const lx = C - 78, rx = C + 78;
  rows.forEach((r, i) => {
    const y = 118 + i * 28, by = y - 3.5;
    s += `<circle cx="${f(lx)}" cy="${f(by)}" r="4.5" fill="none" stroke="${INK}" stroke-width="1.2"/>`;
    if (i === 0) s += check(lx, by, 2.4, 1.2);
    s += T(lx + 13, y, r[0], { s: 11, w: 500, fam: GEO, a: 'start', op: i === 0 ? .5 : 1, style: i === 0 ? 'text-decoration:line-through' : '' });
    s += `<line x1="${lx + 90}" y1="${y - 3}" x2="${rx - 30}" y2="${y - 3}" stroke="${INK}" stroke-width="0.8" stroke-dasharray="1 3"/>`;
    s += T(rx, y, r[1], { s: 10, w: 500, fam: GEO, a: 'end' });
  });
  s += botLabel('d7b', '1 OF 4 DONE', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* D8 — Morning routine (daily ritual) */
function D8() {
  let s = progArc(158, 3 / 5, 4);
  s += topLabel('d8t', 'MORNING ROUTINE', { s: 8.5, w: 600, ls: 3, fam: GEO });
  s += taskList([
    ['Make the bed', 'done'], ['Meditate 10m', 'done'], ['Stretch', 'done'],
    ['Journal', 'open'], ['No phone til 9', 'open'],
  ], { top: 124, gap: 22 });
  s += botLabel('d8b', 'STREAK 12 DAYS &#183; 3 OF 5', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* D9 — Reminders / due soon (bells) */
function D9() {
  let s = ring(176, 1, '1 6');
  s += topLabel('d9t', 'REMINDERS', { s: 9, w: 600, ls: 7, fam: GEO });
  s += bell(C, 96, 16, 1.5);
  const rows = [['Call Mum', '18:00'], ['Pay rent', 'TOMORROW'], ['Dentist', 'FRI 09:30']];
  rows.forEach((r, i) => {
    const y = 150 + i * 28;
    s += T(C, y, r[0], { s: 13, w: 500, fam: GEO });
    s += T(C, y + 14, r[1], { s: 8.5, w: 600, ls: 2, fam: GEO, op: .7 });
  });
  s += botLabel('d9b', '3 UPCOMING &#183; TAP TO SNOOZE', { s: 8, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* D10 — Overdue / behind */
function D10() {
  let s = ring(176, 1.4, '3 4') + ring(170, 0.7, '1.5 5');
  s += topLabel('d10t', '! 2 OVERDUE', { s: 9.5, w: 700, ls: 3, fam: GEO });
  s += taskList([
    ['Submit invoice', 'over'], ['Renew licence', 'over'],
    ['Reply to Lena', 'active'], ['Water plants', 'open'],
  ], { top: 128, gap: 24 });
  s += botLabel('d10b', 'CLEAR THE RED FIRST', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ============================================================
   SECTION E — COMPONENTS  (Terminal house · JetBrains Mono)
   Each disc is one component family with its states.
   ============================================================ */

/* E1 — Checkbox / radio states */
function E1() {
  let s = ring(176, 1, '1 6');
  s += topLabel('e1t', 'SELECTION', { s: 9, w: 600, ls: 6, fam: MONO });
  const items = [['EMPTY', 'empty'], ['CHECKED', 'check'], ['ACTIVE', 'dot'], ['DISABLED', 'disabled']];
  const cx = C - 56;
  items.forEach(([lbl, k], i) => {
    const y = 118 + i * 32, by = y - 3.5;
    s += `<circle cx="${f(cx)}" cy="${f(by)}" r="6" fill="none" stroke="${INK}" stroke-width="${k === 'disabled' ? 1 : 1.4}"${k === 'disabled' ? ' stroke-dasharray="2 2.5"' : ''}/>`;
    if (k === 'check') s += check(cx, by, 3, 1.5);
    if (k === 'dot') s += `<circle cx="${f(cx)}" cy="${f(by)}" r="2.4" fill="${INK}"/>`;
    s += T(cx + 18, y, lbl, { s: 11, w: 500, ls: 1, fam: MONO, a: 'start', op: k === 'disabled' ? .4 : 1 });
  });
  s += botLabel('e1b', 'TAP TO TOGGLE', { s: 8, ls: 3, fam: MONO });
  return frame(MONO, s);
}

/* E2 — Progress arcs (25/50/75/100) */
function E2() {
  let s = topLabel('e2t', 'PROGRESS ARC', { s: 9, w: 600, ls: 5, fam: MONO });
  const cells = [['25', .25], ['50', .50], ['75', .75], ['100', 1]];
  const xs = [C - 88, C - 29, C + 30, C + 89];
  cells.forEach(([lbl, p], i) => {
    const cx = xs[i], cy = 158, r = 22;
    s += `<path d="${gArc(cx, cy, r, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`;
    s += `<path d="${gArc(cx, cy, r, 0, 360 * p)}" fill="none" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`;
    s += T(cx, cy + 4, lbl, { s: 13, w: 600, fam: MONO });
    s += T(cx, 210, lbl + '%', { s: 8.5, w: 400, ls: 1, fam: MONO });
  });
  s += botLabel('e2b', 'STROKE 3.4 &#183; ROUND CAP', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E3 — Toggle / switch */
function E3() {
  let s = ring(176, 1, '1 6');
  s += topLabel('e3t', 'TOGGLE', { s: 9, w: 600, ls: 8, fam: MONO });
  const pill = (cy, on) => {
    let p = `<rect x="${C - 26}" y="${cy - 11}" width="52" height="22" rx="11" fill="none" stroke="${INK}" stroke-width="1.4"${on ? '' : ' stroke-dasharray="2 2.5"'}/>`;
    p += `<circle cx="${on ? C + 13 : C - 13}" cy="${cy}" r="${on ? 7.5 : 6.5}" fill="${on ? INK : 'none'}" stroke="${INK}" stroke-width="1.4"/>`;
    return p;
  };
  s += T(C, 116, 'OFF', { s: 9, w: 600, ls: 3, fam: MONO });
  s += pill(140, false);
  s += T(C, 196, 'ON', { s: 9, w: 600, ls: 3, fam: MONO });
  s += pill(220, true);
  s += botLabel('e3b', 'SWIPE OR TAP', { s: 8, ls: 3, fam: MONO });
  return frame(MONO, s);
}

/* E4 — Stepper / counter */
function E4() {
  let s = ring(176, 1, '1 6');
  s += topLabel('e4t', 'STEPPER', { s: 9, w: 600, ls: 7, fam: MONO });
  const cy = 176;
  s += `<circle cx="${C - 64}" cy="${cy}" r="20" fill="none" stroke="${INK}" stroke-width="1.4"/>`;
  s += `<line x1="${C - 73}" y1="${cy}" x2="${C - 55}" y2="${cy}" stroke="${INK}" stroke-width="1.6"/>`;
  s += `<circle cx="${C + 64}" cy="${cy}" r="20" fill="none" stroke="${INK}" stroke-width="1.4"/>`;
  s += `<line x1="${C + 55}" y1="${cy}" x2="${C + 73}" y2="${cy}" stroke="${INK}" stroke-width="1.6"/>`;
  s += `<line x1="${C + 64}" y1="${cy - 9}" x2="${C + 64}" y2="${cy + 9}" stroke="${INK}" stroke-width="1.6"/>`;
  s += T(C, cy + 11, '3', { s: 44, w: 600, fam: MONO });
  s += T(C, 124, 'GLASSES OF WATER', { s: 8, w: 600, ls: 2.5, fam: MONO });
  s += botLabel('e4b', 'HOLD TO RESET', { s: 8, ls: 3, fam: MONO });
  return frame(MONO, s);
}

/* E5 — Buttons / actions */
function E5() {
  let s = topLabel('e5t', 'ACTIONS', { s: 9, w: 600, ls: 8, fam: MONO });
  const btn = (cy, label, dashed, disabled) => {
    let b = `<rect x="${C - 72}" y="${cy - 15}" width="144" height="30" rx="3" fill="none" stroke="${INK}" stroke-width="1.3"${dashed ? ' stroke-dasharray="3 3"' : ''}/>`;
    b += T(C, cy + 4, label, { s: 10.5, w: 600, ls: 2, fam: MONO, op: disabled ? .35 : 1 });
    return b;
  };
  s += btn(116, 'TAP &#183; START', false, false);
  s += btn(160, 'HOLD &#183; CONFIRM', true, false);
  s += btn(204, 'DISABLED', false, true);
  s += T(C, 244, 'primary / hold / off', { s: 9, w: 400, ls: 1, fam: MONO, op: .6 });
  s += botLabel('e5b', 'CAP. TAP / SWIPE / HOLD', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E6 — Tick gauge w/ pointer */
function E6() {
  let s = ticks(176, 60, 5, 4, 9);
  s += topLabel('e6t', 'GAUGE', { s: 9, w: 600, ls: 9, fam: MONO });
  const deg = 360 * 0.68;
  const [px, py] = P(150, deg);
  s += `<line x1="${C}" y1="${C}" x2="${f(px)}" y2="${f(py)}" stroke="${INK}" stroke-width="1.6"/>`;
  s += `<circle cx="${C}" cy="${C}" r="4" fill="${INK}"/>`;
  s += `<circle cx="${f(px)}" cy="${f(py)}" r="4" fill="${PAPER}" stroke="${INK}" stroke-width="1.8"/>`;
  s += T(C, 212, '68', { s: 30, w: 600, fam: MONO });
  s += T(C, 232, 'OF 100', { s: 8.5, w: 400, ls: 3, fam: MONO });
  s += botLabel('e6b', '60 TICKS &#183; LONG EVERY 5', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E7 — Segmented control on an arc */
function E7() {
  let s = topLabel('e7t', 'SEGMENTED', { s: 9, w: 600, ls: 6, fam: MONO });
  const segs = [[200, 248, 'DAY', 0], [256, 304, 'WEEK', 1], [312, 360, 'MNTH', 0]];
  segs.forEach(([a, b, lbl, on]) => {
    s += `<path d="${arc(150, a - 180, b - 180)}" fill="none" stroke="${INK}" stroke-width="${on ? 6 : 1.6}" stroke-linecap="butt"/>`;
  });
  s += T(C - 58, 196, 'DAY', { s: 9, w: 500, ls: 1, fam: MONO });
  s += T(C, 232, 'WEEK', { s: 11, w: 700, ls: 1, fam: MONO });
  s += T(C + 58, 196, 'MNTH', { s: 9, w: 500, ls: 1, fam: MONO });
  s += T(C, 150, 'RANGE', { s: 8.5, w: 600, ls: 4, fam: MONO });
  s += botLabel('e7b', 'ACTIVE = SOLID ARC', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E8 — Slider on an arc */
function E8() {
  let s = topLabel('e8t', 'SLIDER', { s: 9, w: 600, ls: 8, fam: MONO });
  const a0 = 230, a1 = 310, t = 0.62, deg = a0 + (a1 - a0) * t;
  s += `<path d="${arc(150, a0 - 180, a1 - 180)}" fill="none" stroke="${INK}" stroke-width="1.2" stroke-dasharray="2 3"/>`;
  s += `<path d="${arc(150, a0 - 180, deg - 180)}" fill="none" stroke="${INK}" stroke-width="3.4" stroke-linecap="round"/>`;
  const [kx, ky] = P(150, deg - 180);
  s += `<circle cx="${f(kx)}" cy="${f(ky)}" r="7" fill="${PAPER}" stroke="${INK}" stroke-width="2"/>`;
  s += T(C, 168, '62', { s: 40, w: 600, fam: MONO });
  s += T(C, 190, 'BRIGHTNESS', { s: 8.5, w: 600, ls: 3, fam: MONO });
  s += botLabel('e8b', 'DRAG ALONG THE RIM', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E9 — Status / system icons */
function E9() {
  let s = ring(176, 1, '1 6');
  s += topLabel('e9t', 'STATUS', { s: 9, w: 600, ls: 8, fam: MONO });
  // battery
  const bx = C - 70, by = 150;
  s += `<rect x="${bx - 16}" y="${by - 8}" width="32" height="16" rx="2" fill="none" stroke="${INK}" stroke-width="1.4"/>`;
  s += `<rect x="${bx + 17}" y="${by - 3}" width="3" height="6" rx="1" fill="${INK}"/>`;
  s += `<rect x="${bx - 13}" y="${by - 5}" width="18" height="10" rx="1" fill="${INK}"/>`;
  s += T(bx, by + 28, '86%', { s: 9, w: 600, ls: 1, fam: MONO });
  // bluetooth
  const tx = C, ty = 150;
  s += `<path d="M${tx - 7} ${ty - 8} L${tx + 7} ${ty + 8} L${tx} ${ty + 14} L${tx} ${ty - 14} L${tx + 7} ${ty - 8} L${tx - 7} ${ty + 8}" fill="none" stroke="${INK}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>`;
  s += T(tx, ty + 28, 'LINK', { s: 9, w: 600, ls: 1, fam: MONO });
  // sync
  const sx = C + 70, sy = 150;
  s += `<path d="${gArc(sx, sy, 11, 30, 300)}" fill="none" stroke="${INK}" stroke-width="1.5"/>`;
  const [ax, ay] = gP(sx, sy, 11, 300);
  s += `<path d="M${f(ax - 4)} ${f(ay - 1)} L${f(ax)} ${f(ay + 4)} L${f(ax + 4)} ${f(ay - 2)}" fill="none" stroke="${INK}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>`;
  s += T(sx, sy + 28, 'SYNC', { s: 9, w: 600, ls: 1, fam: MONO });
  s += botLabel('e9b', 'BATTERY &#183; BT &#183; SYNC', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E10 — Notification badge */
function E10() {
  let s = ring(176, 1, '1 6');
  s += topLabel('e10t', 'BADGE', { s: 9, w: 600, ls: 9, fam: MONO });
  s += bell(C, 150, 26, 1.8);
  s += `<circle cx="${C + 22}" cy="128" r="12" fill="${INK}"/>`;
  s += T(C + 22, 132, '3', { s: 13, w: 700, fam: MONO, fill: PAPER });
  s += T(C, 214, '3 NEW', { s: 14, w: 600, ls: 2, fam: MONO });
  s += T(C, 234, 'one to act on', { s: 9, w: 400, ls: 1, fam: MONO });
  s += botLabel('e10b', 'COUNT CHIP &#183; INK FILL', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* E11 — Dot / heat legend */
function E11() {
  let s = ring(176, 1, '1 6');
  s += topLabel('e11t', 'HEAT LEGEND', { s: 9, w: 600, ls: 4, fam: MONO });
  const rows = [['DONE', 'fill'], ['MISSED', 'ring'], ['TODAY', 'today'], ['FUTURE', 'faint']];
  const cx = C - 48;
  rows.forEach(([lbl, k], i) => {
    const y = 122 + i * 30, cy = y - 3.5;
    if (k === 'fill') s += dot(cx, cy, 6, true);
    if (k === 'ring') s += dot(cx, cy, 6, false, 1.4);
    if (k === 'today') { s += dot(cx, cy, 6, true); s += `<circle cx="${f(cx)}" cy="${f(cy)}" r="10" fill="none" stroke="${INK}" stroke-width="1.2"/>`; }
    if (k === 'faint') s += `<circle cx="${f(cx)}" cy="${f(cy)}" r="6" fill="none" stroke="${INK}" stroke-width="0.8" stroke-dasharray="1.5 2.5"/>`;
    s += T(cx + 22, y, lbl, { s: 11, w: 500, ls: 1, fam: MONO, a: 'start' });
  });
  s += botLabel('e11b', 'FILL / RING / RING+RING / DASH', { s: 7.5, ls: 1.5, fam: MONO });
  return frame(MONO, s);
}

/* E12 — Type scale (e-ink ramp) */
function E12() {
  let s = topLabel('e12t', 'TYPE SCALE', { s: 9, w: 600, ls: 5, fam: MONO });
  const rows = [
    ['09:14', 40, 600, 'HERO'],
    ['Finish the deck', 19, 500, 'TITLE'],
    ['Two lines of body text', 12, 400, 'BODY'],
    ['LABEL &#183; META', 8.5, 600, 'CAPS'],
  ];
  let y = 124;
  rows.forEach(([str, sz, w, tag]) => {
    s += T(C, y, str, { s: sz, w, fam: MONO, ls: sz > 30 ? -1 : .3 });
    s += T(C, y + 13, tag + ' &#183; ' + sz + 'PX', { s: 7.5, w: 500, ls: 2, fam: MONO, op: .55 });
    y += sz > 30 ? 46 : 34;
  });
  s += botLabel('e12b', 'ONE RAMP &#183; INK ON PAPER', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* ============================================================
   SECTION F — MORE HOME & GLANCES  (mixed house styles)
   ============================================================ */

/* F1 — Agenda timeline (Orbital) */
function F1() {
  let s = ring(176, 1, '1 6');
  s += topLabel('f1t', 'NEXT UP', { s: 9, w: 600, ls: 8, fam: GEO });
  const ev = [['09:30', 'Standup', 1], ['11:00', 'Design review', 0], ['14:00', '1:1 Sam', 0]];
  const lx = C - 56;
  s += `<line x1="${lx}" y1="108" x2="${lx}" y2="232" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`;
  ev.forEach(([t, name, now], i) => {
    const y = 122 + i * 44;
    s += dot(lx, y - 4, now ? 5 : 3.5, !!now, 1.3);
    if (now) s += `<circle cx="${f(lx)}" cy="${f(y - 4)}" r="9" fill="none" stroke="${INK}" stroke-width="1"/>`;
    s += T(lx + 18, y - 6, t, { s: 9, w: 600, ls: 1, fam: GEO, a: 'start', op: .65 });
    s += T(lx + 18, y + 9, name, { s: 14, w: 500, fam: GEO, a: 'start' });
  });
  s += botLabel('f1b', 'STANDUP IN 12 MIN', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* F2 — Date / first glance (Minimal) */
function F2() {
  let s = `<line x1="${C}" y1="22" x2="${C}" y2="32" stroke="${INK}" stroke-width="1.4"/>`;
  s += T(C, 150, 'Thursday', { s: 30, w: 300, fam: SORA, ls: -.5 });
  s += T(C, 188, '12', { s: 64, w: 200, fam: SORA, ls: -2 });
  s += T(C, 218, 'JUNE', { s: 12, w: 400, ls: 8, fam: SORA });
  s += `<line x1="${C - 24}" y1="244" x2="${C + 24}" y2="244" stroke="${INK}" stroke-width="1"/>`;
  s += T(C, 268, 'first thing &#183; 16k long run', { s: 10.5, w: 300, ls: 1, fam: SORA });
  return frame(SORA, s);
}

/* F3 — Now playing (Orbital) */
function F3() {
  let s = ring(176, 1, '1 5');
  const end = 360 * 0.42;
  s += `<path d="${arc(160, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 5"/>`;
  s += `<path d="${arc(160, 0, end)}" fill="none" stroke="${INK}" stroke-width="3" stroke-linecap="round"/>`;
  const [ex, ey] = P(160, end);
  s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="4" fill="${INK}"/>`;
  s += topLabel('f3t', 'NOW PLAYING', { s: 9, w: 600, ls: 5, fam: GEO });
  // play glyph
  s += `<path d="M${C - 6} 116 L${C + 9} 125 L${C - 6} 134 Z" fill="${INK}"/>`;
  s += T(C, 166, 'Weightless', { s: 22, w: 500, fam: GEO });
  s += T(C, 188, 'Marconi Union', { s: 11, w: 400, ls: 1, fam: GEO });
  s += T(C, 216, '3:08  /  7:24', { s: 10, w: 400, ls: 1, fam: GEO });
  s += botLabel('f3b', 'TAP PAUSE &#183; SWIPE NEXT', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* F4 — Stopwatch / timer (Terminal) */
function F4() {
  let s = ticks(176, 60, 5, 4, 9);
  s += topLabel('f4t', 'STOPWATCH', { s: 8.5, w: 600, ls: 4, fam: MONO });
  const deg = 360 * (37 / 60);
  s += `<path d="${arc(160, 0, deg)}" fill="none" stroke="${INK}" stroke-width="4" stroke-linecap="round"/>`;
  const [ex, ey] = P(160, deg);
  s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="4" fill="${PAPER}" stroke="${INK}" stroke-width="1.8"/>`;
  s += T(C, 172, '02:37', { s: 50, w: 600, ls: -1, fam: MONO });
  s += T(C, 200, 'LAP 3', { s: 10, w: 500, ls: 3, fam: MONO });
  s += T(C, 224, '01:58 &#183; 02:04 &#183; 02:37', { s: 8.5, w: 400, ls: .5, fam: MONO, op: .7 });
  s += botLabel('f4b', 'TAP LAP &#183; HOLD STOP', { s: 8, ls: 2, fam: MONO });
  return frame(MONO, s);
}

/* F5 — Two timezones (Orbital) */
function F5() {
  let s = ring(176, 1, '1 6') + ring(118, 0.8, '1 5');
  s += topLabel('f5t', 'WORLD CLOCK', { s: 9, w: 600, ls: 5, fam: GEO });
  s += `<line x1="${C - 64}" y1="${C}" x2="${C + 64}" y2="${C}" stroke="${INK}" stroke-width="0.8" stroke-dasharray="1.5 4"/>`;
  s += T(C, 138, '14:08', { s: 34, w: 500, fam: GEO, ls: -1 });
  s += T(C, 158, 'LONDON &#183; NOW', { s: 8.5, w: 600, ls: 3, fam: GEO });
  s += T(C, 210, '09:08', { s: 30, w: 400, fam: GEO, ls: -1, op: .8 });
  s += T(C, 230, 'NEW YORK &#183; -5H', { s: 8.5, w: 600, ls: 3, fam: GEO, op: .8 });
  s += botLabel('f5b', 'SAM AWAKE IN 1H', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* F6 — Month mini-grid (Minimal) */
function F6() {
  let s = T(C, 70, 'JUNE 2026', { s: 11, w: 500, ls: 6, fam: SORA });
  const cols = 7, rows = 5, gx0 = 116, gy0 = 108, dx = 21, dy = 21;
  const days = ['m', 't', 'w', 't', 'f', 's', 's'];
  for (let c = 0; c < cols; c++) s += T(gx0 + c * dx, gy0 - 14, days[c], { s: 8, w: 300, fam: SORA, op: .6 });
  const today = 11; // 0-indexed cell of the 12th (starts Mon=cell0 → day1=cell0)
  let day = 1;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const cell = r * cols + c;
    if (cell < 30) {
      const x = gx0 + c * dx, y = gy0 + r * dy;
      const isToday = cell === today;
      if (isToday) s += `<circle cx="${f(x)}" cy="${f(y - 3)}" r="9" fill="${INK}"/>`;
      s += T(x, y, String(day), { s: 9.5, w: isToday ? 500 : 300, fam: SORA, fill: isToday ? PAPER : INK });
      day++;
    }
  }
  s += T(C, 270, 'today &#183; 3 events', { s: 10.5, w: 300, ls: 2, fam: SORA });
  return frame(SORA, s);
}

/* ============================================================
   DATA + RENDER
   ============================================================ */
const gallerySections = [
  {
    badge: 'D', name: 'Tasks & Lists', font: 'Space Grotesk',
    phil: 'The to-do, the only feed a calm object should hold. <b>Ring-checkboxes, a progress arc on the rim, done items dim and strike.</b> Each list is one glanceable state — what is left, what is next, what is overdue.',
    screens: [
      { id: 'D1', name: 'Today', svg: D1, note: 'Six tasks, mixed states — done strike through, the active one carries a filled dot. A 2-of-6 arc tracks the day on the rim.', reads: ['Tasks', 'Active', 'Progress'] },
      { id: 'D2', name: 'Grouped', svg: D2, note: 'Tasks split into Morning and Afternoon headers so the list reads as a shape of the day, not a flat pile.', reads: ['Morning', 'Afternoon', 'Next'] },
      { id: 'D3', name: 'All Done', svg: D3, note: 'Inbox-zero state: a full progress ring, a centred check and a scatter of stars. Reward without a feed.', reads: ['Done', 'Count', 'Empty'] },
      { id: 'D4', name: 'Priority', svg: D4, note: 'One task named large with its subtasks beneath; a depleting arc counts down to the 17:00 deadline.', reads: ['Task', 'Subtasks', 'Due'] },
      { id: 'D5', name: 'Groceries', svg: D5, note: 'A shopping list as the same checklist grammar — ticked items dim, the rim arc shows the basket filling.', reads: ['Items', 'Got', 'Left'] },
      { id: 'D6', name: 'Packing', svg: D6, note: 'Packed-vs-remaining as a counted dot row plus a hero fraction; next items and the departure cue sit beneath.', reads: ['Packed', 'Dots', 'Leave by'] },
      { id: 'D7', name: 'Errands', svg: D7, note: 'Errands with dotted-leader times, like a manifest. The done one strikes; the rest read top-to-bottom.', reads: ['Errand', 'Time', 'Done'] },
      { id: 'D8', name: 'Routine', svg: D8, note: 'A daily ritual checklist with a streak on the base — habit and to-do share one component.', reads: ['Steps', 'Done', 'Streak'] },
      { id: 'D9', name: 'Reminders', svg: D9, note: 'Time-bound reminders under a bell — who and when, calm and stacked, one to act on first.', reads: ['What', 'When', 'Snooze'] },
      { id: 'D10', name: 'Overdue', svg: D10, note: 'The alert state: a dashed warning frame and red-ringed overdue items pushed to the top of the list.', reads: ['Overdue', 'Now', 'Clear'] },
    ],
  },
  {
    badge: 'E', name: 'Components', font: 'JetBrains Mono',
    phil: 'The kit the screens are built from. <b>Each disc is one component family with its states</b> — selection, progress, toggles, steppers, buttons, gauges, badges. The 1-bit vocabulary, isolated and labelled like a spec.',
    screens: [
      { id: 'E1', name: 'Selection', svg: E1, note: 'Ring-checkbox states: empty, checked, active dot and a dashed disabled. The atom every list is built from.', reads: ['Empty', 'Checked', 'Disabled'] },
      { id: 'E2', name: 'Progress Arc', svg: E2, note: 'The progress arc at 25 / 50 / 75 / 100 — dotted track, solid round-capped fill. One primitive, four fills.', reads: ['Track', 'Fill', 'Steps'] },
      { id: 'E3', name: 'Toggle', svg: E3, note: 'A pill switch off and on — dashed + hollow knob for off, solid + filled for on. No colour needed to read state.', reads: ['Off', 'On', 'Knob'] },
      { id: 'E4', name: 'Stepper', svg: E4, note: 'Minus / value / plus for any count. The number is the hero; the controls flank it as outline circles.', reads: ['Minus', 'Value', 'Plus'] },
      { id: 'E5', name: 'Actions', svg: E5, note: 'Button language: solid tap, dashed hold-to-confirm, dimmed disabled. Bracketed, monospace, instrument-like.', reads: ['Tap', 'Hold', 'Off'] },
      { id: 'E6', name: 'Gauge', svg: E6, note: 'The perimeter tick-gauge with a centre pointer — the Terminal house dial, shown bare with its 60 ticks.', reads: ['Ticks', 'Pointer', 'Value'] },
      { id: 'E7', name: 'Segmented', svg: E7, note: 'A range switch riding the rim — the active segment is a heavy arc, the rest hairline. Day / Week / Month.', reads: ['Segments', 'Active', 'Arc'] },
      { id: 'E8', name: 'Slider', svg: E8, note: 'A value dragged along an arc track with a paper knob. Brightness, volume, any 0–100 setting in the round.', reads: ['Track', 'Knob', 'Value'] },
      { id: 'E9', name: 'Status', svg: E9, note: 'System glyphs — battery, link, sync — drawn from the same line weight so the status row reads as one set.', reads: ['Battery', 'Link', 'Sync'] },
      { id: 'E10', name: 'Badge', svg: E10, note: 'A count chip on the bell — the only solid-ink fill in the kit, reserved for "act on this".', reads: ['Bell', 'Count', 'Fill'] },
      { id: 'E11', name: 'Heat Legend', svg: E11, note: 'How the heatmaps read: filled = done, ring = missed, ringed-ring = today, dashed = future. The key in one place.', reads: ['Done', 'Missed', 'Today'] },
      { id: 'E12', name: 'Type Scale', svg: E12, note: 'One ramp — hero, title, body, caps — that every screen draws from. Ink on paper, no second weight of grey.', reads: ['Hero', 'Body', 'Caps'] },
    ],
  },
  {
    badge: 'F', name: 'More Home & Glances', font: 'Mixed houses',
    phil: 'A few more first-glance states across the three houses — agenda, date, media, timer, world clock, calendar. <b>Proof the grammar stretches</b> past goals and habits to the everyday glances a desk object holds.',
    screens: [
      { id: 'F1', name: 'Agenda', svg: F1, note: 'The next three events on a dotted spine; the current one is ringed. A timeline, not a list. (Orbital)', reads: ['Now', 'Next', 'After'] },
      { id: 'F2', name: 'Date Glance', svg: F2, note: 'Weekday and date set like a page, with the first thing of the day whispered below. (Minimal)', reads: ['Day', 'Date', 'First'] },
      { id: 'F3', name: 'Now Playing', svg: F3, note: 'A track with a perimeter scrubber and a play glyph — ambient audio control in the round. (Orbital)', reads: ['Track', 'Scrub', 'Controls'] },
      { id: 'F4', name: 'Stopwatch', svg: F4, note: 'Seconds sweep the tick-gauge while laps stack beneath the big monospace time. (Terminal)', reads: ['Time', 'Sweep', 'Laps'] },
      { id: 'F5', name: 'World Clock', svg: F5, note: 'Two timezones split across a hairline — home now up top, a second city dimmed below. (Orbital)', reads: ['Home', 'Away', 'Offset'] },
      { id: 'F6', name: 'Month', svg: F6, note: 'A whole month as a quiet dot-grid of dates, today inked solid. Maximal air. (Minimal)', reads: ['Grid', 'Today', 'Events'] },
    ],
  },
];

(function renderGallery() {
  const main = document.getElementById('main');
  gallerySections.forEach(d => {
    const sec = document.createElement('section');
    sec.className = 'dir';
    let cards = '';
    d.screens.forEach(sc => {
      const reads = sc.reads.map((r, j) => `<span><i>${j + 1}</i><b>${r}</b></span>`).join('');
      cards += `<figure class="card">
        <div class="statelabel"><span class="num">${sc.id}</span><span class="nm">${sc.name}</span></div>
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
})();
