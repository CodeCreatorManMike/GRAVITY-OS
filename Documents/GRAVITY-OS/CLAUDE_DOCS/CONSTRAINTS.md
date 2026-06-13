# CONSTRAINTS — GRAVITY

---

## Purpose of This Document

Every product is defined as much by what it cannot do as by what it can. This document exists to make the constraints explicit, honest, and architectural — so that decisions made early in development do not create expensive surprises later.

Constraints are not problems to apologise for. They are design inputs. The best version of Gravity is built knowing exactly where the walls are.

---

## AI Layer Strategy — Cost Tiers

The AI layer is the most operationally expensive part of Gravity. The strategy is to spend nothing until revenue justifies it, using a tiered approach as the product matures.

### Tier 0 — Demo / Proof of Concept (now)
**Provider:** Claude artifact sandbox (claude.ai built-in API access)
**Cost:** £0
**Usage:** Browser-based demo only. Used to document the creation process, capture marketing content, and validate the concept visually. Not for real users.
**Limits:** Runs inside claude.ai artifacts only. Cannot be deployed externally.

### Tier 1 — Early Users / Beta (0–500 users)
**Provider:** Groq (groq.com)
**Cost:** Free tier — 14,400 requests/day, no credit card required
**Models:** Llama 3.1 70B (conversation quality comparable to GPT-4), Llama 3.1 8B (fast, cheap for nudge decisions)
**Why Groq:** Fastest inference available for open models (~500 tokens/second). Free tier covers hundreds of real daily-active users before any cost is incurred. No per-token billing on free tier.
**Integration:** Drop-in replacement for Claude API — same REST structure, swap base URL and model name.
**Limits:** Rate limits apply. Not suitable for 500+ concurrent active users without paid tier.

### Tier 2 — Growth (500–2,000 users)
**Provider:** Groq paid OR Anthropic Claude API
**Cost:** Groq paid starts at ~$0.05/1M tokens (Llama 3.1 70B). Claude Sonnet ~$3/1M input tokens.
**Decision point:** At ~500 MAU with £4.99 subscriptions = ~£2,495/month revenue. Claude API becomes affordable. Evaluate quality difference and switch if meaningful.
**Target:** Keep AI cost under £0.85/user/month regardless of provider.

### Tier 3 — Scale (2,000+ users)
**Provider:** Anthropic Claude API (Claude Sonnet)
**Cost:** Covered by subscription revenue at this scale
**Why switch from Groq:** Claude's reasoning, tone, and contextual accuracy is meaningfully better for the core product experience — especially onboarding conversation quality and nudge language. The product is worth paying for at scale.

### Ollama (Local — Development Only)
Michael has Ollama running on `mj-notarobot` via Tailscale. Use this for:
- Local development and testing without burning Groq rate limits
- Prompt engineering and onboarding conversation iteration
- Offline development sessions
**Not suitable for production** — single machine, no redundancy, dependent on home network uptime.

### Summary

| Stage | Provider | Cost | When |
|---|---|---|---|
| Demo | Claude artifact sandbox | £0 | Now |
| Beta | Groq free tier | £0 | 0–500 users |
| Growth | Groq paid / Claude API | ~£0.50–0.85/user/month | 500–2,000 users |
| Scale | Claude API (Sonnet) | ~£0.85/user/month | 2,000+ users |
| Dev/testing | Ollama (local, mj-notarobot) | £0 | Always |

---

## Budget Targets

### Hardware BOM

#### Prototype (Stage 2 — Housed Prototype)

| Component | Supplier | Unit Cost |
|---|---|---|
| Waveshare 3.71" Round E-Paper display | Waveshare / AliExpress | £15–22 |
| Capacitive touch overlay (circular matched) | AliExpress | £8–12 |
| Raspberry Pi Zero 2W | Pimoroni / RPi Foundation | £15 |
| LiPo battery 1500mAh | Adafruit / AliExpress | £6–8 |
| TP4056 USB-C charging + protection module | AliExpress | £2 |
| MPU-6050 accelerometer breakout | AliExpress | £2 |
| MEMS microphone breakout (Phase 2) | Adafruit | £4 |
| SPI wiring, headers, JST connectors | AliExpress | £3 |
| 3D printed enclosure — PLA/PETG filament | Local / own printer | £5–10 |
| Misc (standoffs, thermal tape, resistors) | — | £3 |
| **Prototype total** | | **£63–81** |

