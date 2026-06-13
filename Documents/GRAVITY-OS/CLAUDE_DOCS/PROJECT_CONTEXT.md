# GRAVITY — CLAUDE PROJECT CONTEXT

> This file is the single source of truth for any Claude project, Claude Code session, or AI assistant working on Gravity. Read this before doing anything else. All decisions should be consistent with what is written here.

---

## What Is Gravity

Gravity is a physical AI-powered goal tracking device. It sits on a user's desk or bedside table. It has a circular e-ink display. It runs a 6-month goal cycle. It learns the user's behaviour patterns over time and nudges them — via the physical device screen — when they are procrastinating, avoiding habits, or drifting from their goals.

It is not an app. It is not a smartwatch. It is not a notification machine. It is a physical object with one job: making sure the user becomes the person they said they wanted to be.

**The product has three surfaces:**
1. **The device** — circular e-ink display, sits on desk, shows glanceable data, delivers nudges
2. **The companion app** — React Native, iOS + Android, integration hub, rich data view, onboarding
3. **The backend** — Python FastAPI, owns all AI reasoning, serves both device and app

---

## Who Is Building This

**Michael Jones** — Junior Technical Analyst at VX One, London. Age 20. Solo founder.
- Stack: Python, PowerShell, Bash, React Native (learning), FastAPI (learning)
- Dev environment: MacBook Air (Apple Silicon), Tailscale network, Linux dev machine `mj-notarobot`
- Ollama running on `mj-notarobot` at `vx1-dev.tail972d72.ts.net:11434` — use for local dev/testing
- Building in ~1–2 hours/day alongside a full-time job
- Goal: working demo first, hardware prototype second, real users third

**Current stage: Stage 0 — Brain First**
The AI onboarding conversation engine comes before everything else. No hardware. No app. No backend yet. Just the conversation logic that makes the product real.

---

## Build Stages — Do Not Skip Ahead

| Stage | What Gets Built | Status |
|---|---|---|
| 0 | AI onboarding brain — Python terminal, Claude/Groq API, profile stored as JSON | IN PROGRESS |
| 1 | FastAPI backend + PostgreSQL + React Native app shell | NOT STARTED |
| 2 | RPi Zero 2W + round e-ink display prototype + MicroPython firmware | NOT STARTED |
| 3 | Integration layer — Calendar, Health, Screen Time | NOT STARTED |
| 4 | ESP32-S3 hardware migration + 3D printed enclosure | NOT STARTED |
| 5 | Polish, app store, launch | NOT STARTED |

**The AI brain is the product. A beautiful UI with weak AI is a shell. Build and validate the conversation engine before touching hardware or building the app.**

---

## AI Layer — Provider Strategy

| Stage | Provider | Cost | Notes |
|---|---|---|---|
| Demo / proof of concept | Claude artifact sandbox (claude.ai) | £0 | Browser demo only, not deployable |
| Beta (0–500 users) | Groq free tier | £0 | 14,400 req/day, Llama 3.1 70B |
| Growth (500–2,000 users) | Groq paid or Claude API | ~£0.50–0.85/user/month | Evaluate quality at this point |
| Scale (2,000+ users) | Anthropic Claude API (Sonnet) | ~£0.85/user/month | Revenue covers it at this scale |
| Dev / testing always | Ollama on mj-notarobot | £0 | Local, no rate limits, not for prod |

**Never put API keys in client-side code. All AI runs server-side. No exceptions.**

For development, use the cheapest model available (Haiku / Llama 3.1 8B). Switch to quality models (Sonnet / Llama 3.1 70B) for production conversations.

---

## The Onboarding Conversation — Core Logic

This is the most important thing to get right. The onboarding conversation is what makes Gravity real. It runs in the companion app (or terminal for Stage 0) and builds the user's profile.

### 5 Phases

**Phase 1 — Identity (5–8 min)**
Ask who the user is. Not the goals version — just them. Extract: personality summary, motivation style (intrinsic/extrinsic), energy pattern (morning/evening/variable), failure response style, feedback preference (direct/factual/questioning/gentle).

Opening: *"Before we set any goals — tell me a bit about yourself. Not the goals version of you. Just you."*

