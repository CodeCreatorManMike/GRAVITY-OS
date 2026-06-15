# GRAVITY — FINAL MODEL BUILD SPECIFICATION (V1 / Demo Unit)

**Compute:** ESP32-S3-WROOM-1-N16R8 module on a custom 2-layer PCB
**Scope:** Everything needed to build one shippable-quality demo unit — industrial design, every internal component, the full shopping list, what attaches to what, and the build sequence.
**Status:** Design-ready. Build at Stage 4, after Stage 2 breadboard validation.
**EDA tool:** KiCad 8 (open source). **Enclosure:** Fusion 360 / FreeCAD → 3D print (PETG) for the demo.

---

## 1. What the final unit is

A circular, black-and-white e-ink object that sits on a desk or bedside table in a small angled base. It is silent by default, glanceable in under a second, and exists to hold the user to the goal they committed to. All AI runs in the cloud — the device is a calm display terminal that stays in sync, takes touch and voice, and occasionally speaks or shows a nudge.

The demo unit must look and behave like a finished product, not a prototype: clean back surface, no visible electronics, no loose wires, boots in under 8 seconds, holds weeks of battery, and survives being picked up and put down.

---

## 2. Look & feel — industrial design

### Form

```
        FRONT (display face)                 SIDE (in base)
        ┌───────────────┐
      ╱                   ╲                       ___
     │     ┌─────────┐     │                    ╱     ╲   ← device tilts
     │   ╱             ╲   │                   │  ◜◝   │     back 15–25°
     │  │   ▣  14 ▣     │  │                   │  ▣14▣ │     toward the
     │  │     days       │  │                   │ days  │     user's eyeline
     │   ╲             ╱   │                    ╲_____╱
     │     └─────────┘     │                    ▟█████▙  ← base (puck)
      ╲                   ╱                     USB-C ──┘    holds USB-C
        └───────────────┘
   ~110–120mm diameter circle      tilted on an integrated angled base
```

- **Silhouette:** a slightly-larger-than-HomePod-Mini puck. Circular front face, convex soft-touch back, defined front/back (it is *not* a sphere — it faces the user).
- **Front:** circular e-ink display fills most of the face; minimal 8–12 mm bezel; the bezel is part of the front shell.
- **Back:** smooth convex curve, fits a cupped palm, matte soft-touch (Kindle Paperwhite feel), no buttons, no ports — completely clean.
- **Base:** separate puck that the device seats into, magnetically or friction-fit. Tilts the device back **15–25°** so the screen faces the user when sitting or lying down. The base holds the USB-C port. Device lifts out for handheld use; UI rotates to match (IMU).

### Materials & finish

| Element | Material / finish |
|---|---|
| Front shell + bezel | ABS or PETG, matte black, soft-touch coat |
| Back shell | ABS/PETG, matte black soft-touch, convex |
| Base | ABS/PETG, matte black, weighted for stability |
| Display cover | the e-ink panel's own surface + the touch overlay; no extra glass for demo |
| Colour (V1) | **matte black** — space/terminal aesthetic. Light-grey variant later. |

### Dimensions (target)

| Dimension | Value |
|---|---|
| Total diameter | 110–120 mm |
| Total depth (front→back) | 45–55 mm |
| Display cutout | 95–105 mm |
| Usable display diameter | 90–95 mm |
| Base footprint | ~120 mm dia |
| Base height | ~20 mm |
| Total height in base | ~110–120 mm |
| Weight (device only) | **< 200 g** |
| Weight (with base) | < 280 g |

### Screen aesthetic (what's on the glass)

Pure black/white e-ink. `Space Mono` everywhere. Radial layout — one dominant thing in the centre (a number/word), supporting data in the mid-ring, ambient status (arcs, ticks, glyphs) on the perimeter. No animation, no colour, no icons. Terminal/NASA-display restraint. Boot is a line-by-line terminal print ("GRAVITY OS v1.0.2 … WELCOME BACK, MICHAEL."). Silence after a good day is the product working, not a failure state.

