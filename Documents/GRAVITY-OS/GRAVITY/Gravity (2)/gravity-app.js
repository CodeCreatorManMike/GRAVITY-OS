/* ============================================================
   GRAVITY — Companion App (iOS)  rev 0.1
   The mobile side of the device: pair it, choose what it shows,
   set goals / habits / tasks, read the nudge log, tune coaching,
   see insights. Dark "mission-control" chrome in the brand's
   three typefaces; wherever it mirrors the device, it renders
   the real e-ink paper disc. Strictly black & white.
   Reuses gravity-disc.js globals.
   ============================================================ */

/* ---- line icons (24x24, currentColor) --------------------- */
const I = {
  home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11 12 4l8 7"/><path d="M6 10v9h12v-9"/></svg>`,
  goal: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.4"/></svg>`,
  tasks: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="7" r="2.4"/><circle cx="6" cy="17" r="2.4"/><path d="M11 7h9M11 17h9"/></svg>`,
  insight: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4 20V10M10 20V5M16 20v-8M22 20H2"/></svg>`,
  gear: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.2"/><path d="M12 3v2.5M12 18.5V21M21 12h-2.5M5.5 12H3M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8M18.4 18.4l-1.8-1.8M7.4 7.4 5.6 5.6"/></svg>`,
  bell: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2.2H4.5L6 16Z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>`,
  bolt: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M13 3 5 13h6l-1 8 8-10h-6l1-8Z"/></svg>`,
  sun: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5V5M12 19v2.5M21.5 12H19M5 12H2.5M18.4 5.6l-1.7 1.7M7.3 16.7l-1.7 1.7M18.4 18.4l-1.7-1.7M7.3 7.3 5.6 5.6"/></svg>`,
  moon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M19 14.5A8 8 0 0 1 9.5 5a7 7 0 1 0 9.5 9.5Z"/></svg>`,
  chev: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>`,
  back: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5 8 12l7 7"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11a8 8 0 1 0-1 5"/><path d="M20 5v6h-6"/></svg>`,
  bt: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M8 7.5 16 16l-4 3.5V4.5L16 8 8 16.5"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/></svg>`,
  run: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="15" cy="5" r="2"/><path d="M9 21l2.5-5L8 13l1-5 4 2 2 3M6 12l3-1M13 13l3 1.5"/></svg>`,
  book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H12v16H6.5A2.5 2.5 0 0 0 4 21.5V5.5Z"/><path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H12v16h5.5a2.5 2.5 0 0 1 2.5 2.5V5.5Z"/></svg>`,
  coin: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><path d="M12 7.5v9M14.5 9.5c-.6-.8-4-1.2-4 .8 0 2 4 1 4 3 0 2-3.4 1.7-4 .8"/></svg>`,
  lang: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.4 2.3 2.4 14.7 0 17M12 3.5c-2.4 2.3-2.4 14.7 0 17"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5 10 17 19 7"/></svg>`,
  wifi: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 9a13 13 0 0 1 16 0M7 12.5a8.5 8.5 0 0 1 10 0M10 16a4 4 0 0 1 4 0"/><circle cx="12" cy="19" r="1" fill="currentColor" stroke="none"/></svg>`,
};

/* ---- status bar + tab bar --------------------------------- */
function statusBar(time = '9:14') {
  return `<div class="app-status">
    <span class="t">${time}</span>
    <span class="sys">
      <svg viewBox="0 0 22 12" class="sg"><rect x="0" y="7" width="3" height="5" rx="1"/><rect x="5" y="5" width="3" height="7" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1" opacity=".35"/></svg>
      <span class="ic">${I.wifi}</span>
      <svg viewBox="0 0 26 13" class="bat"><rect x="0.5" y="0.5" width="21" height="12" rx="3" fill="none" stroke="currentColor"/><rect x="23" y="4" width="2.2" height="5" rx="1"/><rect x="2.2" y="2.2" width="14" height="8.6" rx="1.4"/></svg>
    </span>
  </div>`;
}
function tabBar(active) {
  const tabs = [['home', 'Home', I.home], ['goal', 'Goals', I.goal], ['tasks', 'Tasks', I.tasks], ['insight', 'Insights', I.insight], ['gear', 'Settings', I.gear]];
  return `<nav class="tabbar">${tabs.map(([k, lbl, ic]) => `<span class="tab${k === active ? ' on' : ''}"><span class="ti">${ic}</span><span class="tl">${lbl}</span></span>`).join('')}</nav>`;
}
function navBar(title, { back = true, action = '' } = {}) {
  return `<div class="navbar">${back ? `<span class="nb-back">${I.back}</span>` : '<span></span>'}<span class="nb-title">${title}</span><span class="nb-act">${action}</span></div>`;
}

