# GRAVITY — Build Context & Architecture Decisions

Generated from full architectural grill session (June 2026).
Read this before every session. It captures decisions that are not obvious from the code.

---

## What GRAVITY Is

A circular desk device (hardware) paired with a React Native companion app, powered by an AI
that acts as the most honest, most informed version of the user's own intentions — not an
assistant, not a coach, not a chatbot. It knows what they said they wanted. It knows what they
actually did. It holds both without judgement and without letting go.

Three AI modes: **Witness** (observing), **Guide** (surfacing right info), **Challenger**
(confronting avoidance when patterns demand it). Full philosophy in `CLAUDE_DOCS/AI_BEHAVIOUR.md`.

---

## Hardware (V1)

| Component | Spec |
|---|---|
| MCU | ESP32-S3-WROOM-1-N16R8 (240MHz dual-core, WiFi b/g/n, BLE 5.0, 16MB flash, 8MB PSRAM) |
| Display | 2.8" round LCD TFT (ST77xx/GC9A01-class), capacitive touch overlay |
| Touch | CST816S (single-touch + gestures, wake-on-touch) |
| IMU | LIS2DW12 (3-axis, wake-on-pickup) |
| Mic | ICS-43434 I2S MEMS |
| Speaker | 8Ω + MAX98357A class-D amp |
| Battery | 1500mAh LiPo, BQ24074 charger, MAX17048 fuel gauge |
| Light sensor | VEML7700 |
| Form factor | Round, Ø110–120mm, 45–55mm deep, sits on weighted puck base |
| Charging | Pogo contacts on base, USB-C on base, device runs on battery when lifted |

**Key constraint:** Device is a display terminal + voice input terminal only. No decision-making
on device. All AI logic, tool routing, and content generation is server-side.

**Firmware:** MicroPython on ESP32-S3. Keep MicroPython — correct choice for this hardware.

---

## Camera — V2 Only

Camera was NOT included in V1 hardware. Decision:
- ESP32-S3 supports DVP parallel camera interface (same as ESP32-S3-EYE)
- OV2640 module fits (8×8mm) in the 110–120mm body
- Current PCB is fully designed — adding camera = new PCB spin
- LCD TFT display already cuts battery to days. Camera adds 20–30mA active draw.
- **V1 action:** Reserve blanked aperture + DNP camera footprint on PCB (like the ToF slot)
- **V2:** Add OV2640 + mandatory privacy LED indicator
- All CV inference is server-side. Device captures JPEG frames, streams over WiFi to backend.
- Use phone screen-time APIs (iOS Screen Time, Android UsageStats) as proxy for V1 behaviour detection.

---

## Voice Pipeline

```
ESP32-S3 runs ESP-SR wake-word ("Hey Gravity" / "Gravity")
  → audio captured (raw PCM, I2S mic)
  → WebSocket to backend  ← send AUDIO not text (Whisper is faster + more accurate)
  → faster-whisper STT (self-hosted, free, ~300ms)
  → Claude with tool-calling (add_task, complete_task, start_timer, stop_timer,
                               answer_question, create_document, get_schedule)
  → tool executed → DB updated → WebSocket push to device + app simultaneously
  → TTS response generated (edge-tts, free, Microsoft neural)
  → audio bytes returned to device → speaker plays
```

**Mic policy:**
- Off dock: wake-word always armed, full pipeline on trigger
- On dock: same, + optional ambient listening mode (user toggle in app)
- No push-to-touch — always wake-word triggered
- Never stream audio continuously without explicit wake-word trigger

---

## Device UI — 5 Faces

- Max 5 faces. User configures via app (pick type, reorder, configure).
- AI ranks which face shows first based on user context and time of day.
- Each face is a template: device has a MicroPython renderer per face type, receives JSON payload.
- Offline: last state cached to flash. Show offline indicator badge. Read-only.
- Face types: `goal_arc`, `task_list`, `habit_heatmap`, `timer`, `study_progress`

Visual language: round display, perimeter arc for progress, ring-checkboxes for tasks,
heatmap grid for habits. Design system in `MOCK-UPS/`.

App is "mission control" — dark, shows real circular face preview. Device is "calm output".

---

## User Model / RAG

User model lives server-side. Never on device. Structure:

1. **Structured facts** — nightly summarisation job converts raw daily data into fact strings:
   `"Completed gym 3/7 days this week. Completed sessions all before 9am. Missed days followed late phone usage."`
2. **Embedded + stored** in pgvector (memories table, `memory_type='daily_summary'`)
3. **Retrieved** via semantic search on every AI call — top-5 relevant memories injected into system prompt
4. **User profile** (goals, communication style, schedule, non-negotiables) in PostgreSQL
5. **Grows over time** — each interaction adds facts, each cycle review adds structured insight

The fine-tuned model learns Gravity's philosophy. The user model + dynamic system prompt = per-user personalisation. You never fine-tune per user.

---

## Storage Stack