---

## 3. Architecture decision (recap, settled)

**ESP32-S3-WROOM-1 module on a custom PCB.** Not bare-chip (adds full RF intentional-radiator certification + antenna tuning), not a bigger Linux SoC (kills the multi-week battery, blows the BOM, breaks the deep-sleep/e-ink-holds-image model). The S3 covers every on-device job with margin — and its built-in vector/AI acceleration means wake-word and voice/presence work can run on-device when needed.

The device is a terminal: render layout JSON → e-ink, sync over WiFi (WebSocket), pair/proximity over BLE, take touch + voice, drive a small speaker, read sensors, deep-sleep. Nothing here strains the chip.

---

## 4. Internal components — full subsystem breakdown

Each block lists the part, what it does, how it connects, and the bus.

### 4.1 Compute
- **ESP32-S3-WROOM-1-N16R8** — 240 MHz dual-core, 16 MB flash / **8 MB octal PSRAM** (matches spec), WiFi b/g/n + BLE 5.0, native USB, deep sleep ~10 µA, on-board PCB antenna (pre-certified).
- **Pin caveat:** octal PSRAM + flash consume GPIO26–37 — never route there.

### 4.2 Power — input → charge → regulate → gauge
- **USB-C receptacle (on BASE board)** + 5.1 kΩ CC1/CC2 pulldowns (5 V sink) + TVS ESD array + ~1 A PTC fuse. Only VBUS + GND cross to the device.
- **BQ24074** charger **with power-path** — runs from USB while charging the battery without micro-cycling the cell (critical for a plugged-in device). Charge current set ~0.5 C ≈ 750 mA. STAT → GPIO.
- **TPS62840** 3.3 V buck, **60 nA quiescent** — the part that makes weeks-on-battery real. 750 mA covers the WiFi TX peak. Needs a 2.2 µH inductor; lay out per datasheet.
- **MAX17048** fuel gauge (I2C, ~3 µA) — gives the corner battery glyph a real state-of-charge.
- **LiPo 1500 mAh** (1500–2000 mAh acceptable), JST-SH 2-pin.