Target: build 2–3 working prototypes for under £200 total.

#### Production V1 (Stage 4 — ESP32-S3 migration)

| Component | Unit Cost (volume 100) | Unit Cost (volume 1,000) |
|---|---|---|
| Round e-ink display (3.9"–4.2") | £12–15 | £8–11 |
| Capacitive touch overlay | £6–9 | £4–6 |
| ESP32-S3 module | £4–5 | £2.50–3.50 |
| LiPo battery 1500mAh | £4–5 | £2.50–3.50 |
| USB-C charging IC + protection | £1.50 | £0.80 |
| PCB (custom, 2-layer) | £3–4 | £1.50–2 |
| Accelerometer (onboard PCB) | £0.80 | £0.40 |
| Injection moulded enclosure (2-piece + base) | £8–12 | £4–6 |
| Packaging (box, cable, card) | £2–3 | £1.20–1.80 |
| **Production BOM total** | **£41–54** | **£25–33** |

**Target retail price:** £79–£99
**Target gross margin at 1,000 units:** ~65–68% (before fulfilment, VAT, returns)

#### BOM Risk Factors
- Round e-ink displays are a specialist component — Waveshare is currently the primary accessible supplier. Supply chain is thin. **Order displays before designing the enclosure around them — dimensions must be confirmed against physical unit.**
- Capacitive touch overlays for circular displays are not standard off-the-shelf. Rectangular overlays can be cut but introduce reliability risk. Budget extra lead time and prototyping cost for this component specifically.
- ESP32-S3 has had intermittent global supply issues. Identify a secondary source (e.g. Espressif-certified distributors) before committing to production design.

---

### App Development Costs

#### Zero-budget path (solo build)
All app development done by the founder using React Native (Expo). No external contractors.

Costs:
| Item | Cost |
|---|---|
| Apple Developer Program (iOS distribution) | £99/year |
| Google Play Developer Account | £25 one-time |
| Expo EAS Build (cloud builds) | Free tier → £15/month at scale |
| Figma (design) | Free tier sufficient for solo |
| **Total year 1** | **~£139–£175** |

#### Contracted development (if needed)
If app development is contracted out for specific components (e.g. native HealthKit bridge, Android UsageStats integration):
- Freelance React Native developer: £300–600/day
- Budget £2,000–4,000 for the native integration work specifically
- Everything else is buildable without specialist iOS/Android native expertise

---

### Backend Costs

