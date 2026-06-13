# SOFTWARE ARCHITECTURE — GRAVITY

---

## Guiding Principles

- **Backend owns the brain.** All AI reasoning runs server-side via Claude API. The device and app are intelligent displays, not compute nodes. This keeps the device cheap, battery efficient, and upgradeable without hardware changes.
- **Fast where it matters.** Nudges and UI updates are pushed via WebSocket — the device never waits to poll. A nudge arrives in under 500ms of the backend deciding to send it.
- **Seamless onboarding.** Setup is split intelligently — the device handles what a physical object does best (presence, personality, first impression), the app handles what a phone does best (typing, permissions, integrations, rich input).
- **Offline graceful.** The device caches enough state to function without internet. It never shows an error screen — it always shows something useful.
- **Scales cheaply.** Architecture is chosen to run on a £6/month VPS for the first 1,000 users, with a clear path to horizontal scaling beyond that.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GRAVITY SYSTEM                           │
│                                                                 │
│  ┌──────────────┐         ┌──────────────────────────────────┐  │
│  │              │ WiFi    │         BACKEND (FastAPI)        │  │
│  │   GRAVITY    │◄───────►│                                  │  │
│  │   DEVICE     │WebSocket│  ┌─────────────┐  ┌──────────┐  │  │
│  │  (ESP32-S3)  │         │  │  AI Engine  │  │ Database │  │  │
│  │              │         │  │ Claude API  │  │Postgres  │  │  │
│  └──────┬───────┘         │  └──────┬──────┘  └──────────┘  │  │
│         │ Bluetooth       │         │                         │  │
│         │ (pairing +      │  ┌──────▼──────────────────────┐ │  │
│         │  urgent nudge   │  │     Integration Layer       │ │  │
│         │  fallback)      │  │  Calendar │ Health │ Banking │ │  │
│  ┌──────▼───────┐         │  │  Screen Time │ Spotify      │ │  │
│  │  COMPANION   │ HTTPS / │  └─────────────────────────────┘ │  │
│  │     APP      │WebSocket│                                  │  │
│  │ React Native │◄───────►│                                  │  │
│  └──────────────┘         └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Onboarding Flow — Split by Best Device

Onboarding is the most important experience in Gravity. It must feel effortless, intelligent, and like the product is already paying attention. Each step is assigned to whichever surface — device or app — handles it best.

### Full Onboarding Sequence

```
DEVICE                              APP
──────                              ───
Boot sequence (terminal animation)
↓
WiFi setup prompt
  → User enters WiFi on app ────────► App sends credentials to device
↓
Device connects, syncs firmware
↓
Gravity intro sequence on e-ink
(animated welcome, product philosophy
 in 3 screens — sets the tone)
↓
"Download the Gravity app to continue"
  (QR code on e-ink screen) ────────► User scans, app opens, accounts linked
                                      ↓
                                      Account creation (email / Apple / Google)
                                      ↓
                                      Name + basic profile
                                      (typed — faster on phone)
                                      ↓
                                      Permissions flow:
                                      - Calendar access
                                      - Health / fitness data
                                      - Notification permissions
                                      - Screen time (Android) /
                                        Shortcuts setup (iOS)
                                      ↓
                                      "Tell Gravity about yourself"
                                      Conversational AI chat interface —
                                      Claude asks questions, user types.
                                      Topics covered:
                                      - Personality / how they work
                                      - Current daily routine
                                      - What they want to achieve
                                        in the next 6 months
                                      - What gets in their way
                                      - Non-negotiables they want enforced
                                      ↓
                                      AI evaluates goals —
                                      shows likelihood scores,
                                      suggests adjustments,
                                      user confirms or refines
                                      ↓
                                      AI builds personalised schedule +
                                      goal breakdown — shown in app
                                      ↓
                                      "Gravity is ready"
↓
Device receives personalised
UI layout from backend.
First real screen renders —
tailored to this user's goal.
Onboarding complete.
```

### Why this split works
- Device handles: physical presence, first impression, WiFi setup, QR handoff, final reveal
- App handles: account creation, permissions (OS-level prompts must happen on phone), deep conversational input (typing > voice for nuanced answers), integration auth flows
- Neither surface is asked to do something it's bad at

---

## Data Architecture

### What Gets Collected

