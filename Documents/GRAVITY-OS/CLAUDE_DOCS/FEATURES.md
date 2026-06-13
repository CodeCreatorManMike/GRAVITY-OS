# FEATURES — GRAVITY

---

## Core Purpose

Gravity is a physical device built to break down goals, keep users on track, measure progress, and reward consistency. It operates on a 6-month cycle — long enough to build real habits, short enough to stay honest. It gamifies life in a way that is grounded in real outcomes, not empty streaks.

---

## Goal System

### Goal Intake
- Goals are extracted through a structured conversational onboarding — not a form
- The AI asks open questions and derives structured data from natural language responses
- Hidden goals the user did not explicitly state are identified and surfaced
- Each goal is assigned a likelihood score based on the user's schedule, capacity, and history
- Unrealistic goals are challenged with data, not dismissed — the AI proposes adjustments
- Goals are broken into 6-month, mid-term, short-term, and daily structures

### Goal Execution
- Each goal has associated tasks, milestones, and key metrics
- The AI designs a tailored schedule that fits the user's actual day — not an ideal version of it
- Resources, files, and reference material can be uploaded via the companion app
- The AI researches the goal domain and expands its knowledge base over time
- Study plans, project breakdowns, and preparation structures are generated on demand
- Small executable tasks are generated continuously as the goal progresses
- Task realism is monitored — consistent failure triggers a restructuring conversation, not punishment

### 6-Month Cycle
- At the end of each cycle, Gravity initiates a full re-onboarding
- Reviews achievement vs plan — honest data, no softening
- Asks what has changed in the user's life, schedule, and priorities
- Sets a new 6-month goal structure with updated non-negotiables
- Rebuilds the UI to reflect the new cycle's focus

---

## Non-Negotiables

- Users define a list of daily non-negotiables during onboarding — things that happen regardless of everything else (e.g. brush teeth, 2km walk, 3 meals a day)
- Maximum 5 non-negotiables enforced at onboarding
- These are tracked, displayed, and enforced across every cycle
- Missing a non-negotiable triggers a direct nudge — not a gentle reminder

---

## AI Intelligence

### Witness Mode
The AI observes without interrupting. It learns the user's schedule, habits, patterns, location rhythms, and digital behaviour. It builds a model of the user passively before it speaks.

### Guide Mode
The AI surfaces the right information at the right moment. It does not speak unless it has something worth saying. Two precise nudges a week that land correctly are worth more than ten ignored ones.

### Challenger Mode
When patterns demand it — consistent avoidance, missed targets, self-deception — the AI confronts the user directly. It earns this mode by being consistently accurate over time. It exits it when patterns improve.

### Adaptation Engine
- Tracks completion rates by task type, time of day, and day of week
- Learns which nudge styles produce action for this specific user — direct, data-led, or gentle
- Gradually shifts the schedule toward what the user actually does vs what they wish they did
- Flags when a goal needs restructuring (3+ weeks of consistent failure = conversation, not another nudge)

---

## Nudge System

- Nudge decisions are made by a lightweight AI call — cheap, frequent, accurate
- Nudge content is generated only when the decision is yes — prevents wasted API calls
- Nudges are delivered to the physical device screen — not a phone notification that gets ignored
- Every nudge references real user data — never generic
- Nudge timing is contextual, not time-based — the AI determines the right moment, not just the right hour
- Escalation: gentle nudge → direct callout → intervention conversation, based on pattern severity

---

## Procrastination & Bad Habit Detection

- Screen time monitoring: detects doom scrolling by comparing app usage duration against the user's own baseline
- Phone pickup: camera identifies when the user picks up their phone mid-task
- Bad habit logging: user-defined triggers (time-of-day patterns, self-report prompts) detect smoking, overspending, and similar behaviours
- Spending: open banking integration (optional) flags purchases that conflict with a savings goal
- Fitness: cross-references Apple Health / Google Fit step and workout data against targets
- All interventions are delivered to the e-ink screen — bypasses notification blindness

---

## Voice Capability

- The device accepts spoken language and converts it to text for processing
- Responds in spoken language where appropriate
- Supports: questions, reminders, timers, task completion, task creation, goal updates
- Research requests are compiled and sent as downloadable documents via the companion app
- When more context is needed, the device asks — the user provides it via voice or the app

---

## Camera Capabilities

- Presence detection: identifies when the user is at their desk, away, or asleep
- Behaviour identification: detects scrolling on a phone, reading, working, lying down
- Study session enforcement: if a user breaks a timed study block to pick up their phone, a nudge fires immediately
- Trained on common user behaviours — not a surveillance system, a context layer
- Camera feed is processed on-device or uploaded to the backend (user controlled)

---

## Agentic Tasks & Research

- When a user has a goal that requires support, Gravity researches it
- Capable of generating: study plans, email drafts, project breakdowns, goal probability analyses, weekly summaries
- File output: documents requested by the user are generated and made downloadable via the companion app
- Task execution: with permissions set, can send emails, retrieve information, or initiate processes the user has trained it on
- Full awareness: the AI maintains knowledge of everything the user has shared — goals, progress, files, preferences — and references it precisely

---

## Knowledge Base

- Builds continuously across every conversation, upload, and interaction
- Remembers what the user said, what they did, and the gap between the two
- Expands its domain knowledge on each user's specific goals — not generic knowledge, contextual knowledge
- By cycle 3, the device knows the user's patterns better than most people in their life
- RAG-style memory: when a user changes or deprioritises a goal, the system notes the reason and stores it — not discarded, archived

---

## Evolving UI

- The UI is generated by the AI — not hardcoded
- The AI determines the best way to present information for this user's specific goal and outputs a layout JSON
- A local renderer interprets JSON and draws to the display — no firmware updates needed for UI changes
- UI evolves between 6-month cycles and adapts within cycles as goals progress
- Users can choose presets via the companion app; the AI recommends the most effective one with a brief plain-language explanation

---

## Integrations

### Phase 1 (Launch)
- Google Calendar / Apple Calendar
- Apple Health / Google Fit (steps, workouts, sleep)
- Manual habit logging via companion app

### Phase 2
- Android Screen Time API
- iOS Screen Time workaround via Apple Shortcuts
- Spotify (detect music = detect focus state)
- Google Tasks / Todoist

### Phase 3
- Open Banking (Plaid / TrueLayer) for spending vs savings tracking
- Microphone for voice check-ins and ambient presence detection
- Camera (presence + behaviour detection)
- IFTTT / Zapier webhook support

---

## Value & Rewards

- Audio, visual, and system-based rewards are triggered when users complete tasks, hit streaks, or reach milestones
- Rewards are earned, not performative — brief, specific, data-grounded
- Progress is shown in hours studied, tasks completed, gym days, money saved, and custom metrics
- 6-month summaries visualise the full cycle — what the AI contributed, what the user achieved
- The goal of the reward system is sustained dopamine loop through real achievement, not fake points

---

## Companion App

- Integration hub: connects external services, manages permissions, syncs data
- Rich dashboard: heatmaps, streaks, progress rings, weekly reviews, cycle data
- UI customisation: preset selection, screen ordering, goal editing
- File management: upload reference material, download generated documents
- Receives nudges when the device is not in view
- The app inherits the same visual language as the device — dark mode, monospace, minimal, space-station aesthetic

---

## What Gravity Is Not

- Not a to-do app
- Not a notification machine
- Not a gamification gimmick with streaks for the sake of streaks
- Not a journaling app
- Not a smartwatch
- Not a phone replacement

Gravity is a physical object with a purpose. It exists in your space. It has one job.
