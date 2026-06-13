# UI/UX — GRAVITY

---

## Design Philosophy

Gravity's visual language is built on a single constraint that became an identity: **a circular black and white display that cannot animate quickly.**

Everything flows from that. The restraint is not a limitation — it is the aesthetic. E-ink forces honesty. There are no gradients to hide behind, no motion to distract, no colour to signal emotion. Only space, type, and line. The design must work in pure contrast or it does not work at all.

The visual references are:
- **Kindle Paperwhite** — readable at any light level, typographically considered, nothing decorative
- **NASA mission displays** — every pixel earns its place, hierarchy is functional not ornamental
- **1980s terminal UIs** — monospace confidence, scan-line rhythm, text as interface
- **GitHub contribution graphs** — data made beautiful through repetition and density
- **Dieter Rams** — as little design as possible, as much as necessary

The companion app inherits this language and takes it into dark mode — the phone becomes the inside of the device. Opening the app should feel like stepping into the same world the physical object lives in.

---

## Design Token System

### Colour

**Device (e-ink — absolute)**
```
INK_BLACK     #000000   — text, outlines, filled glyphs
INK_WHITE     #FFFFFF   — background, negative space
INK_DITHER    ░░░░░░    — dithered pattern for mid-weight fills (e-ink only)
```

**App (dark mode)**
```
VOID          #080808   — primary background
SURFACE       #111111   — card / panel background
BORDER        #222222   — dividers, outlines, inactive elements
DIM           #444444   — secondary text, disabled states
MID           #888888   — tertiary text, labels
BRIGHT        #CCCCCC   — primary body text
WHITE         #F0F0F0   — headlines, active elements
PULSE         #E8E8FF   — the single accent — cold near-white blue, used with extreme restraint
                          only: active state, live indicator, current cycle marker
```

One accent. Used once per screen maximum. Everything else is greyscale.

### Typography

**Display face:** `Space Mono` — monospace, geometric, the terminal voice of the product. Used for all device e-ink text. Used in the app for numbers, data, glyphs, system-level labels.

**Body face:** `Inter` — neutral, highly legible at small sizes, no personality of its own (intentional — Space Mono carries all the character). Used in the app for paragraphs, descriptions, conversational AI text.

**Type scale (device):**
```
XL    32px   Space Mono Bold    — single dominant value (streak count, goal %)
LG    20px   Space Mono Regular — primary label, time display
MD    14px   Space Mono Regular — secondary info, task names
SM    11px   Space Mono Regular — perimeter labels, status glyphs, ambient data
```

**Type scale (app):**
```
H1    28px   Space Mono Bold    — screen titles, cycle headlines
H2    20px   Space Mono Medium  — section headers, goal names
DATA  32px   Space Mono Bold    — large numbers, progress values
BODY  15px   Inter Regular      — descriptions, AI commentary, explanations
LABEL 12px   Space Mono Regular — tags, metadata, timestamps
MICRO 11px   Inter Regular      — captions, footnotes
```

### Layout Grid

**Device:** Radial. All layout decisions made from the centre outward. Three zones:
- **Core** (0–35% of radius): primary information — one thing only
- **Mid-ring** (35–70% of radius): secondary information — supporting data
- **Perimeter** (70–100% of radius): ambient status — arcs, tick marks, glyphs

**App:** 16px base grid. 20px horizontal margins. No cards with filled backgrounds — only bordered containers. Maximum content width 390px (single column throughout — this is not a dashboard, it is a focused instrument).

---

## Round Display — Constraints & Adaptations

The circular display is the hardest design problem in Gravity. Everything designed for screens assumes a rectangle. The circle breaks all of those assumptions.

### The Fundamental Rules

**Rule 1 — The circle is not a clipped rectangle.**
Content is never laid out as if it will be cropped by a circle. Every element must be designed knowing the circle is the canvas. Layouts that look like a rectangular screen with corners cut off are wrong.

**Rule 2 — One dominant thing.**
The human eye entering a circle has no corner anchors. It goes to the centre. The centre must have one clear thing — a number, a word, a glyph. Two things fighting for the centre reads as noise.

**Rule 3 — The perimeter is active UI space.**
The edge of the circle is not wasted space. It is where arcs, progress rings, tick marks, and ambient status live. It frames the centre without competing with it.