**Phase 2 — Routine (3–5 min)**
Ask what yesterday actually looked like. Extract: wake/sleep times, peak focus windows, known dead zones, avoidance behaviours, existing good habits, realistic daily hours available.

Opening: *"Walk me through yesterday — not an ideal day, just what actually happened."*

**Phase 3 — Goal (5–10 min)**
Ask what they want to be different in 6 months. Drill down through 2 layers of "why" to find the real motivation. Evaluate feasibility against available time. Surface likelihood score honestly if < 0.4.

Opening: *"What do you want to be different in 6 months? Don't filter it."*

**Phase 4 — Non-Negotiables (3–4 min)**
What do they want to do every single day no matter what? Push back if the list exceeds 5 items. These get enforced daily.

Opening: *"What are the small things you want to do every day no matter what?"*

**Phase 5 — Feedback Style (1–2 min)**
Confirm how the AI should communicate when the user is off track. Options: direct / factual / questioning / gentle. Stored and refined over time.

Opening: *"When you're off track, how do you want me to handle it?"*

### Rules
- One question per message. Never two.
- Be direct, warm, intelligent. Not corporate. Not cheerful.
- Move to the next phase after one substantive answer. Don't linger.
- The conversation follows a framework but never reveals the framework.

### Output
After Phase 5, generate and store:
```json
{
  "name": "string",
  "personality_summary": "2-3 sentence AI summary",
  "motivation_style": "intrinsic | extrinsic | mixed",
  "energy_pattern": "morning | evening | variable",
  "feedback_preference": "direct | factual | questioning | gentle",
  "schedule": {
    "wake_time": "HH:MM",
    "sleep_time": "HH:MM",
    "peak_focus_windows": ["HH:MM-HH:MM"],
    "known_dead_zones": ["HH:MM-HH:MM"],
    "realistic_daily_hours": 1.5,
    "avoidance_behaviours": ["string"]
  },
  "goal": {
    "statement": "string",
    "real_why": "string",
    "likelihood_score": 0.73,
    "milestone_structure": ["string"],
    "risk_factors": ["string"]
  },
  "non_negotiables": ["string"],
  "cycle_start": "YYYY-MM-DD",
  "cycle_end": "YYYY-MM-DD"
}
```

---

## The 6-Month Cycle

Gravity runs on 6-month cycles. Every cycle:
1. User onboards or reviews
2. Goal is set with milestones
3. Device tracks daily progress
4. AI nudges based on behaviour data
5. At 6 months: full review — honest data, reflection conversation, new cycle

The review is not an audit. It shows exactly what happened (data first, no editorialising), then Claude gives a direct honest assessment, then the user reflects, then a new goal is set using actual behavioural data from the last cycle — not wishful planning.

---

## Nudge Philosophy

**Core rule: nudges must be rarer than expected and more accurate than feels comfortable.**

A wrong nudge destroys trust. A right nudge builds it. Optimise for accuracy over frequency.

**Frequency limits:**
- Minimum 90 minutes between any two nudges
- Maximum 3 nudges per 24 hours
- Zero during quiet hours
- Zero on rest days

**4 intensity levels:**
1. **Ambient** — e-ink only, no phone notification. Gentle reminder.
2. **Prompt** — e-ink update + silent app badge. Task avoidance detected.
3. **Direct** — e-ink full-screen takeover + app push with sound. Pattern-based intervention.
4. **Conversation** — e-ink prompt + app notification opening check-in chat. Something has shifted.

**Tone modes (set at onboarding, refined over time):**
- Direct: *"You haven't moved today. 847 steps. Go outside."*
- Factual: *"Step count: 847. Your average: 6,240. Goal: 8,000."*
- Questioning: *"You had the gym blocked out — what happened?"*
- Gentle: *"Just a nudge — your walk hasn't happened yet."*

**What nudges never do:** shame, catastrophise, repeat the same message, nudge about something out of the user's control right now.

---

## Device — Physical Spec