| Data Type | Source | Frequency | Stored Where |
|---|---|---|---|
| Goal structure | Onboarding / 6-month review | Per cycle | PostgreSQL |
| Non-negotiables list | Onboarding / user edits | On change | PostgreSQL |
| Habit completion logs | App manual toggle / integrations | Daily | PostgreSQL |
| Calendar events | Google / Apple Calendar API | Hourly sync | PostgreSQL (today only cached on device) |
| Step count / workouts | Apple Health / Google Fit | Daily sync | PostgreSQL |
| Sleep data | Apple Health / Google Fit | Daily sync | PostgreSQL |
| App usage / screen time | Android UsageStats API / iOS Shortcuts | Daily sync | PostgreSQL |
| Spending data | Open Banking (opt-in) | Daily sync | PostgreSQL |
| Nudge log | Backend generated | Per event | PostgreSQL |
| User responses to nudges | App / device touch | Per event | PostgreSQL |
| AI conversation history | Onboarding + check-ins | Per session | PostgreSQL (summarised, not raw) |
| Device telemetry | Device firmware | On event | PostgreSQL |

### Data Retention Policy
- Raw integration data (steps, calendar): 90 days rolling
- Habit completion logs: indefinite (core product value)
- Nudge log + response data: indefinite (AI learning)
- AI conversation transcripts: summarised after each session, raw deleted after 7 days
- Goal history: indefinite (6-month cycle archives)

### Where Data Lives

```
PostgreSQL (primary store)
├── users
├── goals                    ← current + historical per cycle
├── non_negotiables
├── habits
├── habit_logs               ← daily completion records
├── nudges                   ← every nudge sent + user response
├── schedule_blocks          ← today's schedule, rebuilt nightly
├── integration_tokens       ← encrypted OAuth tokens
├── ai_summaries             ← condensed user context for AI calls
├── device_state             ← current e-ink layout instructions
└── cycle_reviews            ← 6-month review snapshots

Redis (ephemeral / fast access)
├── active_websocket_sessions
├── today_schedule_cache     ← pre-built for instant device delivery
├── user_context_cache       ← AI context snapshot, TTL 1 hour
└── nudge_cooldown_keys      ← prevent nudge spam per user per category
```

---

## Backend Architecture

### Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI — async, fast, clean OpenAPI docs auto-generated
- **Database:** PostgreSQL via SQLAlchemy (async)
- **Cache / pubsub:** Redis
- **WebSocket:** FastAPI native WebSocket support
- **Task queue:** Celery + Redis — for scheduled jobs (nightly AI review, integration syncs, 6-month cycle trigger)
- **AI:** Anthropic Claude API via `anthropic` Python SDK
- **Auth:** JWT tokens, OAuth2 for integrations
- **Hosting:** Hetzner VPS (CPX21 — 3 vCPU, 4GB RAM, £6/month) → scales to CPX31 at 1k+ users

### Core Backend Services

```
backend/
├── api/
│   ├── auth.py              ← registration, login, JWT
│   ├── onboarding.py        ← goal intake, AI evaluation, profile build
│   ├── goals.py             ← CRUD for goals + milestones
│   ├── habits.py            ← non-negotiables, habit logs
│   ├── nudges.py            ← nudge history, sensitivity settings
│   ├── device.py            ← device pairing, state, UI layout delivery
│   ├── integrations.py      ← OAuth flows, data ingestion endpoints
│   └── review.py            ← 6-month cycle review trigger + flow
├── ai/
│   ├── engine.py            ← core Claude API wrapper
│   ├── onboarding.py        ← onboarding conversation logic
│   ├── goal_evaluator.py    ← likelihood scoring, schedule feasibility
│   ├── nudge_generator.py   ← decides when + what to nudge
│   ├── ui_composer.py       ← generates e-ink layout JSON per user
│   ├── pattern_detector.py  ← identifies behavioural patterns over time
│   └── review_generator.py  ← 6-month cycle analysis + new goal setup
├── workers/
│   ├── nightly_review.py    ← runs at 2am — rebuilds schedule, AI context
│   ├── integration_sync.py  ← pulls calendar, health, screen time data
│   ├── nudge_scheduler.py   ← evaluates nudge conditions every 15 mins
│   └── cycle_trigger.py     ← detects 6-month cycle end, initiates review
├── integrations/
│   ├── google_calendar.py
│   ├── apple_health.py
│   ├── google_fit.py
│   ├── android_screen_time.py
│   ├── ios_shortcuts_receiver.py
│   ├── spotify.py
│   ├── open_banking.py
│   └── todoist.py
└── websocket/
    ├── connection_manager.py ← manages active device + app WS sessions
    └── event_dispatcher.py   ← routes events to correct connected clients
```

