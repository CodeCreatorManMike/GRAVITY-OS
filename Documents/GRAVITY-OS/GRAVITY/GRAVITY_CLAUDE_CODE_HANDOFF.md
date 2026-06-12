# GRAVITY — Claude Code Handoff Document
**Date:** June 13, 2026  
**Handoff from:** Claude (claude.ai chat)  
**Handoff to:** Claude Code  
**Repo:** https://github.com/CodeCreatorManMike/GRAVITY-OS  
**Local path:** ~/Documents/GRAVITY-OS/GRAVITY  
**Dev:** Michael Jones, Junior Technical Analyst, London, age 20, solo founder  

---

## What Is Gravity

Gravity is a physical AI-powered goal tracking device. Circular display (~71mm, 2.8" round IPS LCD ST7701S). Sits on a desk or bedside table. Runs a 6-month goal cycle. Learns user behaviour and nudges them when they drift from their goals.

**Three surfaces:**
1. **Device** — circular display, physical object on desk
2. **Companion app** — React Native, iOS + Android (not built yet)
3. **Backend** — Python FastAPI (not built yet)

**Core principle: The AI brain is the product. Hardware is the delivery mechanism.**

---

## Development Environment

- MacBook Air (Apple Silicon)
- Python 3.12.3
- Virtual environment at `~/Documents/GRAVITY-OS/GRAVITY/.venv`
- Always activate with: `source .venv/bin/activate`
- AI provider: Groq free tier (llama-3.3-70b-versatile) — key in `.env`
- No Ollama, no Claude API yet (production only)
- Git remote: https://github.com/CodeCreatorManMike/GRAVITY-OS

---

## Current Project Structure

```
GRAVITY/
├── .env                          ← API keys (gitignored)
├── .gitignore
├── requirements.txt
├── run.py                        ← entry point for onboarding
├── core/
│   ├── ai_client.py              ← AI abstraction (Groq/Anthropic swap)
│   ├── onboarding.py             ← 5-phase onboarding conversation engine
│   ├── profile.py                ← UserProfile Pydantic model + save/load
│   ├── nudge_engine.py           ← nudge decision + content pipeline
│   └── prompts/
│       ├── phase1_identity.txt
│       ├── phase2_routine.txt
│       ├── phase3_goal.txt
│       ├── phase4_nonneg.txt
│       ├── phase5_feedback.txt
│       ├── extract_profile.txt   ← silent extraction call
│       ├── nudge_decision.txt
│       └── nudge_content.txt
├── profiles/
│   └── michael.json              ← real profile from completed onboarding
├── simulator/
│   ├── display/
│   │   ├── __init__.py
│   │   ├── primitives.py         ← drawing library (port of gravity-build.js)
│   │   ├── screens.py            ← Direction A screen renders
│   │   ├── gravity_sim.py        ← Pygame live simulator window
│   │   └── fonts/
│   │       ├── JetBrainsMono-Regular.ttf
│   │       ├── JetBrainsMono-Bold.ttf
│   │       ├── JetBrainsMono-Medium.ttf
│   │       └── JetBrainsMono-Light.ttf
│   ├── device_sim.py             ← stub (not built)
│   ├── display_renderer.py       ← stub (not built)
│   └── nudge_tester.py           ← stub (not built)
└── tests/
    ├── test_onboarding.py        ← stub
    ├── test_profile_extraction.py← stub
    └── test_nudge_logic.py       ← stub
```

---

## What Has Been Built — Completed Checklist

### Stage 0 — AI Brain ✅ COMPLETE

- [x] Python 3.12.3 confirmed
- [x] Virtual environment set up and working
- [x] Git repo initialised and pushed to GitHub
- [x] Full project folder structure created
- [x] All dependencies installed (requirements.txt)
- [x] Groq API connected and tested (llama-3.3-70b-versatile)
- [x] `ai_client.py` — provider abstraction layer (Groq now, Claude API later, swap without touching anything else)
- [x] `profile.py` — full UserProfile Pydantic schema with save/load to JSON
- [x] 5-phase onboarding prompts written and tuned
- [x] Silent extraction prompt (separates conversation from data extraction)
- [x] `onboarding.py` — full 5-phase conversation engine working end-to-end
- [x] Real onboarding run completed — michael.json profile saved
- [x] Nudge decision prompt + nudge content prompt written
- [x] `nudge_engine.py` — two-call pipeline (decision → content) working
- [x] Nudge engine tested across 4 scenarios (on-track, pending habits, no goal progress, cooldown)
- [x] `primitives.py` — Python port of gravity-build.js drawing system (PIL/Pillow)
- [x] `screens.py` — Direction A screens (A1-A7) rendered correctly
- [x] `gravity_sim.py` — Pygame live simulator window opening and displaying screens
- [x] Curved rim text working (top and bottom labels curving around circle)
- [x] Tick bezel, progress arcs, heatmap grid, brackets, scanlines all rendering

### Hardware Decisions ✅ LOCKED

- [x] Display: 2.8" round IPS LCD, ST7701S driver, 480×480px, capacitive touch
- [x] Prototype chip: Raspberry Pi Zero 2W (full Python, fast dev)
- [x] Production chip: ESP32-S3 (MicroPython, low power)
- [x] HARDWARE.md updated with full revised spec
- [x] Enclosure target: 90-100mm diameter, HomePod Mini proportions

---

## What Still Needs To Be Built — Remaining Checklist

### Immediate — Simulator Completion

- [ ] **Wire onboarding output → display generation**
  - After onboarding completes, AI generates a personalised layout JSON for this user's goal
  - Layout JSON drives which screen state is shown and what data populates it
  - The simulator should auto-load the profile and show the correct personalised screen
  
- [ ] **Live data integration in simulator**
  - A1 screen: real clock (done), real date (done), real streak from profile
  - A2 screen: real non-negotiables from profile, real top task
  - A4 screen: real goal, real likelihood score from profile
  - All screens should pull from `profiles/michael.json` dynamically

- [ ] **Touch/click navigation in simulator**
  - Left/right arrow keys work but need mouse click support too
  - Tap zones: centre tap = confirm, left half = previous, right half = next
  - Swipe simulation with mouse drag

- [ ] **Screen state system**
  - User's goals/habits should each have their own display screen
  - Navigation: swipe left/right through goal screens
  - Each goal generates its own A4-style progress screen
  - Non-negotiables each get an entry in A2-style morning brief

- [ ] **Profile-driven screen generation**
  - `layout_engine.py` — takes UserProfile, generates ordered list of screens to show
  - First screen: ambient/clock (A1)
  - Second screen: morning brief with user's actual non-negotiables (A2)
  - Following screens: one per goal/habit (A4 variants)
  - Last screen: heatmap of all habits (A5)
  - Night mode: wind-down screen after 10pm (A7)

- [ ] **Visual quality improvements**
  - Rim text needs to be slightly larger and bolder — currently too faint
  - Tick marks need heavier stroke weight
  - Overall ink weight needs to feel more confident/designed
  - Match the HTML reference screens more closely

### Stage 1 — Backend + App Shell (NOT STARTED)

- [ ] FastAPI backend scaffold
  - `main.py` entry point
  - `/onboard` endpoint — runs onboarding conversation via API
  - `/nudge` endpoint — evaluate and generate nudge for a user
  - `/layout` endpoint — generate device layout JSON for a user
  - `/profile` endpoint — get/update user profile
  - WebSocket connection manager for real-time device updates

- [ ] PostgreSQL database setup
  - User profiles table
  - Habit logs table
  - Nudge history table
  - Cycle/goal table

- [ ] Redis cache
  - User context cache (rebuilt nightly)
  - Nudge cooldown tracking

- [ ] React Native companion app shell
  - Basic navigation structure
  - Onboarding chat interface (replaces CLI terminal)
  - Device pairing screen
  - Goal view screen
  - Habits view screen

### Stage 2 — Hardware Prototype (NOT STARTED)

- [ ] Order hardware: RPi Zero 2W + 2.8" round ST7701S display + touch overlay
- [ ] SPI display driver for ST7701S on RPi
- [ ] `driver_hw.py` — hardware backend (replaces Pygame)
- [ ] Port `primitives.py` rendering to write to real display framebuffer
- [ ] WiFi connection to backend
- [ ] Touch input handler
- [ ] Boot sequence animation (terminal-style)
- [ ] OTA update mechanism

### Stage 3 — Integrations (NOT STARTED)

- [ ] Google Calendar sync
- [ ] Apple Calendar (via CalDAV)
- [ ] Apple Health / Google Fit (via React Native app → backend POST)
- [ ] iOS Screen Time (Apple Shortcuts webhook workaround)
- [ ] Android UsageStats API

### Stage 4 — ESP32 Migration (NOT STARTED)

- [ ] Port firmware from RPi Python to ESP32-S3 MicroPython
- [ ] 3D printed enclosure v1
- [ ] Battery + USB-C charging integration
- [ ] Deep sleep power management

### Stage 5 — Polish + Launch (NOT STARTED)

- [ ] App store submission (iOS + Android)
- [ ] Waitlist / early access
- [ ] Final enclosure (injection moulded or premium print)

---

## The Profile JSON (Real Data — Michael's Completed Onboarding)

```json
{
  "name": "michael",
  "personality_summary": "Michael is a driven and passionate individual who values creativity and self-improvement. He has a strong desire to achieve great things and stand out from the crowd. Despite his enthusiasm, he struggles with procrastination and distraction.",
  "motivation_style": "intrinsic",
  "energy_pattern": "evening",
  "self_awareness_level": "moderate",
  "failure_response": "analyse",
  "feedback_preference": "direct",
  "schedule": {
    "wake_time": "06:20",
    "sleep_time": "00:00",
    "peak_focus_windows": ["19:00-23:00"],
    "known_dead_zones": ["17:00-18:00"],
    "realistic_daily_hours": 4,
    "avoidance_behaviours": ["watching videos", "using social media", "calling girlfriend"]
  },
  "goal": {
    "statement": "build a prototype of my app, release at least one more single, and grow my music presence",
    "real_why": "to achieve great things and make a name for myself",
    "likelihood_score": 0.6,
    "milestone_structure": ["building a prototype", "releasing a single", "growing music presence"],
    "risk_factors": ["procrastination", "distraction", "burnout"]
  },
  "non_negotiables": ["working on my music", "making progress on my app", "upskilling/learning"],
  "cycle_start": "2026-06-12",
  "cycle_end": "2026-12-11",
  "onboarding_complete": true,
  "onboarding_phase": 5
}
```

---

## The Display System — How It Works

### Coordinate System
- Canvas: 360×360 pixels (matching JS viewBox)
- Centre: C = 180
- Angles: 0° = 12 o'clock, clockwise
- Palette: INK `#14130d`, PAPER `#f4f2ea`

### Three Visual Directions (from gravity-build.js)
- **Direction A — Terminal:** JetBrains Mono, tick-gauge bezel, bracketed readouts, scanline dividers
- **Direction B — Orbital:** Space Grotesk, concentric rings, orbiting dots
- **Direction C — Minimal Type:** Sora, almost no graphics, large editorial typography

Direction A is the primary direction. B and C exist as alternatives.
The AI is intended to generate personalised layouts — choosing direction, populating data, deciding which screens to show — based on the user's goal type and personality.

### Screen States (Direction A — all in screens.py)
- `A1()` — Ambient/Idle: clock, date, streak ribbon
- `A2()` — Morning Brief: top priority, non-negotiables checklist
- `A3()` — Active Nudge: full-screen intervention
- `A4()` — Goal Progress: progress arc, percentage, sub-tasks
- `A5()` — Weekly Heatmap: habit grid
- `A7()` — Wind-down: moon, sleep countdown

### Layout JSON Concept (to be built)
The AI should generate a layout descriptor like:
```json
{
  "direction": "A",
  "screens": [
    {"type": "A1", "data": {"streak": 47}},
    {"type": "A2", "data": {"task": "Work on app prototype", "nonneg": ["Music", "App work", "Learning"]}},
    {"type": "A4", "data": {"pct": 0.6, "label": "APP PROTOTYPE", "days_left": 182}},
    {"type": "A5", "data": {}},
    {"type": "A7", "data": {"lights_out": "00:00", "in_min": 90}}
  ]
}
```
The renderer reads this and builds the correct screen sequence.

### Simulator Controls (gravity_sim.py)
- LEFT/RIGHT arrows — cycle screens
- R — force re-render
- Q/ESC — quit
- Run from: `~/Documents/GRAVITY-OS/GRAVITY/simulator/display/`
- Command: `python3 gravity_sim.py`

---

## AI Architecture

### Provider Strategy
- Dev: Groq (llama-3.3-70b-versatile) — free, 14,400 req/day
- Production: Anthropic Claude API (Sonnet) — ~£0.85/user/month
- Abstraction: `core/ai_client.py` — swap by changing `AI_PROVIDER` in `.env`

### The Two-Call Nudge Pipeline
1. **Decision call** (cheap, runs every 15 min): should_nudge? yes/no + category + intensity
2. **Content call** (only if yes): generate actual message in user's tone

### Silent Extraction Pattern
The onboarding conversation and data extraction are SEPARATE calls:
- Conversation AI: focuses entirely on being a good interviewer
- Extraction AI: silently pulls structured JSON from transcript after each phase
- User never sees the extraction happening

### Context Architecture (for backend)
Never pass raw conversation history to AI — too expensive. Instead build a layered context object:
```python
user_context = {
  "profile": {...},           # from UserProfile
  "current_cycle": {...},     # goal + milestones + weeks remaining
  "today": {...},             # schedule + habits + calendar
  "recent_behaviour": {...},  # last 7 days patterns
  "nudge_history": {...}      # cooldowns + last category
}
```
This gets cached in Redis and rebuilt nightly.

---

## Key Product Rules (NEVER VIOLATE)

1. **AI brain first** — never build UI before AI is validated
2. **One question at a time** — onboarding AI never asks two questions in one message
3. **Voice-ready** — all AI responses written as if spoken aloud (no symbols, no markdown)
4. **Nudge accuracy > frequency** — wrong nudge destroys trust, no nudge is better than bad nudge
5. **No API keys in client code** — all AI runs server-side, always
6. **Layout JSON abstraction** — AI generates layout instructions, renderer draws them. Never hardcode layouts.
7. **Silent extraction** — data extraction never visible to user, always a separate call
8. **Honest likelihood scores** — never lie about feasibility, users need reality not comfort
9. **Max 5 non-negotiables** — enforce this at onboarding and in UI
10. **Paper + ink only** — 1-bit palette enforced in software, no colour in v1 UI

---

## Immediate Next Tasks for Claude Code

In priority order:

### 1. Fix visual quality of screens.py
The current renders work but look weak compared to the HTML reference. 
Reference files are in the project: `Gravity_Circular_UI.html`, `gravity-build.js`, `gravity-library.js`
Screenshots for reference: `dirA.png`, `01appcheck.png`, `02appcheck.png`, `03appcheck.png`, `04appcheck.png`
Goal: match the HTML renders as closely as possible — heavier ink weight, better rim text sizing, correct proportions.

### 2. Build layout_engine.py
File: `simulator/display/layout_engine.py`
Takes a `UserProfile` object, returns an ordered list of screen configs.
Each config: `{"screen": "A1", "fn": callable, "label": str}`
Should personalise: user's actual non-negotiables in A2, actual goal in A4, actual name in rim labels.

### 3. Wire gravity_sim.py to layout_engine.py
Replace the hardcoded SCREENS list with output from `layout_engine.py`.
Load `profiles/michael.json` → build layout → show personalised screens.

### 4. Add click/touch navigation
Mouse click: left half of circle = previous screen, right half = next screen.
Mouse drag: swipe left/right gesture.

### 5. Build nudge overlay screen
When nudge engine fires: show A3 variant with the actual nudge message.
In simulator: press `N` to trigger a test nudge based on current profile.

### 6. Add Direction B and C screen variants
`screens.py` currently only has Direction A.
Add Direction B (Orbital) and Direction C (Minimal Type) screens.
Gravity selects direction based on user personality (from profile).

---

## Files Claude Code Should Read First

In this order:
1. `CLAUDE.md` (or `CLAUDE__1_.md`) — master project context
2. `core/profile.py` — the data schema everything depends on
3. `core/ai_client.py` — AI abstraction pattern
4. `simulator/display/primitives.py` — drawing system
5. `simulator/display/screens.py` — current screen renders
6. `simulator/display/gravity_sim.py` — live simulator
7. `profiles/michael.json` — real user data to test with
8. `Gravity_Circular_UI.html` + `gravity-build.js` — visual reference (READ ONLY)

---

## Cost Constraints

- Claude API target: under £0.85/user/month
- Backend hosting: Hetzner CX22 ~£4.50/month
- Groq free tier: 14,400 req/day (dev only)
- Total prototype hardware BOM: ~£51-64
- Target production BOM: sub-£18
- Target retail: £79-£99
- Subscription: £4.99/month or £39/year

---

## What NOT To Build Next

- Do NOT build the React Native app before the AI+simulator loop is validated
- Do NOT order hardware before the simulator is working well
- Do NOT build integrations before the backend exists
- Do NOT hardcode any layout — always use the layout JSON system
- Do NOT put API keys anywhere except `.env`
- Do NOT use colour in the UI — 1-bit palette only