**Rule 4 — Radial symmetry creates calm, deliberate asymmetry creates tension.**
Most screens should feel balanced — radially symmetric. A screen with intentional asymmetry signals urgency (nudge screens, alerts). This is used deliberately, not by accident.

**Rule 5 — Text must never touch the edge.**
Minimum 14px from the circle boundary on all sides. Text that approaches the curve reads as an error, not design.

**Rule 6 — No horizontal rules or rectangular dividers.**
Dividers on a circular screen must be arcs or radial lines. A horizontal line across a circle reads as a mistake.

### Refresh Rate Adaptation

E-ink full refresh: ~2 seconds (with characteristic flash). Partial refresh: ~400ms.

UI rules built around this:
- **Full refresh** only on screen state transitions (idle → nudge, goal view → heatmap)
- **Partial refresh** for data updates within a screen (habit ticked, time update, progress increment)
- Touch feedback is always partial refresh — a small invert of the tapped region within 100ms, before any full re-render
- No animations. No transitions. No progress bars that fill in real time. State changes are instantaneous.
- The ambient screen refreshes every 15 minutes maximum — not every minute. E-ink is not a clock.

### Touch Zone Mapping

```
         ┌─────────────┐
         │  TOP ZONE   │
         │  [swipe up  │
         │  or tap for │
         │  detail]    │
    ┌────┤             ├────┐
    │LEFT│   CENTRE    │RGHT│
    │swpe│   [tap to   │swpe│
    │◄───│   confirm / │───►│
    │    │   select]   │    │
    └────┤             ├────┘
         │ BOTTOM ZONE │
         │ [swipe down │
         │ to dismiss] │
         └─────────────┘
```

- **Centre tap:** confirm / acknowledge / select
- **Swipe left:** next screen / next item
- **Swipe right:** previous screen / back
- **Swipe up:** expand detail / surface AI commentary
- **Swipe down:** dismiss nudge / snooze / return to idle
- **Long press (centre):** open quick menu — check-in, settings shortcut, manual habit log

---

## Device Screen States

### Screen 1 — Boot Sequence

**When:** Power on, firmware initialisation.

**What it shows:**
A terminal-style boot sequence. Text prints line by line in Space Mono. Fast — under 8 seconds total.

```
GRAVITY OS v1.0.2
INITIALISING...

[████████████████] 100%

DISPLAY        OK
WIFI           CONNECTING...
WIFI           CONNECTED
BACKEND        OK
PROFILE        LOADED
AI ENGINE      READY

WELCOME BACK, MICHAEL.
```

After the final line — 1 second pause — then cross-fades (via full refresh) to the ambient screen.

**First boot variant:** After "WIFI CONNECTED", shows a QR code centred on screen with:
```
SCAN TO CONTINUE SETUP
[QR CODE — CENTRED, LARGE]
gravity.app/setup
```

---

### Screen 2 — Ambient / Idle

**When:** Default state. Device sitting on desk. No active task window.

**Purpose:** Glanceable in under 1 second. User looks up and knows immediately how their day is going.

**Layout:**
```
         ┌─────────────────────┐
         │                     │
         │  WED 12 JUN  14:32  │  ← SM, top zone, Space Mono
         │                     │
         │    ┌─────────┐      │
         │    │   14    │      │  ← XL, centre, bold — streak count
         │    │  days   │      │  ← SM, below number
         │    └─────────┘      │
         │                     │
         │  ✓ · ·  3 left      │  ← MD, bottom zone — non-negotiables status
         │                     │
         └─────────────────────┘

Perimeter arc: goal progress (0–100% arc clockwise from 12 o'clock)
Tick marks at 25% intervals
```

**What the user reads in order:**
1. Streak — immediately, centre dominant
2. Goal progress arc — peripheral, glanced
3. Non-negotiables remaining — bottom, secondary

**Ambient refresh:** Every 15 minutes or on habit completion event.

---

### Screen 3 — Morning Brief

**When:** Triggered at the user's defined morning time (e.g. 7:30am). Replaces ambient until first non-negotiable is completed.

**Purpose:** Answer "what do I need to do today" in one look.