```yaml
PostgreSQL + pgvector:  structured data (users, goals, habits, tasks, calendar) + vector embeddings
Redis:                  context cache (1h TTL), nudge cooldowns, WebSocket session state
MinIO:                  uploaded files (PDFs, syllabuses), generated documents (notes, study plans)
SearXNG:                self-hosted web search for research feature
```

All in Docker Compose. Single `docker-compose.yml`.

---

## Backend Architecture

**FastAPI** (Python, async) — correct choice. All AI/ML deps (Whisper, sentence-transformers,
faster-whisper) are Python-native. No language mismatch.

Router suite (all exist):
`auth, onboarding, goals, habits, nudges, device, integrations, review, analytics, push,
memory, research, calendar, files, voice (NEW)`

Services (all exist unless marked NEW):
`ai_service, calendar_service, connection_manager, context_service, document_service,
fitness_service, layout_service, memory_service, nudge_service, pattern_service,
pdf_generator, push_service, research_service, weather_service, storage_service (NEW),
voice_service (NEW)`

Scheduler jobs (APScheduler):
- Every 15min: nudge evaluation
- 01:00 daily: **nightly summarisation** → pgvector upsert (NEW)
- 02:00 daily: context cache rebuild
- 02:30 daily: pattern detection
- 09:00 daily: cycle trigger check

---

## AI Provider Strategy

```
NOW:     Groq (llama-3.3-70b) — fast, free-tier, good for nudges + summaries
SOON:    Claude Sonnet — challenger mode, onboarding, study plan generation, high-stakes calls
NEXT:    Fine-tuned open model on Ollama (Llama/Mistral/Phi)
FUTURE:  Custom model trained on Gravity interaction data (long-term, post-funding)
```

**Two-tier routing in ai_service.py:**
- `provider="cheap"` → Groq — nudge eval, layout ranking, quick Q&A (high frequency)
- `provider="quality"` → Claude — challenger mode, reviews, doc generation, onboarding

AI client already supports all three providers via `AI_PROVIDER` env var.

**Fine-tuning data collection starts V1:**
Every AI call logs an `AIInteraction` row. App + device report back via `AIOutcome` whether
user acted within 24h. This becomes the reward signal for future fine-tuning.

---

## Outcome Tracking (Training Data)

Two new tables added in V1:

```python
AIInteraction(id, user_id, message, mode, provider, model, tool_used, timestamp)
AIOutcome(interaction_id, acted, acted_within_hours, user_rating, timestamp)
```

Rule: every nudge, challenger message, voice response, and generated document gets a UUID.
App + device log whether user acted. Never reconstruct this data retroactively.

---

## Agentic Actions

Claude uses structured tool-calling server-side. Device never routes tools.

Defined tools:
- `add_task(title, due_date, priority)` → DB write → WebSocket push to device + app
- `complete_task(task_id)` → DB write → push
- `start_timer(duration_minutes, label)` → push
- `stop_timer()` → push
- `answer_question(question, context_type)` → RAG retrieval → spoken response
- `create_document(title, doc_type, content_query)` → Claude generates → MinIO → app notified
- `get_schedule(day)` → calendar query → spoken response

Long content (documents, study notes) → MinIO → app download only. Device confirms via speaker:
"Done, check your app."

---

## Demo Target (Pre-Hardware)

Build order before device arrives:

**Tier 1 — Backend (no hardware needed):**
1. MinIO in docker-compose + storage_service.py
2. AIInteraction + AIOutcome tables + logging
3. Voice pipeline router + service
4. AI face ranking activated in layout_service.py
5. Face card JSON schema (5 types)
6. Nightly summarisation job

**Tier 2 — App (no hardware needed):**
7. Face editor UI
8. File upload/download (MinIO-backed)
9. Onboarding flow → user model
10. Circular face previews
11. WebSocket connection to backend

**Tier 3 — Hardware bridge (when device arrives):**
12. Firmware WebSocket auth + layout JSON receive
13. MicroPython face renderers (one per type)
14. ESP-SR wake-word integration
15. Audio capture → WebSocket → voice pipeline
16. Offline cache (flash)

**Tier 4 — Demo polish:**
17. Simulator (already has `/GRAVITY/simulator` dir)
18. Boot animation (already built)
19. E2E onboarding test

---

## Key Rules for Claude in This Repo

1. **Always run `graphify query` before grepping.** graph.json exists. Use it.
2. **Caveman mode** saves ~75% output tokens. Say "caveman mode" to activate.
3. **Device is dumb terminal.** Never add logic to firmware that belongs in backend.
4. **User model is RAG, not prompt stuffing.** Don't pass raw data to Claude. Summarise first.
5. **Every AI call must log AIInteraction.** No exceptions. Future training data.
6. **MinIO for all file storage.** Never write uploaded bytes to local filesystem.
7. **Two-tier AI routing.** Cheap (Groq) for high-frequency. Quality (Claude) for high-stakes.
8. **Face types are fixed schemas.** Device renderers are statically compiled. Don't add face types without updating firmware too.
9. **Camera is V2.** Do not add camera-dependent features to V1 scope.
10. **MicroPython stays.** No C++/C# on firmware. Wrong tool for this hardware.