- **Shape:** Circular. ~110–120mm diameter. Similar footprint to Apple HomePod Mini but slightly larger.
- **Display:** Round e-ink, 95–105mm usable diameter, black and white only, 300 DPI target
- **Display panel target:** Waveshare 3.71" Round E-Paper (480×480px) — order before designing enclosure
- **Back:** Smooth convex matte soft-touch plastic. Comfortable to hold. No ports or buttons on back.
- **Stand:** Angled base, 15–25 degrees from vertical. Device faces user. USB-C in base, not body.
- **Touch:** Capacitive overlay over display. Tap, swipe left/right/up/down, long press.
- **Processor:** RPi Zero 2W (prototype) → ESP32-S3 (production)
- **Power:** Primarily plugin (USB-C via base). Battery 1500–2000mAh for backup. Target 2–4 week battery.
- **Weight target:** Under 200g
- **Prototype BOM:** ~£63–81. Order from Waveshare + AliExpress + Pimoroni.

---

## Device UI — Rules

**The circle is not a clipped rectangle.** Everything is designed radially.

**Three zones:**
- Core (0–35% radius): one dominant thing — a number, a word
- Mid-ring (35–70% radius): supporting data
- Perimeter (70–100% radius): ambient status — arcs, glyphs, tick marks

**E-ink refresh rules:**
- Full refresh (2s, with flash): screen state transitions only
- Partial refresh (400ms): in-screen data updates
- Fast partial invert (100ms): touch acknowledgement — must happen before full re-render
- Ambient screen refreshes max every 15 minutes
- Full refresh at minimum once every 4 hours to prevent ghosting

**The AI generates layout JSON, not pixels. The device renders JSON → e-ink. This means UI can be updated without firmware changes.**

**Screen states:** Boot sequence, Ambient/Idle, Morning Brief, Active Nudge (L2 and L3), Goal Progress, Weekly Heatmap, Evening Check-In, Offline state.

---

## Visual Language

**Device:** Black and white only. Space Mono font. Negative space. Terminal/NASA aesthetic.
**App:** Dark mode. Background #080808. Single accent PULSE #E8E8FF — used once per screen maximum. Space Mono for data/labels, Inter for body text. No filled cards, no gradients, no shadows, no icons, no rounded corners above 2px.

**References:** Kindle Paperwhite, NASA mission displays, 1980s terminal UIs, GitHub contribution graphs, Dieter Rams.

**The app should feel like stepping inside the device.**

---

## Tech Stack — Full

| Layer | Technology |
|---|---|
| Device firmware (proto) | MicroPython on Raspberry Pi Zero 2W |
| Device firmware (prod) | MicroPython or C++ on ESP32-S3 |
| Backend language | Python 3.11+ |
| Backend framework | FastAPI (async) |
| Database | PostgreSQL via SQLAlchemy async |
| Cache | Redis |
| Task queue | Celery + Redis |
| AI | Claude API (Anthropic SDK) / Groq / Ollama |
| Real-time | WebSocket (FastAPI native) |
| App framework | React Native (Expo) |
| App state | Zustand |
| App data fetching | React Query |
| App navigation | Expo Router |
| Hosting | Hetzner VPS (CPX21 £6/month to start) |

---

## Backend API Structure (summary)

```
POST /auth/register, /auth/login, /auth/refresh
POST /onboarding/start, /onboarding/message, /onboarding/confirm-goals
GET/POST/PUT/DELETE /goals
GET/POST/PUT/DELETE /habits
POST /habits/{id}/complete
GET /habits/heatmap
GET/PUT /nudges, /nudges/settings
POST /device/pair
GET /device/state
GET/POST /integrations/{name}/connect
GET/POST /review/current, /review/message
GET /analytics/summary, /analytics/patterns, /analytics/likelihood
```

WebSocket events: LAYOUT_UPDATE, NUDGE, HABIT_COMPLETED, HEARTBEAT, TOUCH_EVENT, NUDGE_ACKNOWLEDGED

---

## Data & AI Context

Every Claude API call uses a pre-built context object — never raw conversation history (too expensive):

```python
user_context = {
  "profile": { name, personality_summary, motivation_style, known_blockers },
  "current_cycle": { goal, start_date, end_date, likelihood_score, milestones, weeks_remaining },
  "today": { schedule, non_negotiables_completed, non_negotiables_pending, calendar_events },
  "recent_behaviour": { last_7_days_habit_completion, nudge_response_rate, patterns_identified, screen_time, steps, sleep },
  "nudge_history": { last_nudge_sent, category, cooldown_active }
}
```