/* ---- atoms ------------------------------------------------- */
function ring2(pct, size = 54, sw = 4) {
  const r = (size - sw) / 2, c = 2 * Math.PI * r, off = c * (1 - pct);
  return `<svg class="ring2" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="#2a2a30" stroke-width="${sw}"/>
    <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="#e7e6df" stroke-width="${sw}" stroke-linecap="round" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}" transform="rotate(-90 ${size / 2} ${size / 2})"/>
  </svg>`;
}
const seclbl = (t, act = '') => `<div class="seclbl"><span>${t}</span>${act ? `<span class="sl-act">${act}</span>` : ''}</div>`;
const toggle = on => `<span class="tg${on ? ' on' : ''}"><i></i></span>`;
const chip = (t, on) => `<span class="chip${on ? ' on' : ''}">${t}</span>`;
const btn = (t, pr) => `<span class="btn${pr ? ' pr' : ''}">${t}</span>`;
function row(o) {
  const { ic, title, sub, trail, on } = o;
  return `<div class="row${on ? ' tap' : ''}">${ic ? `<span class="ric">${ic}</span>` : ''}<span class="rtx"><b>${title}</b>${sub ? `<i>${sub}</i>` : ''}</span>${trail !== undefined ? `<span class="rtr">${trail}</span>` : ''}</div>`;
}
function taskRow(t, state) {
  const done = state === 'done', active = state === 'active';
  return `<div class="task${done ? ' done' : ''}"><span class="cbx${done ? ' ck' : ''}${active ? ' ac' : ''}">${done ? I.check : ''}</span><span class="tt">${t}</span></div>`;
}
function mirror(face, big) { return `<div class="mirror${big ? ' big' : ''}">${face}</div>`; }
function slider(pct) { return `<div class="slider"><span class="sl-fill" style="width:${pct}%"></span><span class="sl-knob" style="left:${pct}%"></span></div>`; }

/* ============================================================
   SCREENS
   ============================================================ */