#### Stage 0–1 (development, no users)
| Item | Cost |
|---|---|
| Hetzner CX22 VPS (2 vCPU, 4GB RAM) | £4.50/month |
| PostgreSQL (self-hosted on VPS) | £0 |
| Redis (self-hosted on VPS) | £0 |
| Domain + SSL (Let's Encrypt) | ~£10/year |
| Claude API — development usage | £10–30/month (testing) |
| **Total/month** | **~£25–35** |

#### Stage 2 (0–500 users)
| Item | Cost |
|---|---|
| Hetzner CPX21 (3 vCPU, 4GB RAM) | £6/month |
| Database backups (Hetzner Snapshot) | £1.50/month |
| Claude API (~30 AI calls/user/day avg) | ~£0.50–0.80/user/month |
| Upstash Redis (managed, free tier → paid) | £0–5/month |
| **Total at 500 users** | **~£270–420/month** |
| Subscription revenue at 500 users (£4.99) | **£2,495/month** |
| **Margin** | **~83–89%** |

#### Stage 3 (500–2,000 users)
| Item | Cost |
|---|---|
| Hetzner CPX31 (4 vCPU, 8GB RAM) | £12/month |
| Separate DB server (CPX21) | £6/month |
| Claude API | ~£0.80/user/month |
| CDN (Cloudflare — free tier) | £0 |
| Monitoring (Grafana Cloud free tier) | £0 |
| **Total at 2,000 users** | **~£1,660/month** |
| Revenue at 2,000 users | **£9,980/month** |

#### Claude API Cost Model (detailed)

Claude Sonnet 4.6 pricing (as of build time — verify current pricing at anthropic.com):
- Input: ~£2.40 per million tokens
- Output: ~£12 per million tokens

Estimated tokens per user per day:
| Call type | Frequency | Input tokens | Output tokens |
|---|---|---|---|
| Nudge decision | 8× avg | 800 | 150 |
| Nudge content | 2× avg | 500 | 100 |
| UI layout gen | 1× | 1,500 | 400 |
| Nightly pattern | 1× | 2,000 | 300 |
| **Daily total** | | **~12,400** | **~1,900** |

Daily cost per user: ~(12,400 × £0.0000024) + (1,900 × £0.000012) = £0.030 + £0.023 = **~£0.053/day = ~£1.59/month**

At 83% gross margin target on £4.99 subscription — Claude API must stay under £0.85/user/month.
Optimisation levers if costs exceed target:
1. Reduce nudge decision frequency from every 15 min to every 30 min — halves the most frequent call
2. Cache UI layout for 24 hours unless goal data changes — eliminates daily regeneration call
3. Compress user context passed to Claude — smaller prompt = lower input token cost
4. Batch nightly pattern detection across users in a single call where possible

---

## Platform Constraints — iOS

### What Apple Allows

| Capability | Available | Method |
|---|---|---|
| Calendar read/write | ✓ | EventKit — full access with permission |
| Health data (steps, sleep, workouts, heart rate) | ✓ | HealthKit — with permission prompt |
| Location (background) | ✓ (restricted) | Always-on location requires explicit justification to App Store reviewers |
| Push notifications | ✓ | Standard APNs — requires permission |
| Bluetooth (device pairing) | ✓ | CoreBluetooth |
| WiFi credentials (pass to device) | ✓ (limited) | NetworkExtension or manual user entry — cannot read current WiFi password |
| Background app refresh | ✓ (limited) | 15-minute minimum interval, iOS throttles aggressively based on usage |
| Local notifications (scheduled) | ✓ | UNUserNotificationCenter — scheduled locally, no server needed |
| On-device ML inference | ✓ | CoreML — relevant for future on-device pattern detection |
| Microphone | ✓ | With permission — works for voice onboarding |
| Camera | ✓ | With permission |

### What Apple Does Not Allow

| Capability | Status | Impact on Gravity | Workaround |
|---|---|---|---|
| Screen Time / app usage data | ✗ BLOCKED | Cannot detect doom scrolling natively | Apple Shortcuts webhook (see below) |
| Reading other apps' notifications | ✗ BLOCKED | Cannot detect if user received a message they're ignoring | None — not available |
| Background execution (continuous) | ✗ BLOCKED | Cannot run a persistent background process watching behaviour | Scheduled background fetch (15 min+) only |
| Accessing other apps' data | ✗ BLOCKED | Cannot see Spotify playback state natively without Spotify API | Use Spotify Web API via backend |
| Intercepting outgoing network traffic | ✗ BLOCKED | Cannot monitor which apps are making network requests | None |
| Writing to system settings | ✗ BLOCKED | Cannot programmatically enable/disable app limits | None |
| MDM Screen Time controls (third-party) | ✗ (restricted) | Parental control-style app limits require MDM enrolment — users will not accept this | None viable |

### iOS Screen Time Workaround — Detailed

Apple Shortcuts can trigger on app usage. This is the only legal path to screen time data on iOS.

**How it works:**
1. In the app, user taps "Set up Screen Time alerts"
2. App presents a step-by-step guide — one tap opens the Shortcuts app with a pre-built shortcut template
3. The shortcut is: "When I've had [TikTok] open for [30 minutes] → POST to [user's personal Gravity webhook URL]"
4. User confirms and saves — takes 90 seconds
5. Backend receives POST, evaluates context, decides whether to nudge

**Limitations:**
- Requires user to set up manually — not automatic
- One shortcut per app being monitored — user must create separate shortcuts for each
- Shortcuts can be unreliable when iOS is under memory pressure
- iOS may not trigger the shortcut if the app is backgrounded quickly

**How Gravity handles this honestly:**
- The setup screen explains exactly how it works and why
- It is presented as optional ("for the full experience") not required
- If no shortcuts are set up, Gravity simply cannot detect phone avoidance on iOS — it says so
- The feature is labelled "Screen Time (via Shortcuts)" in integrations — not pretending it's native

**Android comparison:** Android UsageStats API is fully open to third-party apps with a single permission grant. The feature works natively, fully, and continuously on Android. This is a meaningful platform advantage for Android users and should be called out in product positioning.

### App Store Review Risks

| Risk | Mitigation |
|---|---|
| Rejection for "collecting excessive data" | All data collection is opt-in with explicit permissions. Privacy policy must be clear and prominent. |
| Rejection for Screen Time claims | Never claim "Screen Time integration" in App Store listing — say "Focus tracking via Shortcuts" |
| Rejection for open banking | Plaid/TrueLayer are approved integrations. Must include clear data usage disclosure. |
| Background location justification | If location is used (geofence nudges) — must justify in App Store review notes. Consider making location features opt-in Phase 2 only. |

---

## Platform Constraints — Android

### What Android Allows (with permissions)

| Capability | Available | Permission Required |
|---|---|---|
| Calendar read/write | ✓ | READ_CALENDAR / WRITE_CALENDAR |
| Health data (via Health Connect) | ✓ | health_read permissions |
| App usage statistics | ✓ | PACKAGE_USAGE_STATS (user must grant in Settings) |
| Foreground service | ✓ | FOREGROUND_SERVICE — persistent process visible to user |
| Background execution | ✓ (better than iOS) | WorkManager for reliable background jobs |
| Notification access | ✓ | BIND_NOTIFICATION_LISTENER_SERVICE |
| Bluetooth | ✓ | BLUETOOTH_CONNECT / BLUETOOTH_SCAN |
| Precise location (background) | ✓ | ACCESS_BACKGROUND_LOCATION — prompts user separately |
| WiFi credentials (to device) | ✓ | More accessible than iOS |
| Overlay permissions | ✓ | SYSTEM_ALERT_WINDOW — can draw over other apps (use with restraint) |

### Android-Specific Constraints

| Constraint | Detail | Impact |
|---|---|---|
| UsageStats requires manual grant | User must go to Settings → Apps → Special App Access → Usage Access → Enable Gravity | ~40% of users will not complete this step. Make the setup flow frictionless with deep link directly to the settings page. |
| Battery optimisation | Android aggressively kills background apps on some OEMs (Xiaomi, Huawei, OnePlus especially) | Must prompt user to add Gravity to battery optimisation whitelist on affected devices. Detect OEM and show device-specific instructions. |
| Health Connect adoption | Android's unified health API — requires Health Connect app installed (now built into Android 14+, older devices need manual install) | Fallback to Google Fit API for older devices |
| Notification listener | Granting notification access is a significant permission — some users will decline | Make optional. Use only if user explicitly wants "notification pattern" tracking. |
| Fragmentation | Android runs on hundreds of device configurations — UI must be tested on varied screen sizes and OEM skins | React Native handles most of this. Native modules (UsageStats, Health Connect) must be tested on Samsung, Pixel, and OnePlus at minimum. |

---

## E-Ink Refresh Rate Constraints

### The Physical Reality

E-ink displays work by moving charged particles between black and white states. This is a physical process, not an electronic one. It cannot be made instantaneous.

| Refresh type | Typical duration | When to use |
|---|---|---|
| Full refresh (with flash) | 1.5–2.5 seconds | Screen state transitions only |
| Partial refresh (no flash) | 300–500ms | In-screen data updates |
| Fast partial (some displays) | 120–200ms | Touch feedback acknowledgement |

The "flash" is the characteristic e-ink inversion that happens during full refresh — screen goes black, then white, then renders. This cannot be eliminated on a full refresh. It is an inherent property of the technology.

### What This Means for UI Design

**Rule 1 — Never animate.**
No progress bars that fill in real time. No spinners. No transitions. E-ink has no concept of animation — each state is a still image. Design every screen as a photograph, not a video.

**Rule 2 — Acknowledge touch before re-rendering.**
When a user taps, the 300–500ms partial refresh feels slow compared to a phone screen. The display must acknowledge the touch within 100ms using a fast partial refresh — invert the tapped region, change a glyph, show a cursor — before doing the full re-render. Without this, the device feels broken.

Implementation:
```python
def on_touch(region):
    display.partial_refresh(region, invert=True)   # immediate — ~100ms
    time.sleep(0.1)
    new_layout = compute_new_layout(region)
    display.full_refresh(new_layout)               # full render — ~2s
```

**Rule 3 — Minimise refresh frequency.**
Every full refresh costs ~2 seconds and draws power. The ambient screen refreshes every 15 minutes maximum. It does not track seconds. It does not animate. It is a calm object.

**Rule 4 — Design for the still image.**
Every screen must be fully legible and meaningful as a static image with no context. The user should be able to pick up the device after a week away and understand exactly what they're looking at.

**Rule 5 — Ghost management.**
E-ink displays can develop "ghosting" — faint traces of previous content visible on the new screen — if full refreshes are not performed regularly. The firmware must perform a full refresh (with flash) at minimum once every 4 hours, even if content has not changed. Schedule this during the quietest period of the user's day (middle of night by default).

**Rule 6 — Temperature sensitivity.**
E-ink displays slow down significantly below 10°C and can become unresponsive below 0°C. This is a physical property that cannot be engineered around in software. The device is designed as an indoor object (desk, bedside table) — document this in hardware documentation and do not position Gravity as an outdoor device.

### Partial vs Full Refresh Decision Tree

```
Content change detected
        ↓
Is this a screen STATE change?
(idle → nudge, heatmap → goal view)
   YES → Full refresh (with flash)
   NO  ↓
Is this a small in-screen data update?
(habit ticked, time update, progress %)
   YES → Partial refresh (no flash)
   NO  ↓
Is this a touch acknowledgement?
   YES → Fast partial invert (~100ms)
```

### Display Driver Circular Masking

The round display requires the firmware to mask all pixels outside the circle boundary. Without this, rectangular pixel bleed appears at the corners of the framebuffer.

```python
# Every render pass must apply circular mask
def render_to_display(layout_json):
    framebuffer = render_layout(layout_json)    # renders to rectangular buffer
    masked = apply_circular_mask(framebuffer)   # zeroes pixels outside circle
    display.write(masked)
```

The circular mask is computed once at boot and cached — it is the same every render. This adds negligible performance overhead.

---

## Offline Behaviour

### Core Principle

The device must never show a broken or empty state. A user who walks past Gravity at 7am before their phone has connected should still see a meaningful, calm screen. The product's value is physical presence — that cannot be contingent on connectivity.

### What the Device Caches Locally

The firmware maintains a local cache updated every time a successful sync occurs:

| Cached data | Storage method | TTL |
|---|---|---|
| Today's e-ink layout JSON | Flash (LittleFS) | Until replaced by new sync |
| Tomorrow's layout JSON (pre-fetched) | Flash | Until tomorrow |
| Non-negotiables list | Flash | Until changed by user |
| Current goal name + progress % | Flash | Until sync |
| User's name | Flash | Permanent until re-onboarding |
| Quiet hours + rest day config | Flash | Until changed |
| Streak count | Flash | Incremented locally, reconciled on sync |

The device can function in a degraded but useful state for up to 72 hours without any internet connection.

### Offline Behaviour by Feature

| Feature | Online | Offline |
|---|---|---|
| Display current layout | ✓ Full | ✓ Cached layout — may be stale |
| Show non-negotiables | ✓ Live | ✓ Cached list |
| Mark habit complete (touch) | ✓ Syncs immediately | ✓ Logged locally — syncs on reconnect |
| Receive nudges | ✓ Real-time | ✗ Not possible — AI runs server-side |
| Goal progress update | ✓ Live | ✓ Last known value |
| Time and date display | ✓ | ✓ RTC keeps time locally |
| Boot sequence | ✓ | ✓ Fully local — no network required |
| Firmware update | ✓ | ✗ Deferred until reconnect |

### Offline Habit Logging

If a user taps to complete a habit while the device is offline:
1. Completion is written to local flash with timestamp
2. Display updates immediately via partial refresh — the user sees the ✓
3. A sync queue is maintained in flash — pending completions with timestamps
4. On reconnect: queue is flushed to backend in chronological order
5. If the same habit was also completed in the app while offline — backend deduplicates by timestamp

### Reconnection Behaviour

```
WiFi lost
    ↓
Device continues on cache
Status glyph: ○ (hollow — offline indicator)
    ↓
WiFi restored
    ↓
WebSocket reconnects (exponential backoff: 2s → 4s → 8s → max 5 min)
    ↓
Flush local sync queue to backend
    ↓
Pull latest layout JSON
    ↓
Full refresh with new layout
    ↓
Status glyph: ● (filled — online)
```

Missed nudges from the offline period are **not replayed**. A nudge about procrastinating 3 hours ago is no longer relevant. The log is updated server-side to show "nudge not delivered — device offline." The pattern detector accounts for offline periods when evaluating nudge response rates.

### When the Phone Is Nearby But App Is Closed

The device communicates with the backend directly over WiFi — it does not route through the phone. The companion app is not required for the device to function.

The phone matters for:
- Integration data syncing (HealthKit, Calendar — these are read by the app and sent to backend)
- Screen Time shortcuts (iOS — these fire regardless of app state)
- App push notifications (secondary nudge channel — not required for device nudges)

If the phone has been offline for more than 24 hours:
- Health data sync will be stale — step counts and workout logs will not be current
- Calendar sync may miss new events — device schedule may be outdated
- Backend AI context will flag health data as "unavailable" and avoid making health-based nudge decisions until data is fresh again

This is acknowledged behaviour — not a bug. The device will still show cached content and the user can interact with it normally.

### Companion App Offline Behaviour

The app uses React Query with aggressive caching:
- All data is readable offline from the local cache
- Habit completions logged offline are queued and synced on reconnect (same as device)
- Heatmap and goal data are shown from cache with a "last updated X ago" label
- The device mirror on the Home screen shows the last known device state
- No error screens — the app always shows content, even if stale

### Device ↔ App Offline Edge Case

Scenario: User completes a habit on the device while offline. Then completes the same habit in the app while the app is also offline. Both reconnect.

Resolution:
- Both send their completion logs to the backend with timestamps
- Backend deduplication rule: if same habit + same calendar day + timestamps within 60 seconds of each other → treat as single completion
- If timestamps are more than 60 seconds apart → log as two separate events, count as one completion for that day (idempotent)
- No data is lost — the log reflects what actually happened

---

## Development Constraints

### Solo Build Constraints

Gravity is being built initially by one person with a day job. This is a real constraint that shapes what gets built in what order.

| Constraint | Implication |
|---|---|
| Limited daily build time (~1–2 hours/day) | Stage 0 (Python brain) is the right starting point — no hardware dependency, immediate testability |
| No native iOS/Android experience yet | Use React Native (Expo) — avoids native code for 90% of the app. Native modules (HealthKit, UsageStats) are the only exception. |
| No PCB design experience yet | Prototype on RPi Zero 2W + breadboard — validate all logic before touching custom PCB design |
| No injection moulding budget | 3D print all prototypes. Injection moulding only relevant at 500+ unit volumes. |
| AI API costs during development | Use Claude Haiku for development/testing (significantly cheaper). Switch to Sonnet for production quality. |

### Technical Debt to Avoid Early

| Temptation | Why to avoid it |
|---|---|
| Building the app before the AI brain works | The AI is the product. A beautiful app with weak AI is a shell. Build and validate the conversation engine first. |
| Designing the enclosure before confirming display dimensions | Round e-ink panels vary by ±3–5mm from spec. Order the display, measure it, then design the enclosure. |
| Skipping the layout JSON abstraction | If the device renders hardcoded layouts instead of interpreting JSON, every UI update requires a firmware flash. The JSON abstraction layer is not optional. |
| Using localStorage or client-side AI calls | All AI runs server-side. No exceptions. Putting API keys in a mobile app is a security failure. |
| Building all integrations at once | Start with Calendar + Health only. These are the highest-value, lowest-friction integrations. Everything else is Phase 2. |
| Premature optimisation of Claude API costs | Optimise for quality first. Measure actual costs at 50 real users. Then optimise. Premature token-shaving produces worse AI. |

---

## Summary Constraint Table

| Constraint | Hard limit | Workaround / mitigation |
|---|---|---|
| iOS Screen Time data | Not accessible natively | Apple Shortcuts webhook — opt-in, manual setup |
| iOS background execution | ~15 min intervals, throttled | Scheduled local notifications + server push via APNs |
| E-ink full refresh | 1.5–2.5 seconds | Partial refresh for touch feedback, full refresh on state transitions only |
| E-ink temperature | Sluggish <10°C, failure <0°C | Indoor-only device — document limitation |
| Round e-ink supply chain | Limited suppliers | Order displays before enclosure design. Identify secondary source. |
| Circular touch overlays | Not standard off-the-shelf | Custom cut or source from specialist. Budget extra prototype time. |
| Claude API cost | Must stay ~£0.85/user/month | Context caching, call frequency limits, Haiku for dev |
| Android OEM battery killing | Xiaomi/Huawei/OnePlus aggressive | Deep-link to OEM-specific battery whitelist settings |
| Solo build velocity | ~1–2 hrs/day | Stage 0 first — brain before hardware, validate before scaling |
| Prototype BOM | £63–81 per unit | RPi Zero 2W for prototype, ESP32-S3 for production migration |