**Layout:**
```
         ┌─────────────────────┐
         │   THURSDAY  07:31   │
         │ ─────────────────── │  ← arc divider
         │                     │
         │  FOCUS:             │  ← SM label
         │  Finish API spec    │  ← LG, centre — today's top priority
         │                     │
         │ ─────────────────── │  ← arc divider
         │  □ Gym              │
         │  □ 3 meals          │  ← MD — non-negotiables checklist
         │  □ 2km walk         │
         └─────────────────────┘

Perimeter: time arc — how far through the day
Top glyph: ☀ (morning indicator)
```

**What the user reads in order:**
1. Today's focus task — centred, largest
2. Non-negotiables — quick scan checklist
3. Time arc — ambient peripheral

---

### Screen 4 — Active Nudge

**When:** Nudge condition fires, AI decides to intervene.

**Purpose:** Stop what the user is doing and make them aware. This screen is designed to be uncomfortable to ignore — full-face, no ambient data, direct language.

**Layout — Level 2 (Prompt):**
```
         ┌─────────────────────┐
         │                     │
         │  ──────────────     │
         │                     │
         │   API SPEC          │  ← LG, centre
         │   STILL OPEN        │
         │   90 MIN GONE       │  ← MD
         │                     │
         │  ──────────────     │
         │                     │
         │   [TAP TO LOG]      │  ← SM, bottom — action prompt
         └─────────────────────┘

Perimeter: inverted — black arc, white background (visual inversion signals urgency)
```

**Layout — Level 3 (Direct):**
```
         ┌─────────────────────┐
         │                     │
         │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │  ← dithered top band (urgency signal)
         │                     │
         │   4 GYM             │  ← XL bold, centre
         │   SESSIONS          │
         │   MISSED            │
         │                     │
         │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │  ← dithered bottom band
         │                     │
         │  SWIPE ↓ DISMISS    │  ← SM — only action is acknowledge
         └─────────────────────┘
```

Level 3 nudge has no confirm action — only dismiss. The message is the intervention. The user cannot "complete" it from the device. They either act or swipe it away. Both are logged.

---

### Screen 5 — Goal Progress View

**When:** User swipes to this screen from ambient. Or tapped from morning brief.

**Purpose:** Show exactly where the user is on their 6-month goal. No approximation.

**Layout:**
```
         ┌─────────────────────┐
         │                     │
         │         34%         │  ← XL bold, centre
         │    ┌─────────┐      │
         │    │ ░░░░░░░ │      │  ← dithered arc segment — completed
         │    │         │      │     vs empty arc — remaining
         │    └─────────┘      │
         │  BUILD PORTFOLIO    │  ← MD — goal name
         │  WK 11 OF 26        │  ← SM — where in the cycle
         │                     │
         │  ↑ THIS WEEK        │  ← SM bottom — this week's focus task
         │  3 CASE STUDIES     │
         └─────────────────────┘

Perimeter arc: 6-month goal — thick, dominant, the most prominent arc on any screen
Inner arc: weekly milestone completion
```

**What the user reads in order:**
1. Percentage — how far through the goal
2. Arc — visualised, immediately understood
3. Goal name and position in cycle
4. This week's task

---

### Screen 6 — Weekly Heatmap

**When:** Swiped to. Also shown as part of the evening check-in screen.

**Purpose:** Show habit completion across the past 7 days as a dot grid. Beautiful, scannable, honest.

**Layout:**
```
         ┌─────────────────────┐
         │  LAST 7 DAYS        │
         │                     │
         │  GYM  ● ● · ● ● · ● │  ← ● done · missed
         │  WALK ● ● ● ● ● · ● │
         │  MEALS● ● ● · ● ● ● │
         │  READ ● · ● ● · ● ● │
         │  CODE · ● ● ● ● ● · │
         │                     │
         │  M  T  W  T  F  S  S│  ← SM day labels below grid
         │                     │
         │  STREAK: 14 ↑       │  ← MD bottom — overall streak
         └─────────────────────┘

Perimeter: subtle arc for overall completion rate this week
Dots: ● = filled circle (complete), · = centred dot (missed)
```

**Design note:** The dot grid must be sized so dots are large enough to distinguish at 40cm. Minimum dot diameter 8px. Minimum dot spacing 12px.

---

### Screen 7 — Evening Check-In

**When:** User's defined evening time. Replaces ambient.

**Purpose:** Close the day. Log anything not yet logged. Show today's final picture.