/* ---- M · Setup & Device ---- */
function M1() {
  return statusBar('9:14') + `<div class="dev-body center">
    <div class="setup-logo"><svg viewBox="0 0 34 46" fill="none" stroke="#e7e6df" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3 L17 16"/><path d="M9 9 L17 17 L25 9"/><path d="M17 17 C5 26 4 43 17 43 C30 43 29 26 17 17 Z"/><circle cx="17" cy="33" r="3.4" fill="#e7e6df" stroke="none"/></svg></div>
    <div class="pulse">${mirror(faceIdle())}<span class="pulse-ring"></span></div>
    <div class="setup-tx">
      <h1 class="h1">Connect your<br>Gravity</h1>
      <p class="sub">Hold the dial for three seconds until the rim pulses, then keep it close.</p>
    </div>
    <div class="setup-status"><span class="dotpulse"></span>SEARCHING FOR DEVICES…</div>
    <div class="setup-cta">${btn('Pair device', true)}<span class="btn ghost">Enter code manually</span></div>
  </div>`;
}
function M2() {
  return statusBar() + `<div class="dev-body scroll">
    <div class="hello">Good morning, Alex</div>
    ${seclbl('YOUR DEVICE')}
    <div class="devcard">
      ${mirror(faceIdle(), true)}
      <div class="devmeta">
        <b>Gravity</b>
        <span class="lbl">ON SCREEN NOW</span>
        <span class="val">Idle · clock</span>
        <div class="devstat"><span><i>BATTERY</i>86%</span><span><i>SYNCED</i>2m ago</span></div>
      </div>
    </div>
    ${seclbl('QUICK CONTROLS')}
    <div class="qgrid">
      <div class="qc"><span class="qi">${I.sun}</span><b>Brightness</b><i>62%</i></div>
      <div class="qc"><span class="qi">${I.moon}</span><b>Night mode</b><i>Auto</i></div>
      <div class="qc"><span class="qi">${I.bell}</span><b>Nudges</b><i>On</i></div>
      <div class="qc"><span class="qi">${I.refresh}</span><b>Sync now</b><i>Tap</i></div>
    </div>
    ${seclbl('UP NEXT ON DEVICE')}
    ${row({ ic: I.bolt, title: 'Morning brief', sub: 'Switches at 07:30', trail: I.chev })}
    ${row({ ic: I.goal, title: 'Half marathon', sub: 'During your run', trail: I.chev })}
  </div>` + tabBar('home');
}
function M3() {
  return statusBar() + navBar('Display') + `<div class="dev-body scroll pad">
    ${seclbl('BRIGHTNESS')}
    <div class="block"><div class="blk-top"><span>${I.sun}</span><b>62%</b></div>${slider(62)}</div>
    ${seclbl('REFRESH RATE')}
    <div class="segwrap">${chip('Battery', false)}${chip('Balanced', true)}${chip('Crisp', false)}</div>
    <p class="hint">Balanced redraws the e-ink every few seconds — best for glances.</p>
    ${seclbl('NIGHT')}
    ${row({ ic: I.moon, title: 'Night mode', sub: 'Dim the rim after dark', trail: toggle(true) })}
    ${row({ title: 'Schedule', sub: '22:30 – 07:00', trail: I.chev })}
    ${seclbl('PLACEMENT')}
    ${row({ title: 'Tilt calibration', sub: 'Faced 48° · good', trail: I.chev })}
    <div class="cta-row">${btn('Refresh device now', true)}</div>
  </div>`;
}
function M4() {
  const faces = [['Idle', faceIdle, 1], ['Goal', faceGoal, 0], ['Tasks', faceTodo, 0], ['Focus', faceFocus, 0], ['Sleep', faceSleep, 0], ['Weather', faceWeather, 0]];
  return statusBar() + navBar('Faces', { action: I.plus }) + `<div class="dev-body scroll pad">
    <p class="hint top">Choose what your Gravity shows at rest. One idea per circle.</p>
    <div class="facegrid">
      ${faces.map(([n, fn, on]) => `<div class="facecell${on ? ' on' : ''}"><div class="fcdisc">${mirror(fn())}</div><span class="fcname">${n}${on ? `<em>${I.check}</em>` : ''}</span></div>`).join('')}
    </div>
  </div>`;
}

