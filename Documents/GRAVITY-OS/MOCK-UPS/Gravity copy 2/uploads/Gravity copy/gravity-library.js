/* ============================================================
   GRAVITY — Extended Library  (rev 0.5)
   More use-cases in the curved "globe" grammar. Loads after
   gravity-build.js and reuses its globals (P, arc, T, ring,
   dot, topLabel, botLabel, moon, star, frame, GEO, INK, ...).
   ============================================================ */

/* shared progress arc with endpoint node ------------------- */
function progArc(r, pct, sw = 5) {
  const end = 360 * pct, [ex, ey] = P(r, end);
  return `<path d="${arc(r, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`
    + `<path d="${arc(r, 0, end)}" fill="none" stroke="${INK}" stroke-width="${sw}" stroke-linecap="round"/>`
    + `<circle cx="${f(ex)}" cy="${f(ey)}" r="4.2" fill="${PAPER}" stroke="${INK}" stroke-width="2"/>`;
}

/* outline glyphs (no fills) -------------------------------- */
function tri(cx, cy, s, sw = 1.8) {
  const h = s * 0.92;
  return `<path d="M${f(cx)} ${f(cy - h * 0.62)} L${f(cx + s / 2)} ${f(cy + h * 0.5)} L${f(cx - s / 2)} ${f(cy + h * 0.5)} Z" fill="none" stroke="${INK}" stroke-width="${sw}" stroke-linejoin="round"/>`
    + `<line x1="${f(cx)}" y1="${f(cy - h * 0.12)}" x2="${f(cx)}" y2="${f(cy + h * 0.18)}" stroke="${INK}" stroke-width="${sw}" stroke-linecap="round"/>`
    + `<circle cx="${f(cx)}" cy="${f(cy + h * 0.36)}" r="${sw * 0.85}" fill="${INK}"/>`;
}
function bell(cx, cy, s, sw = 1.5) {
  return `<path d="M${f(cx)} ${f(cy - s)} C${f(cx - s * 0.85)} ${f(cy - s * 0.6)} ${f(cx - s * 0.72)} ${f(cy)} ${f(cx - s * 0.82)} ${f(cy + s * 0.42)} L${f(cx + s * 0.82)} ${f(cy + s * 0.42)} C${f(cx + s * 0.72)} ${f(cy)} ${f(cx + s * 0.85)} ${f(cy - s * 0.6)} ${f(cx)} ${f(cy - s)} Z" fill="none" stroke="${INK}" stroke-width="${sw}" stroke-linejoin="round"/>`
    + `<path d="M${f(cx - s * 0.22)} ${f(cy + s * 0.42)} a${f(s * 0.22)} ${f(s * 0.22)} 0 0 0 ${f(s * 0.44)} 0" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
}
function droplet(cx, cy, s, sw = 1.6) {
  return `<path d="M${f(cx)} ${f(cy - s)} C${f(cx + s * 0.92)} ${f(cy + s * 0.25)} ${f(cx + s * 0.55)} ${f(cy + s)} ${f(cx)} ${f(cy + s)} C${f(cx - s * 0.55)} ${f(cy + s)} ${f(cx - s * 0.92)} ${f(cy + s * 0.25)} ${f(cx)} ${f(cy - s)} Z" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
}
function sun(cx, cy, r, sw = 1.5) {
  let s = `<circle cx="${f(cx)}" cy="${f(cy)}" r="${r}" fill="none" stroke="${INK}" stroke-width="${sw}"/>`;
  for (let i = 0; i < 8; i++) {
    const a = i * 45 * RAD;
    s += `<line x1="${f(cx + Math.cos(a) * (r + 3.5))}" y1="${f(cy + Math.sin(a) * (r + 3.5))}" x2="${f(cx + Math.cos(a) * (r + 8))}" y2="${f(cy + Math.sin(a) * (r + 8))}" stroke="${INK}" stroke-width="${sw}" stroke-linecap="round"/>`;
  }
  return s;
}
function check(cx, cy, k = 2.6, sw = 1.4) {
  return `<path d="M${f(cx - k)} ${f(cy)} l${f(k * 0.75)} ${f(k * 0.85)} l${f(k * 1.35)} -${f(k * 1.6)}" fill="none" stroke="${INK}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round"/>`;
}