---

## AI Engine Design

### Context Architecture
Every Claude API call is built from a layered context object — never raw conversation history (too expensive, too slow):

```python
user_context = {
    "profile": {
        "name": "...",
        "personality_summary": "...",   # AI-generated from onboarding
        "daily_routine": "...",
        "known_blockers": [...],         # what gets in their way
    },
    "current_cycle": {
        "goal": "...",
        "start_date": "...",
        "end_date": "...",
        "likelihood_score": 0.73,
        "milestones": [...],
        "weeks_remaining": 14,
    },
    "today": {
        "schedule": [...],
        "non_negotiables_completed": [...],
        "non_negotiables_pending": [...],
        "calendar_events": [...],
    },
    "recent_behaviour": {
        "last_7_days_habit_completion": {...},
        "nudge_response_rate": 0.61,
        "patterns_identified": [...],    # pre-computed by pattern_detector
        "screen_time_yesterday": {...},
        "steps_yesterday": 4200,
        "sleep_last_night": "6h 20m",
    },
    "nudge_history": {
        "last_nudge_sent": "...",
        "last_nudge_category": "fitness",
        "cooldown_active": False,
    }
}
```

This context is rebuilt nightly by the worker and cached in Redis. Intra-day events (habit completions, new nudge sent) update the cache in real time. Each AI call pulls the cached context — no database queries at inference time.

### AI Call Types

| Call Type | Trigger | Avg Tokens | Frequency |
|---|---|---|---|
| Onboarding conversation turn | User message during setup | ~2,000 | Once per user |
| Goal evaluation | Onboarding complete | ~3,000 | Once per cycle |
| UI layout generation | Nightly / on goal change | ~1,500 | Daily |
| Nudge decision | Every 15 min worker run | ~800 | Up to 10x/day |
| Nudge content generation | When nudge decision = true | ~500 | Per nudge |
| Pattern detection | Nightly worker | ~2,000 | Daily |
| 6-month review generation | Cycle end | ~5,000 | Per cycle |
| Check-in conversation turn | User initiates | ~1,500 | On demand |

### Nudge Decision Logic

The nudge worker runs every 15 minutes. For each active user it evaluates:

```
1. Is a nudge cooldown active for this user? → skip
2. Is it within the user's defined quiet hours? → skip
3. For each nudge category (fitness, focus, habit, spending, sleep):
   a. Pull relevant signals from context cache
   b. Check trigger conditions (rule-based first, fast):
      - Fitness: no workout logged + gym was scheduled + >2 hours since last check
      - Focus: screen time spike detected above user baseline
      - Habit: non-negotiable not completed by its expected time window
      - Spending: transaction detected that conflicts with savings goal
      - Sleep: current time > user's target bedtime by 30+ mins
   c. If any rule fires → send to Claude for nudge content generation
   d. Claude decides: nudge or not, what to say, how direct to be
4. Send nudge via WebSocket to device (primary) + app (secondary)
5. Log nudge, set cooldown (minimum 90 mins between nudges, category-aware)
```

### UI Layout Generation

The AI does not generate pixels. It generates a **layout instruction JSON** which the device firmware and app both interpret independently:

```json
{
  "screen": "morning_brief",
  "generated_at": "2025-06-12T07:00:00Z",
  "layout": {
    "centre": {
      "type": "text",
      "content": "FOCUS: Finish API spec",
      "size": "large",
      "weight": "bold"
    },
    "perimeter_arc": {
      "type": "progress_arc",
      "value": 0.34,
      "label": "Goal: 34%"
    },
    "top_zone": {
      "type": "text",
      "content": "WED 12 JUN",
      "size": "small"
    },
    "bottom_zone": {
      "type": "checklist",
      "items": ["Gym", "3 meals", "2km walk"],
      "completed": [true, false, false]
    },
    "mid_ring": {
      "type": "streak_glyph",
      "value": 14,
      "label": "day streak"
    }
  }
}
```

This means the e-ink UI can be updated, personalised, and improved without any firmware changes to the device.

---

## WebSocket Event System

All real-time communication between backend ↔ device and backend ↔ app runs over persistent WebSocket connections.

### Event Types