/* ---- N · Goals & Habits ---- */
function N1() {
  const goals = [
    [I.run, 'Half marathon', '94 days left', 0.62],
    [I.book, 'Read 30 books', '18 of 30 this year', 0.60],
    [I.coin, 'Emergency fund', '£6,800 of £10,000', 0.68],
    [I.lang, 'Spanish · B2', 'Lesson 14 of 20', 0.72],
  ];
  return statusBar() + `<div class="dev-body scroll">
    <div class="hello">Goals</div>
    ${seclbl('IN PROGRESS', I.plus)}
    ${goals.map(([ic, t, s, p]) => `<div class="goalrow"><span class="gr-ring">${ring2(p, 48, 4)}<em>${Math.round(p * 100)}</em></span><span class="rtx"><b>${t}</b><i>${s}</i></span><span class="gr-ic">${ic}</span></div>`).join('')}
    <div class="cta-row">${btn('New goal', false)}</div>
  </div>` + tabBar('goal');
}
function N2() {
  return statusBar() + navBar('Half Marathon', { action: I.gear }) + `<div class="dev-body scroll pad">
    <div class="goalhero">
      <span class="gh-ring">${ring2(0.62, 168, 7)}<b>62%</b></span>
      <div class="gh-meta"><span class="lbl">TARGET 21.1 KM</span><span class="val">94 days left</span><span class="sub2">On track · Dec 14</span></div>
    </div>
    ${seclbl('THIS WEEK')}
    ${row({ ic: I.run, title: 'Long run', sub: '16 / 16 km', trail: I.check })}
    ${row({ title: 'Strength', sub: '2 of 3 sessions', trail: '67%' })}
    ${row({ ic: I.moon, title: 'Sleep 7h+', sub: '5 of 7 nights', trail: '71%' })}
    ${seclbl('ON DEVICE')}
    ${row({ ic: I.goal, title: 'Show during runs', sub: 'Mirrors live pace ring', trail: toggle(true) })}
  </div>`;
}
function N3() {
  const habits = [['Move', [1, 0, 1, 1, 1, 1, 1]], ['Read', [1, 1, 0, 1, 1, 0, 1]], ['Focus', [0, 1, 1, 1, 1, 1, 1]], ['Sleep', [1, 1, 1, 0, 1, 1, 1]], ['Calm', [1, 1, 1, 1, 0, 1, 1]]];
  const days = ['S', 'S', 'M', 'T', 'W', 'T', 'F'];
  return statusBar() + navBar('Habits', { action: I.plus }) + `<div class="dev-body scroll pad">
    <div class="heat">
      <div class="heat-days"><span></span>${days.map((d, i) => `<span class="${i === 6 ? 'now' : ''}">${d}</span>`).join('')}</div>
      ${habits.map(([n, w]) => `<div class="heat-row"><span class="hn">${n}</span>${w.map((v, i) => `<span class="cell ${v ? 'fill' : 'miss'}${i === 6 ? ' today' : ''}"></span>`).join('')}</div>`).join('')}
    </div>
    <div class="heat-sum"><b>30 of 35</b><span>done this week · 86%</span></div>
    ${seclbl('STREAKS')}
    ${row({ ic: I.bolt, title: 'No phone before noon', sub: 'Current streak', trail: '23d' })}
    ${row({ ic: I.moon, title: 'Lights out by 22:30', sub: 'Current streak', trail: '9d' })}
  </div>`;
}
function N4() {
  return statusBar() + navBar('New Goal') + `<div class="dev-body scroll pad">
    ${seclbl('WHAT ARE YOU WORKING TOWARD?')}
    <div class="field"><input value="Run a half marathon" readonly><span class="caret"></span></div>
    ${seclbl('HOW TO TRACK IT')}
    <div class="segwrap">${chip('Progress %', true)}${chip('Count', false)}${chip('Streak', false)}</div>
    ${seclbl('TARGET & DEADLINE')}
    <div class="field2"><span>Distance</span><b>21.1 km</b></div>
    <div class="field2"><span>By</span><b>14 Dec 2026</b></div>
    ${seclbl('DEVICE')}
    ${row({ ic: I.goal, title: 'Show on Gravity', sub: 'Add a face for this goal', trail: toggle(true) })}
    <div class="cta-row">${btn('Create goal', true)}</div>
  </div>`;
}

