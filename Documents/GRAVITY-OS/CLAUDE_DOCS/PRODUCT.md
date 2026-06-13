# PRODUCT — GRAVITY

---

## What It Is

Gravity is a palm-sized device — roughly the footprint of an Apple HomePod Mini — with a 2.8" circular display on its face. It sits on a desk or bedside table. It is always on. It always shows something useful.

It is not a smartwatch. It is not a phone peripheral. It is not another to-do app in a different form. It is a physical presence in a user's space with a single job: making sure the person who owns it becomes the person they said they wanted to be.

The product has three surfaces:
- **Device** — the physical object, circular display, nudge delivery, ambient data
- **Companion App** — React Native, integration hub, onboarding input, rich dashboard
- **Backend** — FastAPI, owns all AI reasoning, serves both surfaces

---

## First Boot & Onboarding

Unboxing Gravity should feel like meeting something alive.

The device boots with a terminal-style animation — scanlines, boot text, firmware sequence — before settling into a clean space-station aesthetic. It prompts the user to download the companion app via a QR code. From there, the AI takes over.

Onboarding is a conversation, not a form. The AI asks open questions about who the user is, what their days look like, and what they want from the next 6 months. It extracts structured data invisibly — the user is never aware of the profiling happening beneath the conversation. By the end, the AI has:

- A full user profile (personality, schedule, capacity)
- A set of defined goals with assessed likelihood scores
- A list of non-negotiables (max 5) the user commits to every day
- A personalised UI layout for the device

If a user has no clear goals, Gravity finds them through questions about hobbies, interests, and habits. It does not start until it has something real to work with.

---

## The 6-Month Cycle

Gravity operates on a 6-month rhythm. This is the core engine of the product.

Every 6 months, the device initiates a full re-onboarding:
- Reviews what was achieved vs what was planned — honest data, no softening
- Shows streaks, completions, avoidance patterns, overall progress
- Asks what has changed — job, lifestyle, priorities, new goals
- Re-evaluates the user's capacity and schedule
- Sets a new 6-month goal structure with updated non-negotiables
- Rebuilds the UI to reflect the new cycle

Between cycles, the AI learns. It notices the gap between what the user said they would do and what they actually did. By cycle 3, it knows the user better than most people in their life.

The 6-month rhythm is not arbitrary. It mirrors how humans actually operate — long enough to build real habits, short enough that the end is always visible.

---

## Monetisation

- **Device:** One-time purchase — target £79–£99
- **Subscription:** £4.99/month or £39/year for AI features (API calls, backend, sync)
- **Free tier:** Device functions as a basic habit tracker without subscription. AI features require a plan.
- **No ads. Ever.**

Target AI cost per user per month: under £0.85 at scale.

---

## What Gravity Is Not

- Not a to-do app
- Not a notification machine that gets ignored
- Not a gamification gimmick with streaks for streaks' sake
- Not a journaling app
- Not a smartwatch competitor
- Not a phone replacement

Gravity is a physical object with a purpose. It sits in your space. It exists in the room with you. It does not ask for your attention — it earns it by being right.

---

## Build Roadmap

| Stage | What Gets Built | Status |
|---|---|---|
| 0 | AI onboarding brain — Python terminal, Claude/Groq API, profile as JSON | **COMPLETE** |
| 1 | FastAPI backend + PostgreSQL + React Native app shell | NOT STARTED |
| 2 | RPi Zero 2W + round display prototype + MicroPython firmware | NOT STARTED |
| 3 | Integration layer — Calendar, Health, Screen Time | NOT STARTED |
| 4 | ESP32-S3 migration + 3D printed enclosure | NOT STARTED |
| 5 | Polish, app store, early access launch | NOT STARTED |

**The AI brain is the product.** A beautiful device with weak AI is a shell. Stage 0 must be solid before anything else is touched.

---

## Detailed Documentation

| Topic | File |
|---|---|
| Hardware specs, BOM, display decision | `HARDWARE.md` |
| Full system architecture, API design | `SOFTWARE_ARCH.md` |
| AI philosophy, nudge logic, adaptation | `AI_BEHAVIOUR.md` |
| UI design language, screen states | `UI_UX.md` |
| Complete feature list | `FEATURES.md` |
| AI cost tiers, budget constraints | `CONSTRAINTS.md` |