```
Backend → Device
├── LAYOUT_UPDATE          ← new e-ink layout JSON
├── NUDGE                  ← immediate intervention message
├── CYCLE_START            ← 6-month review initiated
└── FIRMWARE_UPDATE_AVAILABLE

Backend → App
├── LAYOUT_SYNC            ← mirror of what device is showing
├── NUDGE_SENT             ← log update
├── HABIT_REMINDER         ← gentle in-app prompt
├── PATTERN_ALERT          ← new pattern identified
├── INTEGRATION_ERROR      ← calendar/health sync failed
└── CYCLE_REVIEW_READY     ← 6-month review data available

Device → Backend
├── TOUCH_EVENT            ← user tapped, swiped, long pressed
├── NUDGE_ACKNOWLEDGED     ← user responded to nudge
├── HABIT_COMPLETED        ← user marked habit done on device
└── HEARTBEAT              ← keep-alive every 60s

App → Backend
├── HABIT_COMPLETED
├── GOAL_UPDATED
├── INTEGRATION_CONNECTED
├── CHECK_IN_MESSAGE       ← user initiated AI conversation
└── SETTINGS_CHANGED
```

### Connection Resilience
- Device reconnects automatically on WiFi drop — exponential backoff (2s, 4s, 8s... max 5 min)
- On reconnect, backend replays any missed events from the last 24 hours
- If WebSocket unavailable — device falls back to polling every 5 minutes
- Nudges that failed to deliver are retried up to 3 times before being logged as missed

---

## API Structure

### REST Endpoints (HTTPS)

```
Auth
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
DELETE /auth/logout

Onboarding
POST   /onboarding/start
POST   /onboarding/message        ← conversational turn
POST   /onboarding/confirm-goals
GET    /onboarding/status

Goals
GET    /goals                     ← current cycle goals
POST   /goals
PUT    /goals/{id}
DELETE /goals/{id}
GET    /goals/history             ← previous cycles

Habits
GET    /habits
POST   /habits
PUT    /habits/{id}
DELETE /habits/{id}
POST   /habits/{id}/complete      ← log completion
GET    /habits/heatmap            ← last 90 days grid data

Nudges
GET    /nudges                    ← full log
PUT    /nudges/{id}/response      ← user acted / dismissed
PUT    /nudges/settings           ← sensitivity per category

Device
POST   /device/pair               ← link device to account
GET    /device/state              ← current layout + status
POST   /device/heartbeat
GET    /device/firmware           ← latest firmware version info

Integrations
GET    /integrations              ← connected list + status
POST   /integrations/{name}/connect
DELETE /integrations/{name}/disconnect
POST   /integrations/health/sync  ← manual trigger
POST   /integrations/calendar/sync

Review (6-month cycle)
GET    /review/current            ← active cycle summary
GET    /review/{cycle_id}         ← historical cycle
POST   /review/start              ← trigger new cycle
POST   /review/message            ← conversational turn during review

Analytics
GET    /analytics/summary         ← weekly/monthly rollup
GET    /analytics/patterns        ← AI-identified patterns
GET    /analytics/likelihood      ← current goal likelihood score
```

---

## Integration Layer

### Phase 1 — Launch

| Integration | Platform | Data Pulled | Method |
|---|---|---|---|
| Google Calendar | Android + iOS | Events, free/busy blocks | OAuth2 + Google Calendar API |
| Apple Calendar | iOS | Events, free/busy blocks | EventKit (via app) |
| Apple Health | iOS | Steps, workouts, sleep, heart rate | HealthKit (via app) |
| Google Fit | Android | Steps, workouts, sleep | Google Fit REST API |

### Phase 2

| Integration | Platform | Data Pulled | Method |
|---|---|---|---|
| Android Screen Time | Android | Per-app usage duration | UsageStatsManager API |
| iOS Screen Time | iOS | Per-app usage duration | Apple Shortcuts automation → webhook to backend |
| Spotify | Both | Listening patterns, focus playlist detection | Spotify Web API |
| Google Tasks / Todoist | Both | Task completion signals | REST API |

### Phase 3

| Integration | Platform | Data Pulled | Method |
|---|---|---|---|
| Open Banking | UK (Plaid / TrueLayer) | Transactions vs spending goal | OAuth2 + PSD2 API |
| IFTTT / Webhooks | Both | Custom user-defined triggers | Webhook receiver endpoint |
| Strava | Both | Workout data (richer than Health) | Strava API |
| Oura Ring / Whoop | Both | Sleep + recovery scores | Partner APIs |

