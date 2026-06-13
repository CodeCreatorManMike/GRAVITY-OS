# PRODUCT — GRAVITY

---

## Physical Design

gravity will be a small palm sized (cuffed palms of left and right hands) device, with a completely circular e ink display infront of it 
-> similiar look / feel of a kindle (not flat it will be a circle except for the portion where the screen in)
-> it will be made of mostly plastic but still be comfortable to hold for an extended period

---

## First Boot & Onboarding

-> users will unbox it 
-> boot it up. it will give a terminal loading old fashion style load up sequence that looks arcadey and nice
-> it will have a clean space station modern minimal look and feel (on e ink - so just black and white using negative space well) (similiar shape to a homepod mini but with a larger display (larger cur out of the circle))
-> the device will greet the user after doing its firmware install / whatever process it needs (such as connecting to wifi / the application)
-> then it will ask users to vocally explain there name, personality / ask about them / general knowledge -> goals, ambitions, hobbies. it will ask this in a structured clear and easy to get the right results from way
-> it will then ask the user about there activities what a general day is like (essentially try get data on their workflow (day))
-> it then, it asks th person what they would like to achieve in the next 6 months 
----> now, it will evaluate the realism and likely hood of this goal and structure time into there day actually see if it is possible and likely
----> determine the likelyness of each goal
----.> if a user has no goals it will use the data about the user to ask more / find out hobbies interests / small good things to start getting the user engaged with the idea of the item 
-----> then once it has determined your 6 month goal; it breaks the goal down. determines if it has clarifying questions to better understand the goal it should ask
-----> then it should desgign a tailored ui itself for this purpose using a system which would match the previous brand / ui aesthetics mentioned.
------> and break down the most engaging gameified / useful most of all way to accomplish that goal. fit it in the schedule the budget
------> it will then ask for specific application permissions or anything else it needs to do
-----> this will also then be in tandem with the application arranging ang building its widgets / view / goal brakdown

--> in that process it will ask you / help you build a list of non-negiotables that a user wants to do day in and day out
--> (eg: brush teeth, eat 3 meals a day, walk 2kms etc. and enforce those things)
----> all these diagrams and things need to be in the aesthetics of the black and white e ink futuristic space ship console look
----> things like github heatmaps and nice aesthetic ways to show when a user has done things, improved

---> the value, the ui itself needs to be build circular it needs to be designed with that in mind
----> it needs to prioritise showing users the value it actually provides
----> it needs to stop you from smoking / doom scrolling on tik tok / overspending if you have a savings goal / make you go gym
----> it neeeds to use your digital footprint to ensure that you are getting closer to your goals doing yoru tasks etc...

----> there is potential to install a microphone / camera wherever it is setup to help with this (not necessarily concrete for now)

--> it needs to repeat this cycle liek humans do.. using data from the best proven ways to stay on track and complete goals it needs to buidl itself adapt with the user grow and actually provide use for them

---

## The 6-Month Cycle

Gravity operates on a 6-month rhythm — the core engine of the product.

Every 6 months, the device initiates a full re-onboarding session:
- Reviews what was achieved vs what was planned in the previous cycle
- Shows the user honest data — streaks, completions, avoidance patterns, progress
- Asks what has changed — job, lifestyle, priorities, new goals
- Re-evaluates the user's current capacity and schedule
- Sets a new 6-month goal structure with updated non-negotiables
- Rebuilds the UI to reflect the new cycle

This cycle mirrors how humans actually operate — semester-length sprints where habits solidify, goals evolve, and motivation needs a reset. It is not arbitrary. It is the product's heartbeat.

Between cycles, the device learns. It notices what the user does vs what they said they would do. It adjusts nudge frequency, timing, and intensity accordingly. By cycle 3, it knows the user better than most people in their life.

---

## AI Behaviour & Intelligence Layer

The AI layer is the brain of Gravity. It runs on Claude API (or equivalent) via the companion app backend.

### Onboarding Intelligence
- Asks open, natural questions — not forms
- Extracts structured data from natural language answers
- Identifies hidden goals the user didn't explicitly state
- Detects unrealistic planning and challenges it with data ("most people with your schedule achieve X, not Y")
- Assigns a likelihood score to each goal (internal — shown only when helpful)