### 4.3 Display (SPI)
- Round e-ink panel (**Waveshare 3.71" round**, 480×480, primary source) on an FPC connector (≈24-pin 0.5 mm — **confirm against the ordered panel**).
- Signals: `SCLK, MOSI, EPD_CS, EPD_DC, EPD_RST, EPD_BUSY`.
- Panel charge-pump cap network (VGL/VGH/VDH/VDL/VCOM/VPP, ~1 µF X7R each) — **copy verbatim from the panel datasheet**; wrong values are the #1 e-paper bring-up failure.

### 4.4 Touch (I2C + INT)
- **CST816S** single-touch controller with hardware gestures (tap, double-tap, long-press, swipe up/down/left/right) — maps 1:1 to the touch spec, no gesture code needed.
- `TOUCH_INT` → RTC-capable GPIO for **wake-on-touch** from deep sleep. `TOUCH_RST` for control.
- The circular touch overlay sits over the display; only the sensor film + its small FPC are on the overlay — the controller is on your PCB. Overlay sourcing/fit is the known mechanical risk; prototype it early.

### 4.5 Orientation (I2C + INT)
- **LIS2DW12** 3-axis accelerometer, ~1 µA low-power, hardware 6D orientation + wake-on-motion. Drives desk-vs-held detection and UI rotation. `IMU_INT` → RTC GPIO (wake on pick-up). (Replaces the prototype's MPU-6050, which is too power-hungry and has an unused gyro.)

### 4.6 Ambient light (I2C)
- **VEML7700** ambient light sensor (Phase 1). Mounted behind a small bezel aperture / light-pipe so it sees room light, not enclosure interior. Adapts contrast / future frontlight.

### 4.7 Audio in — microphone (I2S)
- **ICS-43434** I2S MEMS mic — voice onboarding, check-ins, ambient detection (`FEATURES.md` voice capability). Needs a small acoustic port hole in the shell. Wake-word can run on the S3's AI acceleration on-device.

### 4.8 Audio out — speaker (I2S)
- **MAX98357A** I2S class-D amp (mono, ~3 W) → small **8 Ω speaker** (~20–28 mm). Delivers spoken AI responses and earned audio rewards.
- Mic and speaker share one I2S clock pair (BCLK + WS) with separate data lines (DIN in, DOUT out) — clean and pin-efficient.
- **Design note:** the product philosophy is "silent by default." Keep the speaker for voice replies and rare rewards, not for nudge alarms (those stay visual on the device / audible on the phone). Treat the speaker + amp as a populate decision if you want a silent demo unit.

### 4.9 Temperature (I2C, Phase 2, DNP)
- **TMP117** (±0.1 °C). Place away from the ESP32 and buck inductor so it reads room temp. Footprint loaded but not populated until Phase 2.

### 4.10 Camera (Phase 3 — honest constraint)
- `FEATURES.md` wants presence/behaviour detection. A full parallel DVP camera (OV2640) needs ~13 GPIO and **does not comfortably fit on a WROOM-1 alongside everything else**. Three realistic paths for Phase 3, decided later:
  1. **Dedicated presence/ToF sensor** (e.g. an STMicro multizone ToF) over I2C — covers "is the user at the desk?" with ~2 pins. *Preferred for presence-only.*
  2. **Low-pin serial/SPI camera** if actual imaging is required.
  3. **A camera board variant** that drops the microSD slot and reallocates pins to a DVP camera.
- For the V1 demo, the camera is **not populated**. The enclosure can include a blanked aperture for a future module.

### 4.11 Storage (optional, DNP)
- **microSD** push-push on the shared SPI bus with its own `SD_CS` — for future firmware expansion. Not populated by default.

### 4.12 Programming / recovery
- USB-C is **power-only in v1**, so flashing is via a **6-pad header / Tag-Connect** (`3V3, GND, TXD0, RXD0, EN, IO0`) with a **two-transistor auto-reset** circuit (DTR/RTS → EN/IO0) so esptool flashes without button presses.
- **BOOT (GPIO0)** + **RESET (EN)** as buttons or test pads. Native **USB D-/D+ (GPIO19/20)** to test pads for recovery/JTAG-over-USB during dev.

---

## 5. ESP32-S3 GPIO map (final, with audio)

Respects flash/PSRAM (26–37) and strapping pins; all wake sources on RTC GPIOs (0–21).

| Function | Net | GPIO | Notes |
|---|---|---|---|
| SPI clock | SCLK | 12 | e-ink + SD |
| SPI MOSI | MOSI | 11 | |
| SPI MISO | MISO | 13 | SD only |
| E-ink CS | EPD_CS | 10 | |
| E-ink D/C | EPD_DC | 9 | |
| E-ink reset | EPD_RST | 8 | |
| E-ink busy | EPD_BUSY | 7 | input, pull-up |
| SD CS (DNP) | SD_CS | 14 | |
| I2C data | SDA | 4 | touch/IMU/ALS/gauge/temp |
| I2C clock | SCL | 5 | 4.7 kΩ pull-ups |
| Touch INT | TOUCH_INT | 6 | RTC wake |
| Touch reset | TOUCH_RST | 15 | |
| IMU INT | IMU_INT | 16 | RTC wake (pick-up) |
| Charger status | CHG_STAT | 17 | from BQ24074 STAT |
| I2S bit clock | I2S_BCLK | 1 | shared mic+amp |
| I2S word select | I2S_WS | 2 | shared mic+amp |
| I2S data in (mic) | I2S_DIN | 42 | from ICS-43434 |
| I2S data out (spk) | I2S_DOUT | 41 | to MAX98357A |
| UART TX (prog) | TXD0 | 43 | |
| UART RX (prog) | RXD0 | 44 | |
| USB D- | USB_DM | 19 | test pad |
| USB D+ | USB_DP | 20 | test pad |
| Boot strap | BOOT | 0 | BOOT button |

**Spare for revisions:** GPIO18, 21, 38, 39, 40, 47, 48.
**Reserved — never route:** GPIO26–37 (flash + octal PSRAM); GPIO3/45/46 (strapping, leave default).

### I2C address map (one bus, no collisions)
| Device | Addr |
|---|---|
| MAX17048 fuel gauge | 0x36 |
| CST816S touch | 0x15 |
| LIS2DW12 IMU | 0x18/0x19 |
| VEML7700 ALS | 0x10 |
| TMP117 temp (P2) | 0x48 |

---

## 6. Power budget (validates weeks-on-battery)

| State | Draw |
|---|---|
| Deep sleep (ESP32 10 µA + buck 60 nA + gauge 3 µA + IMU 1 µA + touch LP 3 µA + leakage) | **~20 µA** |
| E-ink full refresh | ~35 mA for ~2 s |
| WiFi sync burst | ~120 mA avg / ~500 mA peak, few sec |
| Touch wake + partial refresh | ~25 mA < 0.5 s |
| Voice reply (mic + amp + WiFi) | ~150–300 mA while active |

Battery-only rough day (sleep-dominated, ~8 refreshes + 4 syncs/day): **~1.3 mAh/day → multi-week even with heavy real-world derating.** The e-ink holding its image at zero power is what makes this work. Speaker/voice use will cut into this proportionally to how much it's used — that's the main variable.

---

## 7. Complete shopping list — everything to buy

### A. PCB electronics (per device board)

| Part | Function | Where | ~£ @ qty-low |
|---|---|---|---|
| ESP32-S3-WROOM-1-N16R8 | MCU module | Mouser/DigiKey/LCSC | 4–6 |
| BQ24074 | charger + power-path | Mouser/DigiKey | 1.50 |
| TPS62840 + 2.2 µH inductor | 3.3 V buck | Mouser/DigiKey | 1.00 |
| MAX17048 | fuel gauge | Mouser/DigiKey | 1.20 |
| CST816S | touch controller | LCSC/AliExpress | 0.80 |
| LIS2DW12 | accelerometer | Mouser/DigiKey | 1.00 |
| VEML7700 | ambient light | Mouser/DigiKey | 0.60 |
| ICS-43434 | I2S mic | Mouser/DigiKey | 1.50 |
| MAX98357A | I2S amp | Adafruit/Mouser | 1.20 |
| 8 Ω speaker (~20–28 mm) | audio out | AliExpress/Adafruit | 1.50 |
| TMP117 *(DNP, P2)* | temperature | Mouser | 1.00 |
| microSD push-push *(DNP)* | storage | LCSC | 0.50 |
| FPC connector — e-ink (≈24p 0.5 mm) | display IF | LCSC | 0.40 |
| FPC connector — touch overlay | touch IF | LCSC | 0.30 |
| JST-SH 2-pin | battery | LCSC | 0.10 |
| 2× pogo / spring contacts | base power | Mill-Max/AliExpress | 0.60 |
| Passives (caps/res/inductor/TVS/pull-ups) | support | LCSC | ~1.50 |
| 2× tact buttons or test pads | BOOT/RESET | LCSC | 0.20 |
| **Custom 2-layer PCB (device)** | — | JLCPCB/PCBWay | 2–4 |

### B. Base board

| Part | Function | ~£ |
|---|---|---|
| USB-C receptacle | power in | 0.40 |
| 2× 5.1 kΩ CC resistors + TVS array + PTC fuse | input protection | 0.40 |
| 2× pogo receptacle pads | mate to device | 0.30 |
| Small 2-layer base PCB | — | 1–2 |

### C. Display, battery, mechanical

| Part | Function | Where | ~£ |
|---|---|---|---|
| Waveshare 3.71" round e-paper | display | Waveshare/AliExpress | 15–22 |
| Circular capacitive touch overlay | touch surface | specialist/AliExpress (custom cut likely) | 8–12 |
| LiPo 1500 mAh (w/ protection) | battery | Adafruit/AliExpress | 6–8 |
| 3D-printed front shell + bezel | enclosure | own printer / print service | — |
| 3D-printed back shell (convex) | enclosure | — | — |
| 3D-printed base (weighted) | stand | — | — |
| PETG filament (matte) | enclosure stock | Amazon | 5–10 |
| Soft-touch coating / matte paint | finish | hobby/auto store | 5–8 |
| 4–8× M2 threaded inserts + screws | assembly | AliExpress | 2 |
| Acoustic mesh (speaker grille) | audio port | AliExpress | 1 |
| Small magnets (base seating) ×2–4 | base retention | AliExpress | 1 |
| Light pipe / clear window (ALS) | sensor aperture | offcut / 3D print clear | <1 |
| Foam tape, thermal pad, double-sided VHB | mounting | hardware store | 2 |

### D. Tools / one-time (not per unit)

| Item | Use |
|---|---|
| USB-UART adapter (CP2102 / FT232) | flashing the board |
| Hot-air rework station + solder paste + stencil | assembling SMD board (or order PCBA from JLCPCB) |
| Multimeter + (ideally) bench PSU with current limit | bring-up / power debugging |
| 3D printer + PETG | enclosure |
| KiCad 8 (free), Fusion 360 / FreeCAD (free tier) | EDA + CAD |

**Demo-unit cost (rough, low qty):** electronics ~£25–35, display+touch+battery ~£30–42, enclosure/finish/fasteners ~£15–25 → **~£70–100 for one finished demo unit.** Production BOM at volume falls to the £25–33 target in `CONSTRAINTS.md`.

---

## 8. How it all attaches (physical integration)

```
FRONT SHELL (display side)
   ├─ Round e-ink panel — bonded into the bezel cutout (VHB / optical adhesive)
   ├─ Touch overlay — laminated over the e-ink active area, FPC routed inward
   └─ ALS light-pipe — seated in a small bezel aperture

      │ e-ink FPC + touch FPC fold back to the board
      ▼
DEVICE PCB (circular, ~75–85 mm) — mounted on standoffs behind the display
   ├─ ESP32-S3 module at board EDGE, antenna overhanging into plastic-only keepout
   ├─ Speaker mounted to a grille port in the shell, wired to board
   ├─ Mic over an acoustic port hole
   └─ 2 pogo contacts on the BACK of the board

      │ battery on the FAR side of the board from the ESP32 + buck (thermal)
      ▼
LiPo 1500 mAh — secured with foam/VHB, JST-SH to board

BACK SHELL (convex soft-touch) — clips/screws to front shell via threaded inserts

———————————————— device lifts out of ↓ ————————————————

BASE (separate puck)
   ├─ USB-C receptacle + base PCB (protection)
   ├─ 2 pogo RECEPTACLES mate to the device's pogo pins when seated
   ├─ Magnets / friction ribs to seat and hold the device at 15–25° tilt
   └─ Weighted floor for stability; rubber foot ring
```

Key mechanical rules:
- **Antenna keepout:** no copper, battery, or metal near the module's antenna end — point it into plastic.
- **Thermal:** ESP32 + buck on the opposite side/edge from the LiPo (heat-near-battery is a flagged risk).
- **Power transfer:** charging current crosses only the 2 pogo contacts; device runs on battery when lifted, charges when seated. (This is why USB-C lives in the base but the *charger* lives with the battery in the device — you can't separate charger and cell across a lift-out joint.)
- **Repairability:** front/back shells clip or screw, not glue, so the battery is replaceable.

---

## 9. On-device software stack (what runs on the chip)

| Layer | Choice |
|---|---|
| Firmware language | MicroPython (faster iteration) or C++/ESP-IDF (lower power, production) |
| Display | SPI driver + **circular mask applied every render pass** (mask computed once at boot, cached) |
| UI | **renders layout JSON → e-ink** — never hardcoded layouts (no firmware flash for UI changes) |
| Refresh model | full refresh on state transitions only; partial for in-screen updates; 100 ms invert for touch ack *before* re-render |
| Connectivity | WiFi WebSocket to backend (events: LAYOUT_UPDATE, NUDGE, TOUCH_EVENT, HEARTBEAT…); BLE for pairing/proximity |
| Offline | caches today's + tomorrow's layout JSON, non-negotiables, goal %, name, streak in LittleFS; functions degraded-but-useful up to 72 h; reconnect flushes a sync queue |
| Wake sources | touch INT, IMU INT (pick-up), RTC timer; deep sleep between |
| Audio | I2S in (wake-word/voice on-device via S3 AI accel) + I2S out (TTS playback, rewards) |

---

## 10. Build sequence to the demo unit

1. **Order long-lead parts first:** the round e-ink panel + touch overlay (specialist, thin supply — `CONSTRAINTS.md`). Measure the real panel before finalising the enclosure CAD.
2. **Breadboard on an ESP32-S3 devkit** with breakout boards for every IC above. Get firmware fully working: display + circular mask, touch gestures, WiFi/WebSocket sync, BLE pair, IMU orientation, mic, speaker, fuel gauge.
3. **KiCad:** schematic capture → footprints (SnapEDA) → route 2-layer board → DRC. Mirror the breadboard exactly.
4. **First spin:** order ~5 boards (JLCPCB/PCBWay, optionally PCBA). Expect one respin — budget for it.
5. **Bring-up order:** power rails → flash ESP32 → I2C scan (confirm all addresses) → e-ink → touch → IMU/ALS → audio.
6. **Enclosure:** 3D print front/back/base in PETG, soft-touch coat, fit display + touch + speaker + battery + board, mount pogo contacts, seat in base.
7. **Integration test:** boot sequence < 8 s, weeks-scale idle current verified on a bench PSU, lift-out/seat charging, UI rotation, voice round-trip, offline behaviour.

---

## 11. Risks & procurement notes

| Risk | Mitigation |
|---|---|
| Round e-ink FPC pinout + cap network unknown until panel in hand | Order panel first; copy reference schematic verbatim; gate enclosure on physical measurement |
| Circular touch overlay not off-the-shelf | Source specialist or custom-cut; prototype the overlay→board FPC early; budget extra lead time |
| Octal-PSRAM pins (GPIO26–37) | Already excluded in the pin map — don't reclaim them |
| TPS62840 buck layout sensitivity | Follow datasheet layout figure exactly (tight inductor + feedback + input cap) |
| ESP32-S3 supply intermittency | Identify a second authorised distributor before committing |
| Camera (Phase 3) doesn't fit on WROOM-1 with everything else | Use a low-pin presence/ToF sensor, or a camera board variant; not populated for the demo |
| Heat near battery | ESP32 + buck on opposite side from LiPo |
| Speaker vs "silent by default" philosophy | Keep audio for voice replies + rare rewards, not nudge alarms; populate-optional |

---

## 12. Cost & retail summary

| | Demo unit (low qty) | Production @100 | Production @1,000 |
|---|---|---|---|
| Electronics + PCB | ~£25–35 | ~£18–22 | ~£12–15 |
| Display + touch | ~£23–34 | ~£18–24 | ~£12–17 |
| Battery | ~£6–8 | £4–5 | £2.50–3.50 |
| Enclosure + finish | ~£15–25 (3D print) | £8–12 (moulded) | £4–6 (moulded) |
| **Total** | **~£70–100** | **~£48–63** | **~£31–42** |

**Target retail:** £79–£99. **Target gross margin @1,000:** ~65–68%.

---

*Built against `HARDWARE.md`, `FEATURES.md`, `UI_UX.md`, `PROJECT_CONTEXT.md`, and `CONSTRAINTS.md`. The decisions doing the heavy lifting: the WROOM-1 module (sidesteps RF cert + tuning), the BQ24074 power-path charger and 60 nA TPS62840 buck (make weeks-on-battery real), and the layout-JSON render model (UI changes without firmware flashes). The one open hardware item before routing is the e-ink panel's real FPC pinout — order it first.*