### iOS Screen Time Workaround (Important)
Apple does not expose Screen Time data to third-party apps. The workaround:
1. User creates an Apple Shortcut on their phone — "When I use TikTok for more than 30 minutes, send a webhook to Gravity"
2. Gravity provides a personal webhook URL in the app
3. The Shortcut POSTs to that URL when triggered
4. Backend receives the signal, evaluates against goal context, fires nudge if appropriate

This is opt-in, takes 2 minutes to set up, and is explained clearly in the app with a one-tap Shortcut install link.

---

## Companion App Architecture

### Stack
- **Framework:** React Native (Expo) — single codebase, iOS + Android
- **State management:** Zustand — lightweight, no boilerplate
- **API calls:** React Query — caching, background refetch, optimistic updates
- **WebSocket:** Native WebSocket with reconnection logic
- **Local storage:** Expo SecureStore (tokens), AsyncStorage (cached state)
- **Navigation:** Expo Router (file-based)

### App ↔ Device Sync Model
- App maintains its own WebSocket connection to backend — independent of device
- App receives same layout JSON as device — renders circular preview on Home screen
- When user completes a habit in the app — optimistic update in UI, backend event dispatched, device layout updated within 2 seconds
- App is the primary surface for integrations setup — OS permission prompts live here

---

## Device Firmware Architecture

### Stack
- **Prototype:** MicroPython on Raspberry Pi Zero 2W
- **Production:** MicroPython or C++ (Arduino framework) on ESP32-S3

### Firmware Responsibilities
```
firmware/
├── main.py                  ← boot sequence, init, main loop
├── wifi.py                  ← connection management, reconnect logic
├── websocket_client.py      ← persistent WS connection to backend
├── display/
│   ├── driver.py            ← low-level e-ink SPI driver
│   ├── renderer.py          ← interprets layout JSON → draws to screen
│   ├── components.py        ← arc, heatmap, text, glyph primitives
│   └── fonts/               ← monospace bitmap fonts
├── touch.py                 ← capacitive touch interrupt handler
├── imu.py                   ← accelerometer — orientation detection
├── cache.py                 ← local state storage (today's layout)
├── power.py                 ← deep sleep management, battery monitor
└── ota.py                   ← over-the-air firmware update handler
```

### Boot Sequence
```
Power on
↓
Run terminal-style boot animation (cached locally — no network needed)
↓
Connect to WiFi (stored credentials) — show connecting glyph
↓
Open WebSocket to backend
↓
Pull latest layout JSON from backend
↓
Render first real screen
↓
Enter main loop:
  - Listen for WebSocket events
  - Handle touch interrupts
  - Send heartbeat every 60s
  - Sleep display between refreshes (partial refresh every 15 min ambient)
```

### OTA Updates
- Backend maintains latest firmware version number
- On each heartbeat response, backend includes `latest_firmware_version`
- If device version < latest: backend sends `FIRMWARE_UPDATE_AVAILABLE` event
- Device downloads new firmware in background, applies on next idle restart
- User sees "System updated" briefly on e-ink — no interaction required

---

## Infrastructure & Scaling

### Initial Setup (0–1,000 users)
```
Hetzner CPX21 VPS — £6/month
├── FastAPI backend (gunicorn + uvicorn workers)
├── PostgreSQL
├── Redis
├── Celery workers (2)
└── Nginx reverse proxy + SSL (Let's Encrypt)
```

### Scale Path (1,000–10,000 users)
```
Hetzner CPX31 (£12/month) or split:
├── App server (CPX21)
├── Database server (CPX21 + daily backups)
├── Redis (managed — Upstash free tier → paid)
└── Celery workers scaled to demand
```

### Cost Model Per User Per Month (at scale)
| Item | Cost |
|---|---|
| Claude API (est. 50 AI calls/day avg) | ~£0.80 |
| Backend compute (per user share) | ~£0.05 |
| Database storage | ~£0.02 |
| Integration API calls | free (within limits) |
| **Total per user** | **~£0.87/month** |
| Subscription price | £4.99/month |
| **Gross margin** | **~83%** |

---

## Security & Privacy

- All data encrypted at rest (PostgreSQL encryption, AES-256)
- All transit encrypted (TLS 1.3)
- OAuth tokens stored encrypted, never logged
- AI context sent to Claude API contains no PII beyond first name — goals and behaviours only
- Users can export all their data at any time (GDPR compliance)
- Users can delete their account — all data purged within 24 hours
- Open Banking integration is opt-in, read-only, and can be revoked instantly
- Device WebSocket authenticated via JWT — token rotated every 24 hours
- No data sold. No third-party analytics SDKs in the app.