**Layout:**
```
         ┌─────────────────────┐
         │  THU  21:00         │
         │                     │
         │  TODAY:             │
         │  ✓ ✓ · ✓ ✓          │  ← non-negotiables — ticked/missed
         │                     │
         │    4 / 5            │  ← XL — completions today
         │                     │
         │  ─────────────────  │
         │  OPEN APP           │  ← MD — prompt to log in app
         │  TO CHECK IN        │
         └─────────────────────┘

Perimeter: today's arc — fills as habits complete, static now at day's end
```

---

### Screen 8 — Offline / Error State

**When:** WiFi disconnected, backend unreachable.

**Design principle:** The device never shows an error screen that leaves the user with nothing. It always shows the last cached data with a subtle indicator of offline state.

**Layout:** Same as ambient, but:
- A small `○` (hollow circle glyph) in the top-right corner of the perimeter — the WiFi status indicator
- When online: `●` (filled)
- When offline: `○` (hollow)
- No error message. No "cannot connect" text. Just the hollow indicator.

The user who knows what it means will notice. The user who doesn't will still see a functioning, calm screen.

---

## Companion App Screens

### App Screen 1 — Home / Today

**The daily instrument panel. The most visited screen.**

Layout structure:
```
┌─────────────────────────┐
│ GRAVITY          ●  14d │  ← header: app name, live device indicator, streak
│─────────────────────────│
│                         │
│    ┌───────────────┐    │
│    │               │    │
│    │  [DEVICE      │    │  ← circular device mirror, ~180px diameter
│    │   PREVIEW]    │    │     live render of current e-ink layout
│    │               │    │     tap to cycle device screens
│    └───────────────┘    │
│                         │
│─────────────────────────│
│ TODAY                   │
│                         │
│ □  Gym                  │  ← non-negotiables with toggle
│ ✓  3 meals              │     Space Mono labels
│ □  2km walk             │     tap to complete
│ □  Read 20 mins         │
│                         │
│─────────────────────────│
│ FOCUS                   │
│ Finish API spec         │  ← top priority task, LG
│                         │
│─────────────────────────│
│ "You're 3 for 5 on      │  ← AI focus line — one sentence, italic Inter
│  non-negotiables.       │     generated fresh each morning
│  Gym is the gap."       │
└─────────────────────────┘
```

**Key element — the circular device preview:**
- Renders exactly what the physical device is showing right now
- Circular frame, black background, white content — matches device aesthetic exactly
- Tapping it cycles through device screens (ambient → morning brief → goal → heatmap)
- A `●` indicator in the header glows PULSE colour when device is connected live
- When device is offline: preview shows last known state with `○` indicator

---

### App Screen 2 — Goal View

**The full picture of the 6-month goal. Accessed from bottom nav.**

Layout structure:
```
┌─────────────────────────┐
│ ← GOAL                  │
│─────────────────────────│
│                         │
│         34%             │  ← DATA size, centre
│    [LARGE ARC RING]     │  ← circular progress ring, ~200px, dominant
│  BUILD PORTFOLIO        │  ← H2 below ring
│  WK 11 → WK 26         │  ← LABEL — position in cycle
│                         │
│─────────────────────────│
│ LIKELIHOOD     73%  ↑   │  ← on-track score + trend arrow
│─────────────────────────│
│ THIS WEEK               │
│ □ 3 case studies        │  ← weekly sub-tasks
│ □ Update homepage       │
│ □ LinkedIn post         │
│                         │
│─────────────────────────│
│ "You're ahead of pace   │  ← AI commentary paragraph
│  on content but the     │     Inter body, honest tone
│  portfolio site hasn't  │
│  moved in 3 weeks.      │
│  That's the blocker."   │
│                         │
│─────────────────────────│
│ MILESTONES              │
│ M1 ●─────────────────── │  ← milestone timeline
│ M2 ●─────────────────── │     filled dot = hit
│ M3 ·─────────────────── │     hollow dot = pending
│ M4 ·─────────────────── │
│ M5 ·─────────────────── │
│ M6 ·─────────────────── │
└─────────────────────────┘
```

---

### App Screen 3 — Habits & Heatmap

**The historical view. Where patterns become visible.**