Context is rebuilt nightly at 2am by a Celery worker and cached in Redis. Real-time events (habit completions, nudges sent) update the cache immediately. No DB queries at inference time.

---

## Integrations Roadmap

**Phase 1 (launch):** Google Calendar, Apple Calendar (EventKit), Apple Health (HealthKit), Google Fit
**Phase 2:** Android UsageStats, iOS Screen Time (via Apple Shortcuts webhook), Spotify, Todoist
**Phase 3:** Open Banking (Plaid/TrueLayer), Strava, Oura/Whoop, IFTTT webhooks

**iOS Screen Time note:** Apple does not expose this to third-party apps. Workaround is Apple Shortcuts automation — user creates a shortcut that POSTs to a personal Gravity webhook URL when app usage threshold is hit. Opt-in, manual, takes 90 seconds to set up.

---

## Key Platform Constraints

| Constraint | Reality |
|---|---|
| iOS Screen Time | Blocked natively. Apple Shortcuts webhook only. |
| iOS background execution | ~15 min minimum interval. Throttled by OS. |
| Android OEM battery killing | Xiaomi/Huawei/OnePlus kill background apps. Must prompt whitelist. |
| E-ink full refresh | 1.5–2.5s with flash. Design around it — never animate. |
| E-ink temperature | Sluggish <10°C. Indoor device only. |
| Round e-ink supply | Waveshare is primary source. Order before designing enclosure. |
| Circular touch overlays | Not standard. May need custom cut. Test early. |
| Claude API cost target | Must stay under £0.85/user/month. Context caching + call frequency controls. |

---

## What NOT To Build First

- Do not build the app before the AI brain is validated
- Do not design the enclosure before confirming display dimensions with a physical unit
- Do not skip the layout JSON abstraction — hardcoded layouts require firmware flash for every UI change
- Do not put API keys in client-side code
- Do not build all integrations at once — Calendar + Health first, everything else Phase 2
- Do not premature-optimise Claude API costs — measure at 50 real users first

---

## File Map

| File | Contents |
|---|---|
| `PRODUCT.md` | Full product vision, onboarding flow, 6-month cycle, build roadmap |
| `HARDWARE.md` | Physical dimensions, display spec, BOM, enclosure, power, sensors |
| `SOFTWARE_ARCH.md` | System diagram, backend architecture, API structure, WebSocket events, data model |
| `AI_BEHAVIOUR.md` | Onboarding phases in full, nudge philosophy, 6-month review, learning model |
| `UI_UX.md` | Device screen states, app screens, design tokens, component library, interaction principles |
| `CONSTRAINTS.md` | Budget, platform limits, e-ink constraints, offline behaviour, AI cost tiers |
| `CLAUDE.md` | This file — master context for any AI working on this project |

---

## How To Use This File

**If you are helping with the AI conversation engine (Stage 0):**
Read the onboarding phases section above. The goal is a Python script that runs the 5-phase conversation, extracts structured data, and stores a profile JSON. Use Ollama locally or the Claude artifact sandbox for zero cost.

**If you are helping with the backend:**
Read SOFTWARE_ARCH.md in full. FastAPI + PostgreSQL + Redis + Celery. WebSocket for real-time device/app communication. AI context object is pre-built and cached — never built at inference time.

**If you are helping with the device firmware:**
Read HARDWARE.md and the e-ink constraints in CONSTRAINTS.md. The device renders layout JSON → e-ink. It does not generate layouts. Circular mask must be applied on every render pass.

**If you are helping with the app:**
Read UI_UX.md in full. React Native (Expo). Dark mode only. Space Mono + Inter. One accent colour (PULSE #E8E8FF). No fills, no gradients, no icons.

**If you are helping with UI design:**
Read UI_UX.md. The device is circular — everything is radial. Three zones. One dominant element per screen. E-ink cannot animate. The app matches the device aesthetic — same world, richer surface.

**If you are making any AI-related decision:**
Read AI_BEHAVIOUR.md. The AI is not an assistant. It is the user's own intentions reflected back at them. Honest over comfortable. Specific over generic. Earned trust over constant presence.

---

## The One-Line Brief

> Gravity is the physical object that holds you to who you said you wanted to be.
