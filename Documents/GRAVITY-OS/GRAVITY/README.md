# GRAVITY

A physical AI-powered goal tracker. Circular display. Sits on your desk. Runs on a 6-month cycle. Learns your behaviour, nudges you when you drift.

---

## What It Is

Gravity is a palm-sized device with a 2.8" round IPS LCD display. It connects to a companion app and a backend AI engine. Every 6 months it runs a full re-onboarding — reviews what was achieved, resets goals, rebuilds the UI around the new cycle.

It has one job: making sure you become the person you said you wanted to be.

**Three surfaces:**
1. **Device** — circular display, sits on desk, glanceable data, nudges
2. **Companion App** — React Native (iOS + Android), integrations, rich dashboard, onboarding
3. **Backend** — Python FastAPI, owns all AI reasoning, serves device and app

---

## Current Stage: Stage 0 — Brain First

The AI onboarding conversation engine is complete. No hardware. No app. Just the AI logic that makes the product real.

| Stage | What Gets Built | Status |
|---|---|---|
| 0 | AI onboarding brain — Python, Claude/Groq API, JSON profiles | **COMPLETE** |
| 1 | FastAPI backend + PostgreSQL + React Native app shell | NOT STARTED |
| 2 | RPi Zero 2W + round display prototype + MicroPython firmware | NOT STARTED |
| 3 | Integration layer — Calendar, Health, Screen Time | NOT STARTED |
| 4 | ESP32-S3 migration + 3D printed enclosure | NOT STARTED |
| 5 | Polish, app store, launch | NOT STARTED |

---

## Project Structure

```
core/
  ai_client.py         AI provider abstraction (Groq dev / Claude prod)
  profile.py           UserProfile schema — single source of truth
  onboarding.py        5-phase conversation engine
  nudge_engine.py      Two-call pipeline: decide → generate
  prompts/             System prompts for each AI call

simulator/
  display/
    primitives.py      PIL drawing library — circles, arcs, ticks, type
    screens.py         All screen renders: A1–A7, B1–B7, C1–C7
    layout_engine.py   Profile → ordered screen list
    gravity_sim.py     Pygame live simulator
    fonts/             JetBrainsMono typeface files

tests/
  test_profile_extraction.py
  test_onboarding.py
  test_nudge_logic.py

profiles/              User profiles (gitignored in prod)
```

---

## Running the Simulator

```bash
source .venv/bin/activate
cd simulator/display
python3 gravity_sim.py
```

Controls: `←/→` or click left/right half = navigate screens  
`N` = fire test nudge | `O` = onboarding hint | `R` = re-render | `Q` = quit

---

## Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

---

## Documentation

Full design and technical documentation lives in `../CLAUDE_DOCS/`:

| File | Contents |
|---|---|
| `PRODUCT.md` | Product vision, 6-month cycle, monetisation |
| `HARDWARE.md` | Display spec, BOM, component decisions |
| `SOFTWARE_ARCH.md` | Full system architecture, API design, data models |
| `AI_BEHAVIOUR.md` | AI philosophy, nudge logic, adaptation engine |
| `UI_UX.md` | Design language, screen states, component system |
| `FEATURES.md` | Complete feature list by category |
| `CONSTRAINTS.md` | AI cost tiers, budget targets, technical limits |
| `PROJECT_CONTEXT.md` | Quick-start context for AI assistants and collaborators |

---

## Built By

**Michael Jones** — Junior Technical Analyst, VX One, London. Age 20. Solo.  
Building in ~1–2 hours/day alongside a full-time job.