Layout structure:
```
┌─────────────────────────┐
│ ← HABITS                │
│─────────────────────────│
│ LAST 90 DAYS            │
│                         │
│ GYM                     │
│ [dot grid — 90 cols]    │  ← GitHub-style, 1 dot per day
│ 71%  ↑  streak: 6       │  ← completion rate, trend, streak
│                         │
│ WALK                    │
│ [dot grid — 90 cols]    │
│ 88%  →  streak: 14      │
│                         │
│ 3 MEALS                 │
│ [dot grid — 90 cols]    │
│ 62%  ↓  streak: 2       │
│                         │
│ READ                    │
│ [dot grid — 90 cols]    │
│ 55%  ↓  streak: 1       │
│                         │
│─────────────────────────│
│ PATTERN                 │
│ "Gym drops every        │  ← AI-identified pattern, surfaced here
│  week after a           │     LABEL size, indented
│  late social event."    │
│─────────────────────────│
│ + ADD HABIT             │  ← minimal add button, bottom
└─────────────────────────┘
```

**Heatmap dot spec:**
- Dot size: 6px diameter
- Dot spacing: 3px gap
- Completed: `●` filled white circle on dark background
- Missed: `·` 2px dot (dim — present but quiet)
- Future: empty space
- Dots are not coloured — never. Intensity is weight only (filled vs dim vs empty)

---

### App Screen 4 — Nudge Log

**The AI's record of every intervention. Transparent by design.**

Layout structure:
```
┌─────────────────────────┐
│ ← NUDGE LOG             │
│─────────────────────────│
│ PATTERNS                │
│                         │
│ "You act on direct      │  ← AI pattern observations, bold, top
│  nudges 3× more than    │
│  gentle ones."          │
│                         │
│ "Gym nudges work.       │
│  Focus nudges don't."   │
│                         │
│─────────────────────────│
│ HISTORY                 │
│                         │
│ TODAY 14:32             │
│ FOCUS — ignored         │  ← nudge entry: time, category, response
│ "API spec still open.   │     Space Mono label, Inter body
│  90 min gone."          │
│                         │
│ TODAY 09:15             │
│ GYM — acted ✓           │  ← ✓ = user completed within 2 hrs
│ "Gym blocked. No log."  │
│                         │
│ YESTERDAY 21:00         │
│ SLEEP — acted ✓         │
│ "Past your bedtime."    │
│                         │
│─────────────────────────│
│ SENSITIVITY             │
│ FITNESS    [●●●●○]      │  ← per-category sensitivity control
│ FOCUS      [●●○○○]      │     5-dot selector, Space Mono
│ SPENDING   [●●●○○]      │
│ SLEEP      [●●●●●]      │
└─────────────────────────┘
```

---

### App Screen 5 — 6-Month Review

**The most important screen in the product. Designed to feel ceremonial.**

This screen has a distinct visual treatment — the only screen with a structural departure from the standard layout.

```
┌─────────────────────────┐
│                         │
│  CYCLE 1 COMPLETE       │  ← H1, centred, Space Mono
│  26 WEEKS               │
│                         │
│  ────────────────────   │
│                         │
│  WHAT YOU SET OUT TO DO │  ← LABEL
│  "Build a portfolio     │  ← original goal verbatim, Inter italic
│   and get my first      │
│   freelance client."    │
│                         │
│  ────────────────────   │
│                         │
│  WHAT HAPPENED          │  ← LABEL
│                         │
│  [LARGE HEATMAP         │  ← 26-week heatmap, all habits combined
│   26 WEEKS WIDE]        │     the full picture at a glance
│                         │
│  NON-NEGS    78% ●●●●○  │  ← key stats as dot ratings
│  MILESTONES  2 of 3 ✓   │
│  NUDGE RATE  61% acted  │
│                         │
│  ────────────────────   │
│                         │
│  "You built the work.   │  ← Claude's honest assessment
│   The site never went   │     Inter body, no hedging
│   live. That's the gap  │
│   between this cycle    │
│   and the next."        │
│                         │
│  ────────────────────   │
│                         │
│  START CYCLE 2 →        │  ← single CTA, bottom
└─────────────────────────┘
```

**Design notes:**
- Only screen with centred text alignment (all other screens are left-aligned)
- The 26-week heatmap is the centrepiece — makes the full cycle visible as one object
- No navigation bar visible — full screen, no distractions
- Scrollable — the review is long. That is intentional. This is not a notification.

---

### App Screen 6 — Device & Settings

**Functional and minimal. Not the interesting part of the product.**