### Daily Intelligence
- Knows the user's schedule, habits, location patterns, and digital behaviour
- Determines the optimal moment to surface a nudge — not just a time, but a context
- Distinguishes between a bad day and a pattern — one missed gym session vs five in a row
- Escalates intervention when patterns emerge — from gentle nudge to direct callout
- Celebrates wins without being performative — brief, specific, earned

### Procrastination & Bad Habit Detection
- Integrates with phone screen time data (Android) or Apple Shortcuts automation (iOS workaround)
- Detects doom scrolling by monitoring app usage duration spikes against the user's own baseline
- Detects smoking / bad habits via user self-report triggers or time-of-day patterns the user defines
- If the user has a savings goal — flags unnecessary spending via open banking integration (optional)
- If the user has a fitness goal — cross-references with Health/Google Fit step/workout data
- Interventions are delivered to the e-ink screen directly — not as a phone notification that gets ignored

### Adaptation Engine
- Tracks completion rates per task type, time of day, day of week
- Learns which nudge styles work for this user (direct vs gentle vs data-led)
- Gradually shifts the schedule toward what the user actually does — not what they wish they did
- Flags when a goal needs to be restructured (3 weeks of consistent failure = conversation, not punishment)

---

## Hardware Specification (Target)

### Core Components
- **Display:** Round e-ink panel — target 3.7" to 4.2" circular, 300 DPI, black and white
- **Processor:** ESP32-S3 (WiFi + Bluetooth built in, low power, sufficient for display driving + API calls)
- **Memory:** 8MB PSRAM + 16MB Flash (enough to cache daily schedule and UI state offline)
- **Connectivity:** WiFi 802.11 b/g/n, Bluetooth 5.0 (for phone pairing)
- **Power:** USB-C charging, 1000–2000mAh LiPo battery (target 7–14 day battery life leveraging e-ink's low refresh power draw)
- **Audio (Phase 2):** MEMS microphone for voice onboarding and check-ins
- **Camera (Phase 3 / TBD):** Small wide-angle lens for presence detection — determines if user is at desk
- **Physical inputs:** Single tactile button or capacitive touch ring around the display bezel
- **Form factor:** Circular, sits flat on desk or bedside table, slight wedge angle for readability

### Why ESP32 over Raspberry Pi
- Raspberry Pi Zero 2W: ~£15, runs Linux, more capable but higher power draw, longer boot time, overkill for display + API calls
- ESP32-S3: ~£4, instant on, deep sleep mode extends battery to weeks, purpose-built for IoT exactly like this
- For a prototype: start with Raspberry Pi Zero 2W for speed of development, migrate to ESP32-S3 for v1 hardware

### Estimated BOM (Prototype)
| Component | Estimated Cost |
|---|---|
| Round e-ink display (3.7") | £12–18 |
| Raspberry Pi Zero 2W (proto) | £15 |
| LiPo battery 1500mAh | £6 |
| USB-C charging module | £2 |
| Enclosure (3D printed) | £3–8 filament |
| Misc (wiring, buttons, connectors) | £5 |
| **Total prototype BOM** | **~£43–54** |

Target retail BOM at volume: sub-£25. Target retail price: £79–£99.

---

## Software Architecture

### System Overview
```
[Gravity Device] <--WiFi/BT--> [Companion App] <--HTTPS--> [Backend API] <---> [Claude API]
                                      |
                              [Integrations Layer]
                              - Google Calendar
                              - Apple Health / Google Fit
                              - Open Banking (optional)
                              - Screen Time (Android API / iOS Shortcuts)
                              - Spotify (mood/focus signals)
```

### Backend
- Language: Python (FastAPI)
- Hosting: VPS (Hetzner or DigitalOcean) — £4–6/month to start
- Database: PostgreSQL (user profiles, goal data, habit logs, nudge history)
- AI: Claude API via Anthropic SDK — all reasoning, nudge generation, goal evaluation, UI generation instructions

### Companion App
- Framework: React Native (single codebase, iOS + Android)
- Role: Integration hub, data relay to device, rich visual dashboard
- Displays: goal progress, heatmaps, streaks, weekly reviews, 6-month cycle data
- Also receives nudges when device is not in view

### Device Firmware
- Language: MicroPython (ESP32) or Python (RPi Zero 2W prototype)
- Responsibilities: Render e-ink UI, poll backend for updates, push button events, manage display refresh cycles
- Offline mode: Caches today's schedule and non-negotiables locally — functions without internet for basic display

### E-ink UI Generation
- The AI generates layout instructions (not raw pixels) — a structured JSON describing what to show
- A local renderer on the device interprets JSON → draws to e-ink
- This allows the AI to adapt the UI per user goal without firmware updates
- UI components: circular progress rings, heatmap grids, text prompts, status glyphs, streak counters

---

## UI & Visual Language

### Core Aesthetic
- Black and white only — e-ink constraint becomes a design strength
- Inspired by: space station control panels, terminal UIs, Kindle typography, NASA mission displays
- Heavy use of negative space — the circle is mostly empty, content is precise and intentional
- Monospace or geometric sans-serif typefaces only
- No gradients, no fills — outlines, dots, dashes, glyphs

### Circular Display Design Principles
- The circle is not a rectangle with corners removed — UI is designed radially
- Progress is shown as arcs around the perimeter
- The centre is reserved for the primary message — one thing at a time
- Quadrants used for secondary data — top, left, right, bottom zones each have a role
- Heatmaps render as circular dot-grids — aesthetic nod to GitHub contribution graphs

### Screen States
- **Idle / ambient:** Time, date, one metric (e.g. streak count, steps today)
- **Morning brief:** Today's non-negotiables, top priority task, one focus prompt
- **Active nudge:** Full screen intervention — direct message, no decoration
- **Goal view:** Circular progress ring for current 6-month goal, breakdown below
- **Weekly heatmap:** Dot grid of the past 7 days per habit category
- **Check-in prompt:** Question from AI, answered via app or voice

---

## Integrations Roadmap

### Phase 1 (Launch)
- Google Calendar / Apple Calendar (EventKit)
- Apple Health / Google Fit (steps, workouts, sleep)
- Manual habit logging via companion app

### Phase 2
- Android Screen Time API (app usage data)
- iOS Screen Time workaround via Apple Shortcuts automation
- Spotify (detect music = working? = log focus time)
- Google Tasks / Todoist

### Phase 3
- Open Banking (Plaid or TrueLayer) for spending vs savings goal tracking
- Microphone for voice check-ins and ambient presence detection
- IFTTT / Zapier webhook support for power users
- Camera (presence detection — is the user actually at their desk?)

---

## Monetisation

- **Device:** One-time hardware purchase £79–£99
- **Subscription:** £4.99/month or £39/year for AI features (Claude API calls, backend, sync)
- **Free tier:** Device works as a basic habit tracker without subscription — AI features require plan
- **No ads. Ever.**

---

## What Gravity Is Not

- Not another to-do app
- Not a notification machine that gets ignored
- Not a gamification gimmick with streaks for streaks' sake
- Not a journaling app
- Not a smartwatch competitor
- Not a phone replacement

Gravity is a physical object with a purpose. It sits on your desk or bedside table. It exists in your physical space. It has one job: making sure you become the person you said you wanted to be.

---

## Build Roadmap (Prototype to V1)

### Stage 0 — Brain First (Now, laptop only)
- Build the onboarding conversation flow in Python (terminal)
- Claude API integration — goal intake, evaluation, breakdown
- Store structured user profile as JSON
- Test the AI logic with real inputs

### Stage 1 — App Shell
- React Native companion app skeleton
- FastAPI backend with PostgreSQL
- Basic goal tracking, manual habit logging
- No device yet — validate the AI + app loop first

### Stage 2 — Device Prototype
- Raspberry Pi Zero 2W + round e-ink display
- MicroPython firmware — render JSON layout instructions to screen
- WiFi connection to backend
- Daily schedule display, nudge delivery

### Stage 3 — Integration Layer
- Calendar sync
- Health data sync
- Screen time hooks (Android first)
- Refine nudge timing and content with real usage data

### Stage 4 — Hardware V1
- Migrate from RPi to ESP32-S3
- 3D print enclosure v1
- USB-C charging integration
- Battery optimisation

### Stage 5 — Polish & Launch
- Final enclosure design (injection moulded or premium 3D print)
- App store submission
- Waitlist / early access campaign