/* ---- L1  Savings goal ---- */
function L1() {
  let s = progArc(158, 0.68);
  s += topLabel('l1t', 'SAVINGS &#183; EMERGENCY FUND', { s: 8.5, w: 600, ls: 3, fam: GEO });
  s += T(C, 172, '&#163;6,800', { s: 46, w: 500, fam: GEO, ls: -1 });
  s += T(C, 198, 'of &#163;10,000 goal', { s: 11, w: 400, ls: 1, fam: GEO });
  s += T(C, 224, '68% saved', { s: 11.5, w: 600, ls: 1, fam: GEO });
  s += botLabel('l1b', '+&#163;400 / MO &#183; ON TRACK FOR DEC', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L2  Investment goal (allocation ring) ---- */
function L2() {
  let s = `<path d="${arc(158, 3, 213)}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round"/>`;
  s += `<path d="${arc(158, 219, 321)}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round" stroke-dasharray="2.5 4"/>`;
  s += `<path d="${arc(158, 327, 354)}" fill="none" stroke="${INK}" stroke-width="5" stroke-linecap="round" stroke-dasharray="0.5 4"/>`;
  s += topLabel('l2t', 'PORTFOLIO', { s: 9, w: 600, ls: 7, fam: GEO });
  s += T(C, 168, '&#163;42,180', { s: 42, w: 500, fam: GEO, ls: -1 });
  s += T(C, 194, '&#9650; 2.4% today', { s: 12.5, w: 500, ls: .5, fam: GEO });
  s += T(C, 222, 'STOCKS 60 &#183; BONDS 30 &#183; CASH 10', { s: 8, w: 500, ls: .8, fam: GEO });
  s += botLabel('l2b', 'GOAL &#163;100K &#183; ~7 YEARS', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L3  Study goal ---- */
function L3() {
  let s = progArc(158, 0.72);
  s += topLabel('l3t', 'STUDY &#183; SPANISH', { s: 8.5, w: 600, ls: 4, fam: GEO });
  s += T(C, 168, '72%', { s: 48, w: 500, fam: GEO, ls: -1 });
  s += T(C, 194, 'to level B2', { s: 11.5, w: 400, ls: 1, fam: GEO });
  s += T(C, 222, 'Lesson 14 of 20', { s: 11, w: 400, ls: .5, fam: GEO });
  s += botLabel('l3b', 'STREAK 23 DAYS &#183; NEXT 18:00', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L4  Physical activity (3 rings) ---- */
function L4() {
  let s = '';
  [[158, 0.84], [134, 0.62], [110, 0.90]].forEach(([r, p]) => {
    const end = 360 * p, [ex, ey] = P(r, end);
    s += `<path d="${arc(r, 0, 359.9)}" fill="none" stroke="${INK}" stroke-width="1" stroke-dasharray="1.5 4"/>`;
    s += `<path d="${arc(r, 0, end)}" fill="none" stroke="${INK}" stroke-width="4" stroke-linecap="round"/>`;
    s += `<circle cx="${f(ex)}" cy="${f(ey)}" r="3.4" fill="${PAPER}" stroke="${INK}" stroke-width="1.6"/>`;
  });
  s += T(C, 170, '8,420', { s: 38, w: 500, fam: GEO, ls: -1 });
  s += T(C, 194, 'of 10,000 steps', { s: 10.5, w: 400, ls: 1, fam: GEO });
  s += T(C, 30, 'STEPS', { s: 7, w: 600, ls: 2, fam: GEO });
  s += T(C, 54, 'MOVE', { s: 7, w: 600, ls: 2, fam: GEO });
  s += T(C, 78, 'STAND', { s: 7, w: 600, ls: 2, fam: GEO });
  s += botLabel('l4b', 'EXERCISE 28 / 45 MIN', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L5  Warning ---- */
function L5() {
  let s = ring(176, 1.4, '3 4') + ring(170, 0.7, '1.5 5');
  s += topLabel('l5t', '! WEATHER WARNING', { s: 9.5, w: 700, ls: 3, fam: GEO });
  s += tri(C, 110, 42, 2);
  s += T(C, 174, 'Storm front', { s: 24, w: 500, fam: GEO });
  s += T(C, 202, 'moving in at 18:00', { s: 13, w: 400, ls: .5, fam: GEO });
  s += T(C, 228, 'Bring your run forward.', { s: 11.5, w: 400, ls: .3, fam: GEO });
  s += botLabel('l5b', 'TAP FOR DETAIL', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L6  Notification ---- */
function L6() {
  let s = ring(176, 1, '1 5');
  s += topLabel('l6t', 'REMINDER', { s: 9, w: 600, ls: 8, fam: GEO });
  s += bell(C, 108, 19, 1.6);
  s += T(C, 176, 'Call Mum', { s: 27, w: 500, fam: GEO });
  s += T(C, 204, 'in 30 min &#183; 18:00', { s: 12.5, w: 400, ls: 1, fam: GEO });
  s += botLabel('l6b', 'TAP SNOOZE &#183; SWIPE DONE', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L7  To-do list ---- */
function L7() {
  let s = progArc(158, 0.4, 4);
  s += topLabel('l7t', 'TODAY &#183; 5 TASKS', { s: 8.5, w: 600, ls: 3, fam: GEO });
  const items = [['Standup notes', 1], ['Reply to Sam', 1], ['Q3 roadmap deck', 0], ['Gym at 18:00', 0], ['Book flights', 0]];
  const cx = C - 70;
  items.forEach(([t, done], i) => {
    const y = 128 + i * 23;
    s += `<circle cx="${cx}" cy="${y - 3.5}" r="5" fill="none" stroke="${INK}" stroke-width="1.2"/>`;
    if (done) s += check(cx, y - 3.5, 2.6, 1.3);
    s += T(cx + 14, y, t, { s: 11.5, w: done ? 400 : 500, ls: .2, fam: GEO, a: 'start', op: done ? .55 : 1, style: done ? 'text-decoration:line-through' : '' });
  });
  s += botLabel('l7b', '2 OF 5 DONE', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L8  Reading goal ---- */
function L8() {
  let s = progArc(158, 0.6);
  s += topLabel('l8t', 'READING &#183; 2026', { s: 8.5, w: 600, ls: 4, fam: GEO });
  s += T(C, 170, '18 / 30', { s: 42, w: 500, fam: GEO, ls: -1 });
  s += T(C, 195, 'books this year', { s: 10.5, w: 400, ls: 1, fam: GEO });
  s += T(C, 222, 'Now: The Overstory &#183; 64%', { s: 10, w: 400, ls: .2, fam: GEO });
  s += botLabel('l8b', 'AHEAD BY 2 BOOKS', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L9  Hydration ---- */
function L9() {
  let s = ring(176, 1, '1 6');
  s += topLabel('l9t', 'HYDRATION', { s: 9, w: 600, ls: 7, fam: GEO });
  s += droplet(C, 100, 18, 1.7);
  s += T(C, 178, '5 / 8', { s: 44, w: 500, fam: GEO, ls: -1 });
  s += T(C, 203, 'glasses today', { s: 10.5, w: 400, ls: 1, fam: GEO });
  for (let i = 0; i < 8; i++) {
    const [x, y] = P(132, 180 - 42 + i * (84 / 7));
    s += dot(x, y, 4.2, i < 5, 1.3);
  }
  s += botLabel('l9b', '3 GLASSES TO GO', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L10  Sleep score ---- */
function L10() {
  let s = progArc(158, 0.82);
  s += topLabel('l10t', 'LAST NIGHT', { s: 9, w: 600, ls: 7, fam: GEO });
  s += moon(C, 100, 15, 1.5);
  s += star(C - 26, 90, 1.8) + star(C + 26, 104, 2.2);
  s += T(C, 178, '7h 12m', { s: 38, w: 500, fam: GEO, ls: -1 });
  s += T(C, 203, 'sleep score 82', { s: 11, w: 400, ls: 1, fam: GEO });
  s += botLabel('l10b', 'BED 23:18 &#183; WAKE 06:30', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L11  Meditation / breathe ---- */
function L11() {
  let s = '';
  [152, 116, 80].forEach(r => s += ring(r, 1, '1 5'));
  s += ring(50, 1.5);
  s += T(C, 174, '12 min', { s: 28, w: 500, fam: GEO });
  s += T(C, 198, 'today', { s: 11, w: 400, ls: 3, fam: GEO });
  s += topLabel('l11t', 'BREATHE', { s: 9, w: 600, ls: 9, fam: GEO });
  s += botLabel('l11b', 'STREAK 9 DAYS', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L12  Next meeting ---- */
function L12() {
  let s = progArc(158, 0.5, 4);
  s += topLabel('l12t', 'UP NEXT', { s: 9, w: 600, ls: 8, fam: GEO });
  s += T(C, 162, 'Standup', { s: 28, w: 500, fam: GEO });
  s += T(C, 190, '10:00 &#183; in 12 min', { s: 13, w: 400, ls: .5, fam: GEO });
  s += T(C, 216, 'Design team &#183; Room 2', { s: 10, w: 400, ls: .3, fam: GEO });
  s += botLabel('l12b', 'THEN 11:30 &#183; 1:1 W/ SAM', { s: 8.5, ls: 2, fam: GEO });
  return frame(GEO, s);
}

/* ---- L13  Weather glance ---- */
function L13() {
  let s = ring(176, 1, '1 6');
  s += topLabel('l13t', 'TODAY &#183; LONDON', { s: 8.5, w: 600, ls: 4, fam: GEO });
  s += sun(C, 104, 16, 1.5);
  s += T(C, 182, '14&#176;', { s: 54, w: 400, fam: GEO, ls: -1 });
  s += T(C, 208, 'Partly cloudy', { s: 12, w: 400, ls: 1, fam: GEO });
  s += T(C, 232, 'H 17&#176;   L 9&#176;   &#183;   Rain 40%', { s: 10, w: 400, ls: .3, fam: GEO });
  s += botLabel('l13b', 'RAIN FROM 18:00', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L14  Commute / transit ---- */
function L14() {
  let s = ring(176, 1, '1 6');
  s += topLabel('l14t', 'COMMUTE', { s: 9, w: 600, ls: 8, fam: GEO });
  // mini line with stops
  s += `<line x1="${C - 52}" y1="112" x2="${C + 52}" y2="112" stroke="${INK}" stroke-width="1.6"/>`;
  [-52, -17, 18, 52].forEach((dx, i) => s += dot(C + dx, 112, i === 1 ? 5 : 3.5, i === 0, 1.3));
  s += T(C, 172, '6 min', { s: 42, w: 500, fam: GEO, ls: -1 });
  s += T(C, 197, 'to next train', { s: 11, w: 400, ls: 1, fam: GEO });
  s += T(C, 223, 'Northern &#183; Southbound', { s: 10, w: 400, ls: .3, fam: GEO });
  s += botLabel('l14b', 'LEAVE BY 08:42', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L15  Single habit streak ---- */
function L15() {
  let s = progArc(158, 23 / 31, 5);
  s += topLabel('l15t', 'NO PHONE BEFORE NOON', { s: 8, w: 600, ls: 2.5, fam: GEO });
  s += T(C, 170, '23', { s: 60, w: 500, fam: GEO, ls: -1 });
  s += T(C, 198, 'day streak', { s: 11, w: 400, ls: 2, fam: GEO });
  for (let i = 0; i < 7; i++) {
    const [x, y] = P(130, 180 - 36 + i * (72 / 6));
    s += dot(x, y, 4, true, 1.2);
  }
  s += botLabel('l15b', 'BEST 31 DAYS', { s: 8.5, ls: 3, fam: GEO });
  return frame(GEO, s);
}

/* ---- L16  Budget remaining ---- */
function L16() {
  let s = progArc(158, 0.65, 4);
  s += topLabel('l16t', 'BUDGET &#183; JUNE', { s: 8.5, w: 600, ls: 4, fam: GEO });
  s += T(C, 170, '&#163;420', { s: 46, w: 500, fam: GEO, ls: -1 });
  s += T(C, 195, 'left of &#163;1,200', { s: 11, w: 400, ls: 1, fam: GEO });
  s += T(C, 222, '&#163;35 / day for 12 days', { s: 10, w: 400, ls: .3, fam: GEO });
  s += botLabel('l16b', 'DINING &#163;180 &#183; TRANSPORT &#163;90', { s: 8, ls: 1.5, fam: GEO });
  return frame(GEO, s);
}

/* ---- data + render ---- */
const libDir = {
  badge: 'L', name: 'Library · More Use-Cases', font: 'Space Grotesk',
  phil: 'The same circular grammar applied across the goals and glances a desk object actually holds. <b>One clear idea per circle — dominant centre, supporting ring, curved rim for context.</b> Built in the Orbital house style so they read as one family.',
  screens: [
    { id: 'L1', name: 'Savings Goal', svg: L1, note: 'Perimeter arc tracks the fund to 68%; the pound figure is the hero, the target and monthly pace support it.', reads: ['Amount', 'Target', 'Pace'] },
    { id: 'L2', name: 'Investment Goal', svg: L2, note: 'The rim splits into an allocation ring — solid stocks, dashed bonds, dotted cash. Value and today\'s move sit at the core.', reads: ['Value', 'Change', 'Mix'] },
    { id: 'L3', name: 'Study Goal', svg: L3, note: 'Fluency-to-next-level as a single big arc. Percentage leads; current lesson and streak follow.', reads: ['Progress', 'Lesson', 'Streak'] },
    { id: 'L4', name: 'Activity Rings', svg: L4, note: 'Three outline rings — steps, move, stand — keyed up top. Steps is the headline number at the calm centre.', reads: ['Steps', 'Rings', 'Exercise'] },
    { id: 'L5', name: 'Warning', svg: L5, note: 'A stark, dashed alert frame and a warning glyph. The threat and the suggested action read in one glance.', reads: ['Warning', 'What', 'Action'] },
    { id: 'L6', name: 'Notification', svg: L6, note: 'A single incoming reminder — bell glyph, who, and when. Calm, not a feed; one thing to act on.', reads: ['Who', 'When', 'Action'] },
    { id: 'L7', name: 'To-do List', svg: L7, note: 'Five tasks with ring-checkboxes; done items dim and strike through. A 40% arc on the rim shows progress.', reads: ['Tasks', 'Done', 'Progress'] },
    { id: 'L8', name: 'Reading Goal', svg: L8, note: 'Books-this-year as the hero count with a progress arc; the current title and its progress sit beneath.', reads: ['Count', 'Pace', 'Current'] },
    { id: 'L9', name: 'Hydration', svg: L9, note: 'Glasses as a counted arc of dots — filled = drunk. The fraction and droplet make it instantly legible.', reads: ['Count', 'Glasses', 'To go'] },
    { id: 'L10', name: 'Sleep Score', svg: L10, note: 'Last night\'s duration is the hero; the score rides the perimeter; bed and wake times curve along the base.', reads: ['Duration', 'Score', 'Window'] },
    { id: 'L11', name: 'Meditation', svg: L11, note: 'Concentric calm rings around a quiet core — minutes today at centre, streak on the rim. A breathing motif.', reads: ['Minutes', 'Today', 'Streak'] },
    { id: 'L12', name: 'Next Meeting', svg: L12, note: 'The next event named large, with its time and countdown; a half-arc visualises time remaining.', reads: ['Event', 'When', 'After'] },
    { id: 'L13', name: 'Weather', svg: L13, note: 'A geometric sun glyph and a single big temperature. Hi/lo and rain chance read second, timing third.', reads: ['Temp', 'Condition', 'Timing'] },
    { id: 'L14', name: 'Commute', svg: L14, note: 'Minutes-to-next-train as the hero, with a mini line-and-stops motif and the route. Leave-by on the base.', reads: ['Minutes', 'Line', 'Leave by'] },
    { id: 'L15', name: 'Habit Streak', svg: L15, note: 'A single habit as one big number and an arc toward your best; the last seven days dot along the lower rim.', reads: ['Streak', 'Last 7', 'Best'] },
    { id: 'L16', name: 'Budget', svg: L16, note: 'Money-left is the hero; a 65%-spent arc frames it; daily allowance and top categories give context.', reads: ['Left', 'Spent', 'Daily'] },
  ],
};

(function renderLibrary() {
  const d = libDir;
  const sec = document.createElement('section');
  sec.className = 'dir';
  let cards = '';
  d.screens.forEach((sc, i) => {
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
  document.getElementById('main').appendChild(sec);
})();
