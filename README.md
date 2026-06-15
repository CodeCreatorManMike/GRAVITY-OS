# GRAVITY

> A physical AI-powered goal tracker. 2.8" round IPS LCD. Sits on your desk. Runs on a 6-month cycle. Learns your behaviour, nudges you when you drift.

## What It Is

Three surfaces, one purpose:

- **Device** — ESP32-S3, 2.8" round IPS LCD (480×480, ~174 PPI), warm paper aesthetic (INK `#14130D` / PAPER `#F4F2EA`), sits in an angled base, always glanceable.
- **Companion App** — React Native (iOS-first), integrations hub, rich dashboard, onboarding chat.
- **Backend** — Python FastAPI, owns all AI reasoning, serves device and app over WebSocket + REST.

## Build Status

| Layer | What | Status |
| --- | --- | --- |
| AI Brain | Groq/Claude/Ollama swap, two-call nudge pipeline, 5-phase onboarding, pygame simulator | ✅ Complete |
| Backend API | Auth, goals, habits, nudges, device, integrations, review, analytics, push, memory, research, calendar, files | ✅ Complete |
| WebSocket | Connection manager, NUDGE/HABIT/HEARTBEAT/LAYOUT events, push fallback | ✅ Complete |
| Scheduled workers | Nudge eval (15 min), context rebuild (02:00), pattern detection (02:30), cycle trigger (09:00) | ✅ Complete |
| Long-term memory | pgvector + sentence-transformers, cosine recall, injected into every AI context | ✅ Complete |
| React Native App | Login, onboarding chat, home, health, settings, analytics, goal/habit management, cycle review | ✅ Complete |
| Apple Health | HealthKit sync → backend (steps, sleep, HR, calories) — needs EAS Build to run natively | ✅ Built |
| Open-Meteo weather | No-key weather API, 1h Redis cache, wired into AI context | ✅ Complete |
| CalDAV calendar | iCloud/any CalDAV sync, today's events in AI context | ✅ Complete |
| Web research | SearXNG (self-hosted) + Jina Reader, Wger exercise database | ✅ Complete |
| File upload + PDF export | PyMuPDF ingestion → memory, WeasyPrint cycle review + habit reports | ✅ Complete |
| Push notifications | Expo Push API fallback when WebSocket offline | ✅ Complete |
| ESP32-S3 firmware | MicroPython, ST7701S display HAL, layout JSON renderer, touch, IMU, ALS, OTA, boot animation | ✅ Complete |
| Production deploy | Nginx + Gunicorn + Certbot, Hetzner one-command deploy script | ✅ Complete |
| Voice (STT) | Whisper / faster-whisper — waiting on microphone hardware (ICS-43434) | ⏳ Needs hardware |
| Voice (TTS) | Piper TTS — waiting on speaker hardware (MAX98357A) | ⏳ Needs hardware |
| Wake word | OpenWakeWord "Hey Gravity" — waiting on microphone hardware | ⏳ Needs hardware |
| Camera / presence | OpenCV / MediaPipe — Phase 3 | ⏳ Phase 3 |
| Hardware bring-up | ESP32-S3 DevKit + ER-TFT028 eval display, breadboard, enclosure | ⏳ Parts to order |

## Hardware Spec (V1)

| Component | Part | Detail |
| --- | --- | --- |
| MCU | ESP32-S3-WROOM-1-N16R8 | Dual-core LX7 @ 240 MHz, 16 MB flash, 8 MB octal PSRAM, WiFi b/g/n + BLE 5 |
| Display | 2.8" round IPS LCD, ST7701S | 480×480 px, ~174 PPI, Ø70.13 mm active area, 250–300 cd/m², SPI+RGB interface |
| Touch | CST816S (production) | Single-point + HW gestures, I²C 0x15, wake-on-touch |
| Eval display module | ER-TFT028-2-6318 (BuyDisplay) | LT7683 + GT911, Arduino-shield — breadboard bring-up only |
| IMU | LIS2DW12 | 3-axis accel, ~1 µA, orientation + wake-on-motion, I²C 0x18 |
| ALS | VEML7700 | Ambient light → backlight PWM, I²C 0x10 |
| Charger | BQ24074 | Power-path charger — runs from USB while charging, no micro-cycling |
| Regulator | TPS62840 | 60 nA quiescent buck — drives the standby battery life |
| Fuel gauge | MAX17048 | Real state-of-charge, I²C 0x36, ~3 µA |
| Mic | ICS-43434 | I²S MEMS mic (Phase 2 voice) |
| Amp | MAX98357A | I²S Class-D, mono ~3 W (Phase 2 voice) |
| Battery | 1000–1500 mAh LiPo | ~8–16 h active (backlight on), ~2–3 days standby |
| Enclosure | ~90–100 mm dia, 40–50 mm deep | < 180 g device, < 250 g with base. 15–25° tilt in base |

The display renders a warm paper-on-ink aesthetic in software (background `#F4F2EA`, foreground `#14130D`, 1-bit palette). No e-ink hardware — instant refresh, stable supply, LCD all the way. E-ink remains a future swap at the driver layer when a reliable round source exists at volume.

## Project Structure