```
┌─────────────────────────┐
│ ← SETTINGS              │
│─────────────────────────│
│ DEVICE                  │
│                         │
│ [●] Gravity             │  ← live status indicator
│     Connected · v1.0.2  │
│     Battery: 84%        │
│                         │
│─────────────────────────│
│ DISPLAY                 │
│ Morning brief    07:30  │  ← time pickers
│ Evening check-in 21:00  │
│ Quiet hours    23–07    │
│ Rest days        [SUN]  │  ← toggleable day selector
│                         │
│─────────────────────────│
│ INTEGRATIONS            │
│ [●] Google Calendar     │  ← ● = connected, ○ = disconnected
│ [●] Apple Health        │
│ [○] Screen Time         │  ← tap to set up Shortcut
│ [○] Open Banking        │
│ [○] Spotify             │
│                         │
│─────────────────────────│
│ ACCOUNT                 │
│ Subscription    Active  │
│ Export my data          │
│ Delete account          │
└─────────────────────────┘
```

---

## Navigation Model

### Device Navigation
No persistent nav. Gesture-only.

```
IDLE ←──swipe left/right──► MORNING BRIEF ←──► GOAL VIEW ←──► HEATMAP
  ↑                                                                  ↑
  └──────────────── swipe right from any screen = back to IDLE ─────┘

Long press anywhere = quick menu (log habit, check-in, settings)
Active nudge overlays current screen — swipe down to dismiss
```

### App Navigation
Bottom tab bar — 4 items, Space Mono labels, icon-free (text only):

```
[ TODAY ]  [ GOAL ]  [ HABITS ]  [ LOG ]
```

Settings accessed via top-right glyph on TODAY screen.
Review screen appears as full-screen modal at cycle end — not accessible from nav bar.

---

## Component Library

### Device Components

**Arc** — variable weight, variable fill %, always anchored at 12 o'clock clockwise
**Dot grid** — N×7 matrix, ●/· fill states, fixed spacing
**Progress number** — XL Space Mono Bold, always centred
**Checklist** — □/✓ prefix, MD Space Mono, left-aligned in bottom zone
**Dithered band** — horizontal ░░░ band, used only in Level 3 nudges for urgency signal
**Perimeter tick marks** — 4 marks at 12/3/6/9 o'clock, SM scale marks
**Status glyph** — ●/○ single character, SM, always top-right perimeter

### App Components

**Device mirror** — circular frame, exact device UI re-rendered in React Native, live
**Heatmap row** — label + dot grid + stat line (% / trend arrow / streak)
**Arc ring** — circular SVG progress ring, BRIGHT stroke on VOID background, DATA number centred
**AI callout** — left-bordered text block, BORDER left accent, Inter italic body, no background fill
**Stat line** — `LABEL    VALUE  TREND` — three columns, Space Mono throughout
**Milestone track** — vertical line, ●/· nodes, H2 milestone labels right-aligned
**Sensitivity selector** — 5-dot row `●●●○○`, tap to adjust, Space Mono label left
**Toggle** — text-based: `[●]` connected / `[○]` disconnected — no native switch components
**Divider** — 1px BORDER horizontal rule, full width, 16px vertical margin each side
**CTA** — full-width, 1px BRIGHT border, BRIGHT Space Mono text, no fill, 48px height

### What the App Never Uses
- Native iOS/Android UI components (no segmented controls, no native switches, no system alerts)
- Filled card backgrounds
- Colour other than PULSE for active state
- Drop shadows
- Border radius > 2px (near-zero — the aesthetic is angular, not soft)
- Icons (text and glyphs only — Space Mono has sufficient character)
- Gradient of any kind

---

## Interaction Principles

**One action per screen state.**
Every screen has one obvious next action. The user is never choosing between competing CTAs.

**Data before explanation.**
Numbers and glyphs come first. Prose commentary comes below. The user who wants to understand reads down. The user who just wants the number looks once and looks away.

**Nothing performs positivity.**
Completion states do not celebrate. A completed habit logs as ✓ — no animation, no sound, no confetti. The streak number going up is the reward. The product trusts the user to feel good about that without being told to.

**Silence is part of the design.**
When there is nothing to say, Gravity says nothing. A quiet ambient screen after a good day is not a failure state — it is the product working correctly.

**Errors are never vague.**
If something goes wrong — integration disconnected, sync failed, device offline — the screen says exactly what happened and exactly what to do. No "something went wrong." No spinning indicators left indefinitely.