/* ---- O · Tasks & Coaching ---- */
function O1() {
  return statusBar() + `<div class="dev-body scroll">
    <div class="hello">Today<span class="hello-sub">Fri 12 Jun · 2 of 6</span></div>
    <div class="prog"><span style="width:33%"></span></div>
    ${seclbl('MORNING')}
    ${taskRow('Standup notes', 'done')}
    ${taskRow('Reply to Sam', 'done')}
    ${taskRow('Q3 roadmap deck', 'active')}
    ${seclbl('AFTERNOON')}
    ${taskRow('Gym at 18:00', '')}
    ${taskRow('Book flights', '')}
    ${taskRow('Call dentist', '')}
    <div class="addbar"><span class="ab-ic">${I.plus}</span>Add a task…</div>
  </div>` + tabBar('tasks');
}
function O2() {
  return statusBar() + `<div class="dev-body sheet">
    <div class="grab"></div>
    <h2 class="sheet-h">New task</h2>
    <div class="field big"><input value="Finish Q3 roadmap deck" readonly><span class="caret"></span></div>
    ${seclbl('WHEN')}
    <div class="segwrap">${chip('Today', true)}${chip('Tomorrow', false)}${chip('Pick date', false)}</div>
    ${seclbl('PRIORITY')}
    <div class="segwrap">${chip('Low', false)}${chip('Normal', false)}${chip('Top', true)}</div>
    ${row({ ic: I.goal, title: 'Pin to device', sub: 'Shows on the task face', trail: toggle(false) })}
    <div class="cta-row">${btn('Add task', true)}</div>
  </div>`;
}
function O3() {
  const log = [
    ['STAND UP', 'You haven\'t moved in 4 hours.', '14:08', 'Movement'],
    ['BRING THE RUN FORWARD', 'Storm front moving in at 18:00.', '09:30', 'Weather'],
    ['YOU\'RE BEHIND ON SLEEP', '5 of 7 nights under 7h this week.', 'Yesterday', 'Sleep'],
    ['SHIP IT BEFORE NOON', 'The roadmap deck has slipped twice.', 'Yesterday', 'Focus'],
  ];
  return statusBar() + navBar('Nudges', { action: I.gear }) + `<div class="dev-body scroll pad">
    <p class="hint top">Every nudge your Gravity has given. Honest, never a feed.</p>
    ${log.map(([h, b, t, tag]) => `<div class="nudge"><div class="nu-top"><span class="nu-h">${h}</span><span class="nu-t">${t}</span></div><p class="nu-b">${b}</p><span class="nu-tag">${tag.toUpperCase()}</span></div>`).join('')}
  </div>`;
}
function O4() {
  return statusBar() + navBar('Coaching') + `<div class="dev-body scroll pad">
    ${seclbl('TONE')}
    <div class="segwrap">${chip('Calm', false)}${chip('Direct', false)}${chip('Honest', true)}</div>
    <div class="quote">"You said this mattered. It's 2pm and you haven't started."</div>
    ${seclbl('HOW OFTEN')}
    <div class="block"><div class="blk-top"><span>Frequency</span><b>Balanced</b></div>${slider(55)}</div>
    ${seclbl('QUIET HOURS')}
    ${row({ ic: I.moon, title: 'Do not disturb', sub: '22:30 – 07:00', trail: toggle(true) })}
    ${seclbl('TOPICS')}
    ${row({ title: 'Movement', trail: toggle(true) })}
    ${row({ title: 'Sleep', trail: toggle(true) })}
    ${row({ title: 'Weather', trail: toggle(false) })}
  </div>`;
}

/* ---- P · Insights & Settings ---- */
function P1() {
  const bars = [62, 74, 58, 86, 70, 92, 80, 66, 78, 88, 84, 90];
  const mx = Math.max(...bars);
  return statusBar() + `<div class="dev-body scroll">
    <div class="hello">Insights</div>
    ${seclbl('LAST 6 MONTHS')}
    <div class="bignum"><b>86%</b><span>average daily completion<br>across all goals & habits</span></div>
    <div class="chart">${bars.map(v => `<span class="bar" style="height:${(v / mx * 100).toFixed(0)}%"></span>`).join('')}</div>
    <div class="chart-x"><span>JAN</span><span>JUN</span></div>
    ${seclbl('HIGHLIGHTS')}
    <div class="statgrid">
      <div class="sg-cell"><b>47</b><i>longest streak</i></div>
      <div class="sg-cell"><b>3/4</b><i>goals on track</i></div>
      <div class="sg-cell"><b>312</b><i>tasks done</i></div>
      <div class="sg-cell"><b>+9%</b><i>vs last quarter</i></div>
    </div>
  </div>` + tabBar('insight');
}
function P2() {
  return statusBar() + navBar('Notifications') + `<div class="dev-body scroll pad">
    ${seclbl('FROM YOUR DEVICE')}
    ${row({ ic: I.bell, title: 'Nudges', sub: 'Movement, focus, weather', trail: toggle(true) })}
    ${row({ ic: I.goal, title: 'Goal milestones', sub: '25 / 50 / 75 / 100%', trail: toggle(true) })}
    ${row({ ic: I.bolt, title: 'Daily brief', sub: '07:30 each morning', trail: toggle(true) })}
    ${seclbl('DEVICE HEALTH')}
    ${row({ title: 'Low battery', sub: 'Under 15%', trail: toggle(true) })}
    ${row({ title: 'Lost connection', trail: toggle(false) })}
    ${seclbl('QUIET HOURS')}
    ${row({ ic: I.moon, title: 'Mute 22:30 – 07:00', trail: toggle(true) })}
  </div>`;
}
function P3() {
  return statusBar() + `<div class="dev-body scroll">
    <div class="hello">Settings</div>
    <div class="devcard sm">${mirror(faceIdle())}<div class="devmeta"><b>Gravity</b><span class="val">Connected · 86%</span><span class="lbl">FW 0.6.2 · UP TO DATE</span></div></div>
    ${seclbl('DEVICE')}
    ${row({ ic: I.bt, title: 'Connection', sub: 'Bluetooth · strong', trail: I.chev })}
    ${row({ ic: I.sun, title: 'Display', sub: 'Brightness, refresh, night', trail: I.chev })}
    ${row({ ic: I.goal, title: 'Calibrate tilt', sub: 'Faced 48°', trail: I.chev })}
    ${row({ ic: I.refresh, title: 'Check for firmware', trail: I.chev })}
    ${seclbl('')}
    ${row({ title: 'Unpair Gravity', on: true, trail: '' })}
  </div>` + tabBar('gear');
}
function P4() {
  return statusBar() + navBar('You') + `<div class="dev-body scroll pad">
    <div class="profile"><span class="avatar">A</span><b>Alex Mercer</b><i>Member since Jan 2026</i></div>
    <div class="statgrid">
      <div class="sg-cell"><b>4</b><i>active goals</i></div>
      <div class="sg-cell"><b>47</b><i>best streak</i></div>
    </div>
    ${seclbl('APPEARANCE')}
    ${row({ title: 'Theme', sub: '1-bit · matched to device', trail: 'Mono' })}
    ${row({ title: 'Typeface', sub: 'Space Grotesk · Mono', trail: I.chev })}
    ${seclbl('ACCOUNT')}
    ${row({ title: 'Data & privacy', trail: I.chev })}
    ${row({ title: 'Sign out', on: true })}
  </div>`;
}

