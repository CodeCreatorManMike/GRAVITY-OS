## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

---

# GRAVITY — Claude Code Project Context

## What it is

Gravity is a physical AI-powered goal tracker. A circular display (~71mm, 2.8" round IPS LCD) on a desk. Runs a 6-month goal cycle. Two-call AI pipeline: nudge *decision* (cheap, frequent) + nudge *content* (only on yes). Stage 0 is complete: AI brain + full display simulator.

## Architecture overview

```
core/
  ai_client.py        AI provider abstraction (Groq dev / Anthropic prod, swap via .env)
  profile.py          UserProfile Pydantic schema — the ONE source of truth for user data
  onboarding.py       5-phase conversation engine (silent extraction after each phase)
  nudge_engine.py     Two-call pipeline: decide_nudge() → generate_nudge_content()
  prompts/            System prompts for each AI call

profiles/
  michael.json        Real completed profile (gitignored in prod)

simulator/
  display/
    primitives.py     PIL/Pillow drawing library — port of gravity-build.js
    screens.py        All screen renders: A1-A7, B1-B7, C1-C7
    layout_engine.py  Profile → ordered screen list (personalised layout)
    gravity_sim.py    Pygame live simulator (run this to see screens)
    fonts/            JetBrainsMono-*.ttf (Space Grotesk + Sora = optional B/C directions)

tests/
  test_profile_extraction.py   Profile save/load + field constraint tests
```

## Module connections

```
UserProfile (profile.py)
    ↓
layout_engine.build_layout(profile)
    ↓ returns list of {screen, label, fn} dicts
gravity_sim.py
    ↓ calls fn(profile_dict) → PIL.Image
screens.py A1/A2/A4/etc.
    ↓ calls drawing primitives
primitives.py (ring, arc, ticks, T, brackets, scan, etc.)
```

```
nudge_engine.evaluate_nudge(profile, state)
    → decide_nudge()    (Call 1: JSON decision)
    → generate_nudge_content()  (Call 2: message text)
    → result dict with message, category, intensity
```

## Display system coordinate conventions

- Canvas: **360×360 pixels**
- Centre: **C = 180**
- Angles: **0° = 12 o'clock, clockwise** (so P(r, 0) = top, P(r, 90) = right)
- Palette: **INK = #14130d**, **PAPER = #f4f2ea** — never pure black/white
- `T(draw, x, y, ...)` — **y is the typographic baseline** (matches SVG `dominant-baseline=alphabetic`)
- `ring(draw, r, ...)` — full circle at radius r
- `arc(draw, r, a, b, ...)` — arc from angle a to b (both 0°=top, clockwise)
- `ticks(draw, r, n, long_every, short_len, long_len)` — bezel tick marks

## Three visual directions

| Dir | Name      | Font          | Character                           |
|-----|-----------|---------------|-------------------------------------|
| A   | Terminal  | JetBrains Mono | Tick-gauge bezel, scanlines, brackets |
| B   | Orbital   | Space Grotesk  | Concentric rings, orbiting dots     |
| C   | Minimal   | Sora           | Editorial type, almost no graphics  |

Direction selected automatically from profile:
- `feedback_preference="direct"` or `failure_response="analyse"` → **A**
- creative/artist personality → **C**
- default → **B**

To add Space Grotesk or Sora: place `SpaceGrotesk-Regular.ttf` etc. in `simulator/display/fonts/`. JetBrains Mono is used as fallback.

## Screen states (Direction A — canonical)

| ID  | Name         | Key data shown                          |
|-----|-------------|------------------------------------------|
| A1  | Ambient/Idle | Clock, date, 14-day streak ribbon        |
| A2  | Morning Brief | Top task, non-negotiables checklist     |
| A3  | Active Nudge | Full-screen verb ("STAND UP"), dismiss   |
| A4  | Goal Progress | Progress arc, %, label, subtasks        |
| A5  | Weekly Heatmap | 7×5 habit grid, week totals            |
| A6  | Focus Timer   | Depleting arc, remaining time, DND      |
| A7  | Wind-down     | Moon, sleep window, tomorrow task       |

## AI prompt conventions

- **Voice-ready**: no symbols, no markdown in any spoken/displayed content
- **One question at a time**: onboarding AI never asks two questions per message
- **Silent extraction**: conversation AI and extraction AI are SEPARATE calls — user never sees JSON
- **Nudge accuracy > frequency**: wrong nudge destroys trust

## Key product rules (never violate)

1. INK = #14130d, PAPER = #f4f2ea — never pure black/white
2. Canvas 360×360, all content inside r=176
3. 1-bit palette only — no colour in v1 UI
4. Layout JSON abstraction — AI generates instructions, renderer draws them. Never hardcode layouts.
5. Max 5 non-negotiables (enforced at onboarding)
6. No API keys anywhere except .env
7. All AI runs server-side (no keys in client/renderer code)
8. Honest likelihood scores — never inflate feasibility

## Running the simulator

```bash
source .venv/bin/activate
cd simulator/display
python3 gravity_sim.py
```

Controls: `←/→` or click left/right half of circle = navigate  
`N` = fire test nudge | `O` = onboarding hint | `R` = re-render | `Q` = quit  
Simulator auto-reloads when `profiles/` changes.

## Running tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## What's NOT built yet

- FastAPI backend (`/nudge`, `/layout`, `/profile` endpoints)
- PostgreSQL + Redis
- React Native companion app
- Hardware driver (RPi + ST7701S SPI display)
- Stage integration tests (ai_client round-trip, nudge scenarios)
