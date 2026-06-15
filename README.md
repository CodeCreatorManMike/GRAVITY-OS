# GRAVITY

A physical AI-powered goal tracker. Circular e-ink display. Sits on your desk. Runs on a 6-month cycle. Learns your behaviour, nudges you when you drift.

---

## What It Is

Gravity is a palm-sized device with a **circular black-and-white e-ink display** (~3.71"–4.2", 90–95mm usable). It connects to a companion app and a backend AI engine. Every 6 months it runs a full re-onboarding — reviews what was achieved, resets goals, rebuilds the UI around the new cycle.

It has one job: making sure you become the person you said you wanted to be.

**Three surfaces:**
1. **Device** — circular e-ink display, sits on desk, glanceable data, nudges
2. **Companion App** — React Native (iOS + Android), integrations, rich dashboard, onboarding
3. **Backend** — Python FastAPI, owns all AI reasoning, serves device and app

---

## Current Stage: Stage 0 — Brain First

The AI onboarding conversation engine is built and tested. No app, no backend service yet — just the AI logic that makes the product real, plus a desktop simulator for the device UI.

| Stage | What Gets Built | Status |
|---|---|---|
| 0 | AI onboarding brain — Python, Groq/Claude API, JSON profiles | **COMPLETE** |
| 1 | FastAPI backend + PostgreSQL + React Native app shell | NOT STARTED |
| 2 | RPi Zero 2W + round e-ink display prototype + MicroPython firmware | NOT STARTED |
| 3 | Integration layer — Calendar, Health, Screen Time | NOT STARTED |
| 4 | ESP32-S3 migration + custom PCB + 3D printed enclosure | NOT STARTED |
| 5 | Polish, app store, launch | NOT STARTED |

**Stage 0 "complete" means:** the 5-phase conversation runs end-to-end, emits the full profile JSON (`core/profile.py` schema), the two-call nudge pipeline (decide → generate) works, and the suite passes (`pytest tests/` — 25 tests, no API key required to run them).

---

## Hardware — V1 (final / Stage 4)

The production unit is built around an **ESP32-S3** module driving a circular e-ink display, with everything on a custom 2-layer PCB. The device is a display terminal — all AI runs in the cloud.

| Spec | Value |
|---|---|
| Compute | ESP32-S3-WROOM-1-N16R8 (240 MHz dual-core, WiFi b/g/n + BLE 5.0, 16 MB flash / 8 MB PSRAM) |
| Display | Round e-ink, Ø90–95 mm active (Waveshare 3.71" 480×480), pure B/W, holds image at 0 W |
| Touch | CST816S capacitive — single touch + hardware gestures, wake-on-touch |
| Battery | 1500 mAh LiPo · multi-week (deep sleep ~20 µA total) |
| Body | Matte-black ABS/PETG puck, Ø110–120 mm, depth 45–55 mm, < 200 g, in an angled base |
| PCB | Custom 2-layer, Ø75–85 mm, 1.0 mm · KiCad 8 |
| Target BOM | ~£25–33 at volume · retail £79–£99 |

**Core components**

- **Compute:** ESP32-S3-WROOM-1-N16R8 (module, pre-certified antenna — no RF cert/tuning needed)
- **Power:** BQ24074 charger with power-path · TPS62840 3.3 V buck (60 nA quiescent) · MAX17048 fuel gauge
- **Sensors:** LIS2DW12 accelerometer (orientation + wake-on-pickup) · VEML7700 ambient light · TMP117 temp *(Phase 2)*
- **Audio:** ICS-43434 I²S mic (voice + on-device wake-word) · MAX98357A class-D amp → 8 Ω speaker
- **Display IF:** round e-ink over SPI · capacitive touch over I²C, FPC ribbons to the board
- **Base:** USB-C (power-only in V1) + ESD/PTC protection on a small board; 2 pogo contacts (VBUS + GND) bridge the lift-out joint — device runs on battery when lifted, charges when seated

Full detail in `MOCK-UPS/GRAVITY HARDWARE/uploads/GRAVITY_V1_PCB_DESIGN.md` and `GRAVITY_V1_FULL_BUILD_SPEC.md`.

> **Display note:** Gravity is an **e-ink** device — the whole UI philosophy (no animation, weeks of battery, terminal aesthetic) depends on it. Earlier drafts referenced a 2.8" IPS LCD; that is superseded. The authoritative spec is round e-ink. See `CLAUDE_DOCS/HARDWARE.md`.

---

## Project Structure

```
core/
  ai_client.py         AI provider abstraction (Groq dev / Claude prod), lazy-loaded
  profile.py           UserProfile schema — single source of truth
  onboarding.py        5-phase conversation engine
  nudge_engine.py      Two-call pipeline: decide → generate
  prompts/             System prompts for each AI call

simulator/
  display/
    primitives.py      PIL drawing library — circles, arcs, ticks, type
    screens.py         All screen renders
    layout_engine.py   Profile → ordered screen list
    gravity_sim.py     Pygame live simulator
    fonts/             Monospace typeface files

tests/                 pytest suite (profile, onboarding, nudge logic)
profiles/              User profiles (gitignored)
```

Hardware design for the production unit (Stage 4) lives in
`MOCK-UPS/GRAVITY HARDWARE/uploads/`:
`GRAVITY_V1_PCB_DESIGN.md` and `GRAVITY_V1_FULL_BUILD_SPEC.md`.

---

## Running with Docker

```bash
cp .env.example .env        # add your GROQ_API_KEY for live onboarding
docker compose build
docker compose run --rm gravity                            # runs the test suite
docker compose run --rm gravity python -m core.onboarding  # runs onboarding
```

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v          # no API key needed
python -m core.onboarding           # needs GROQ_API_KEY (or AI_PROVIDER=anthropic)
```

### Simulator

```bash
source .venv/bin/activate
cd simulator/display
python3 gravity_sim.py
```

Controls: `←/→` (or click left/right half) navigate screens · `N` test nudge · `O` onboarding hint · `R` re-render · `Q` quit

---

## Documentation

Full design docs live in `CLAUDE_DOCS/`:

| File | Contents |
|---|---|
| `PRODUCT.md` | Product vision, 6-month cycle, monetisation |
| `HARDWARE.md` | Display spec, BOM, component decisions |
| `SOFTWARE_ARCH.md` | System architecture, API design, data models |
| `AI_BEHAVIOUR.md` | AI philosophy, nudge logic, adaptation engine |
| `UI_UX.md` | Design language, screen states, component system |
| `FEATURES.md` | Complete feature list by category |
| `CONSTRAINTS.md` | AI cost tiers, budget targets, technical limits |
| `PROJECT_CONTEXT.md` | Quick-start context for AI assistants and collaborators |

---

## Built By

**Michael Jones** — Junior Technical Analyst, VX One, London. Age 20. Solo.
Building in ~1–2 hours/day alongside a full-time job.