/* ============================================================
   RENDER
   ============================================================ */
const appSections = [
  {
    badge: 'M', name: 'Setup & Device', font: 'Space Grotesk',
    phil: 'First contact and the device dashboard. <b>The app is the dark mission-control; the disc is the calm output.</b> Wherever a screen shows what your Gravity is displaying, it renders the real e-ink face — paper inside the phone.',
    screens: [
      { id: 'M1', name: 'Pair Device', fn: M1, note: 'Onboarding. A pulsing live disc previews the device while the app searches; one primary action, one fallback.', reads: ['Preview', 'Search', 'Pair'] },
      { id: 'M2', name: 'Device Home', fn: M2, note: 'The home tab: a live mirror of the current face, battery and sync, and four quick controls. What it shows now, and next.', reads: ['Mirror', 'Status', 'Controls'] },
      { id: 'M3', name: 'Display', fn: M3, note: 'Brightness on a slider, refresh-rate as a segmented control, night schedule and tilt — the e-ink knobs.', reads: ['Brightness', 'Refresh', 'Night'] },
      { id: 'M4', name: 'Faces', fn: M4, note: 'Pick the resting face from a grid of real disc thumbnails — idle, goal, tasks, focus, sleep, weather. One is selected.', reads: ['Grid', 'Preview', 'Select'] },
    ],
  },
  {
    badge: 'N', name: 'Goals & Habits', font: 'Space Grotesk',
    phil: 'The long game. <b>Progress rings everywhere — the same arc the device draws, in dark UI form.</b> Goals roll up to a single ring; habits read as a weekly heat grid; new goals can be pushed straight to a device face.',
    screens: [
      { id: 'N1', name: 'Goals', fn: N1, note: 'Every goal as a row with its own progress ring and percent. The list is the dashboard; one tap to add.', reads: ['Rings', 'Percent', 'Add'] },
      { id: 'N2', name: 'Goal Detail', fn: N2, note: 'One goal opened: a hero ring, the week\'s sub-targets, and a toggle to mirror live pace on the device during runs.', reads: ['Ring', 'Sub-goals', 'On device'] },
      { id: 'N3', name: 'Habits', fn: N3, note: 'The weekly heatmap, app-side — filled = done, outline = missed, today\'s column weighted. Streaks beneath.', reads: ['Heatmap', 'Today', 'Streaks'] },
      { id: 'N4', name: 'New Goal', fn: N4, note: 'Compose a goal: name, how to track it, target and deadline, and whether to give it a face on the device.', reads: ['Name', 'Track', 'Device'] },
    ],
  },
  {
    badge: 'O', name: 'Tasks & Coaching', font: 'Space Grotesk',
    phil: 'The everyday loop. <b>Tasks grouped by time of day, the nudge log in the device\'s own blunt voice, and the dial that tunes that voice.</b> The app captures; the device confronts.',
    screens: [
      { id: 'O1', name: 'Today', fn: O1, note: 'Tasks grouped Morning / Afternoon with a progress bar; done items strike through. An add-bar sits at the base.', reads: ['Tasks', 'Progress', 'Add'] },
      { id: 'O2', name: 'Add Task', fn: O2, note: 'A bottom sheet: title, when (segmented), priority, and a toggle to pin it to the device\'s task face.', reads: ['Title', 'When', 'Pin'] },
      { id: 'O3', name: 'Nudge Log', fn: O3, note: 'A history of every nudge in the device\'s honest, monospace voice — headline, reason, time, topic. Not a feed.', reads: ['Headline', 'Reason', 'Topic'] },
      { id: 'O4', name: 'Coaching', fn: O4, note: 'Tune the AI: tone (calm → honest), frequency, quiet hours, and which topics it\'s allowed to push.', reads: ['Tone', 'Often', 'Topics'] },
    ],
  },
  {
    badge: 'P', name: 'Insights & Settings', font: 'JetBrains Mono',
    phil: 'The back office. <b>Six-month review as 1-bit bars and stat tiles, then the plumbing</b> — notifications, device settings, profile. The same monochrome restraint; no second weight of grey.',
    screens: [
      { id: 'P1', name: 'Insights', fn: P1, note: 'The six-month review: one big completion number, a 1-bit bar chart of the months, and a grid of highlight stats.', reads: ['Average', 'Chart', 'Stats'] },
      { id: 'P2', name: 'Notifications', fn: P2, note: 'Per-category toggles — nudges, milestones, daily brief, device health — plus a single quiet-hours switch.', reads: ['Categories', 'Health', 'Quiet'] },
      { id: 'P3', name: 'Device Settings', fn: P3, note: 'A device card with the live face, then connection, display, calibration, firmware — and the unpair line at the bottom.', reads: ['Device', 'Rows', 'Unpair'] },
      { id: 'P4', name: 'Profile', fn: P4, note: 'Account and appearance. The theme is locked to 1-bit mono — the app deliberately matches the device it serves.', reads: ['You', 'Stats', 'Theme'] },
    ],
  },
];