```text
GRAVITY/                     backend + core AI (run server from here)
  core/
    ai_client.py             AI provider swap (Groq / Claude / Ollama via .env)
    nudge_engine.py          Two-call pipeline: decide_nudge() → generate_nudge_content()
    profile.py               UserProfile Pydantic schema
    prompts/                 System prompts for every AI call
  backend/
    main.py                  FastAPI app, WebSocket endpoint, scheduler lifespan
    routers/                 auth, goals, habits, nudges, device, integrations, review,
                             analytics, push, memory, research, calendar, files
    services/                context, layout, memory, pattern, push, research, fitness,
                             calendar, weather, document, pdf_generator, connection_manager
    models/                  user, goal, habit, nudge, integration, memory,
                             calendar_event, user_location, push, file
    workers/
      scheduler.py           APScheduler — 4 jobs running inside the FastAPI process
    templates/pdf/           Jinja2 templates for WeasyPrint PDF exports
  simulator/
    display/
      gravity_sim.py         Pygame live simulator (360×360 canvas — scaled-down preview)
      screens.py             A1–A7 Direction A screen renders
      primitives.py          PIL drawing library — arcs, ticks, rings, type
  deploy/
    Dockerfile
    docker-compose.prod.yml
    nginx.conf               HTTPS + WebSocket reverse proxy
    deploy.sh                One-command Hetzner Ubuntu 24.04 bootstrap
  searxng/settings.yml       Self-hosted SearXNG config
GravityApp/                  React Native app (Expo SDK 56, iOS-first)
  app/
    (tabs)/                  Home, Health, Settings, Analytics
    login.tsx
    onboarding.tsx           5-phase AI onboarding chat
    review.tsx               6-month cycle review chat
    goal-edit.tsx
    habits-manage.tsx
  hooks/
    useGravitySocket.ts      WebSocket with exponential backoff reconnect
    usePushNotifications.ts  Expo push token registration on startup
  components/
    DevicePreview.tsx        Circular device preview (pure React Native, no SVG)
firmware/                    ESP32-S3 MicroPython
  main.py                    Boot sequence + 50 ms polling main loop
  boot_animation.py          Terminal-style line-by-line boot reveal
  websocket_client.py        Hand-rolled RFC 6455 client (no stdlib WS in MicroPython)
  display/
    hal.py                   Abstract HAL — 460 KB PSRAM framebuffer (480×480×2 bytes)
    st7701s.py               Production ST7701S driver (SPI config + RGB pixel push)
    lt7683.py                Eval board LT7683 driver (ER-TFT028 breadboard path)
    renderer.py              Layout JSON → A1/A2/A3/A4/A5/A7 screen dispatch
    components.py            Circle mask (r=230), arc, progress ring, bitmap font, heatmap
  touch.py                   CST816S + GT911 unified driver
  imu.py                     LIS2DW12 orientation + wake-on-motion
  als.py                     VEML7700 ambient light → backlight PWM
  power.py                   MAX17048 fuel gauge + deep sleep entry
  ota.py                     OTA firmware update handler
CLAUDE_DOCS/                 Architecture, hardware spec, product docs
```

## Running Locally

### Backend

```bash
cd GRAVITY
docker-compose up -d          # Postgres (pgvector/pg16), Redis, SearXNG
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### App

```bash
cd GravityApp
npx expo start                # Expo Go for most screens

# Apple Health + push require a native build:
npx expo prebuild && open ios/GravityApp.xcworkspace
```

### Simulator

```bash
cd GRAVITY && source .venv/bin/activate
cd simulator/display && python3 gravity_sim.py
# ←/→ navigate | N = fire test nudge | R = re-render | Q = quit
```

## AI Provider

```bash
# Development (free tier, fast)
AI_PROVIDER=groq
GROQ_API_KEY=your_key

# Local offline (no rate limits, needs Ollama running)
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Production
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
```

## Hardware — Next Milestone

Order these to start firmware bring-up:

| Part | Source | ~£ |
| --- | --- | --- |
| ESP32-S3-DevKitC-1-N8R8 | DigiKey / Mouser | ~£15 |
| ER-TFT028-2-6318 (2.8" round IPS LCD eval module) | BuyDisplay | ~£22 |
| LiPo 1200–2000 mAh with protection | Adafruit | ~£6 |
| TP4056 USB-C charge module | AliExpress | ~£2 |

> **Note:** the eval module uses an LT7683 controller, not the production ST7701S. The firmware has separate drivers for both — swap via `DISPLAY_DRIVER` in `firmware/config.py`. Rendering and touch logic validated on the eval module transfers directly; the driver layer is the only thing that changes for production.

Full BOM, GPIO map, and wiring guide: [`CLAUDE_DOCS/HARDWARE.md`](CLAUDE_DOCS/HARDWARE.md) and [`firmware/README.md`](firmware/README.md).

## Documentation

| File | Contents |
| --- | --- |
| [`CLAUDE_DOCS/PRODUCT.md`](CLAUDE_DOCS/PRODUCT.md) | Product vision, 6-month cycle, monetisation |
| [`CLAUDE_DOCS/HARDWARE.md`](CLAUDE_DOCS/HARDWARE.md) | Full hardware spec, BOM, GPIO map, power budget |
| [`CLAUDE_DOCS/SOFTWARE_ARCH.md`](CLAUDE_DOCS/SOFTWARE_ARCH.md) | System architecture, API design, data models |
| [`CLAUDE_DOCS/AI_BEHAVIOUR.md`](CLAUDE_DOCS/AI_BEHAVIOUR.md) | AI philosophy, nudge logic, adaptation engine |
| [`CLAUDE_DOCS/FEATURES.md`](CLAUDE_DOCS/FEATURES.md) | Complete feature list by category |
| [`CLAUDE_DOCS/OPEN_SOURCE_STACK.md`](CLAUDE_DOCS/OPEN_SOURCE_STACK.md) | Every third-party tool and why it was chosen |

## Built By

**Michael Jones** — London. Age 20. Solo. Building alongside a full-time job.