(function renderApp() {
  const main = document.getElementById('main');
  appSections.forEach(d => {
    const sec = document.createElement('section');
    sec.className = 'dir';
    let cards = '';
    d.screens.forEach(sc => {
      const reads = sc.reads.map((r, j) => `<span><i>${j + 1}</i><b>${r}</b></span>`).join('');
      cards += `<figure class="card pcard">
        <div class="statelabel"><span class="num">${sc.id}</span><span class="nm">${sc.name}</span></div>
        <div class="phone-shell"><div class="device"><div class="bezel"><div class="dev-screen">${sc.fn()}</div><span class="island"></span></div></div></div>
        <figcaption><p>${sc.note}</p><div class="reads">${reads}</div></figcaption>
      </figure>`;
    });
    sec.innerHTML = `
      <div class="dirhead"><span class="badge">${d.badge}</span><h2>${d.name}</h2><span class="font">${d.font}</span></div>
      <p class="dirphil">${d.phil}</p>
      <div class="row approw">${cards}</div>`;
    main.appendChild(sec);
  });
  fitPhones();
  requestAnimationFrame(fitPhones);
  setTimeout(fitPhones, 350);
})();

function fitPhones() {
  document.querySelectorAll('.phone-shell').forEach(sh => {
    const dev = sh.querySelector('.device');
    const w = sh.clientWidth;
    const s = w / 390;
    dev.style.transform = `scale(${s})`;
    sh.style.height = (844 * s) + 'px';
  });
}
window.addEventListener('resize', fitPhones);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitPhones);
