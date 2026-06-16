# GRAVITY — V1 PCB DESIGN SPECIFICATION

**Target:** Stage 4 production board (ESP32-S3 migration)
**Status:** Design-ready. Build only after Stage 2 logic is validated on RPi/breadboard (per `CONSTRAINTS.md`).
**Tooling:** KiCad 8 (open-source, fits the OSS stack; component libs via SnapEDA / Ultra Librarian).
**Board count:** 2 — main device board + base power board, bridged by 2 pogo contacts.

---

## 0. Why this is the production board, not the prototype

`CONSTRAINTS.md` and `PROJECT_CONTEXT.md` are explicit: prototype on RPi Zero 2W + breadboard, validate logic, *then* design a PCB. A custom board for the RPi prototype would be wasted effort — the RPi already is a board. The custom PCB is the **ESP32-S3 production design**, and that's what's specified here. Everything below is sequenced to be picked up at Stage 4, with sensors and interfaces already proven on the breadboard.

The one thing you should do *early* (it has long lead time and dictates the FPC pinout): **order the round e-ink panel and pull its actual FPC datasheet.** The connector pinout below is a placeholder until you have the real panel in hand.

---

## 1. System block diagram

```
                            BASE BOARD (small)
        ┌─────────────────────────────────────────────────┐
        │  USB-C 5V ── ESD ── input fuse ── 5V             │
        │  CC1/CC2 → 5.1k pulldowns (sink, 5V/default)     │
        │  VBUS ─────────────┐         GND ───────────┐    │
        └────────────────────┼─────────────────────── ┼───┘
                             POGO 5V                  POGO GND
                              │                         │
        ════════════ lift-out interface (2 spring contacts) ════════════
                              │                         │
        ┌─────────────────────┼─────────────────────────┼─────────────┐
        │  DEVICE BOARD       ▼                          ▼             │
        │   5V ─► [BQ24074 charger + power-path] ─► VSYS               │
        │            │   ▲                                             │
        │         LiPo  STAT                                           │
        │         1500mAh                                              │
        │   VSYS ─► [TPS62840 buck 3.3V, 60nA Iq] ─► 3V3 rail          │
        │   BAT  ─► [MAX17048 fuel gauge, I2C] ───────────────┐        │
        │                                                     │        │
        │   3V3 ─► ESP32-S3-WROOM-1-N16R8 (16MB flash/8MB PSRAM)       │
        │            │                                        │        │
        │      ┌─────┼──────────────┬──────────────┐   ┌──────┴──────┐ │
        │     SPI   I2C            I2S(P2)        UART  │  I2C bus     │ │
        │      │     │              │              │    │  (shared)   │ │
        │   ┌──┴──┐  ├─ CST816S touch (INT→wake)   prog │  fuel gauge │ │
        │   │EPD  │  ├─ LIS2DW12 IMU (INT→wake)         │  touch       │ │
        │   │FPC  │  ├─ VEML7700 ambient light          │  IMU         │ │
        │   └─────┘  ├─ TMP117 temp (P2, DNP)           │  ALS         │ │
        │   microSD  └─ MEMS mic (P2, I2S, DNP)         └─────────────┘ │
        │   (DNP)                                                       │
        └───────────────────────────────────────────────────────────── ┘
```

---

## 2. Functional blocks

### 2.1 MCU — ESP32-S3-WROOM-1-N16R8

- **Module, not bare silicon.** Pre-certified PCB antenna, integrated flash + PSRAM, no RF layout/tuning skill required. Correct choice for a first PCB.
- **N16R8** = 16 MB QSPI flash + **8 MB octal PSRAM** — matches the memory spec in `HARDWARE.md` exactly (16 MB flash / 8 MB PSRAM).
- Dual-core 240 MHz, WiFi b/g/n + BLE 5.0, native USB, deep sleep ~10 µA.
- **Critical pin caveat:** octal PSRAM consumes GPIO33–37, and flash uses GPIO26–32 internally. **Do not route to GPIO26–37.** Treat them as unavailable. This is the #1 mistake on S3-R8 boards.
- Decoupling: 100 nF + 10 µF on 3V3 at the module; bulk 22 µF nearby (WiFi TX current bursts).
- Strapping pins: GPIO0 → BOOT button only; leave GPIO3/45/46 at default loading (no pull-ups/downs that flip boot mode).

### 2.2 Power — input, charge, regulate, gauge

**Input (BASE board):** USB-C receptacle, 5.1 kΩ pulldowns on CC1/CC2 (configures as 5 V sink), TVS diode array on VBUS for ESD/surge, optional resettable PTC fuse (~1 A). Only VBUS + GND cross the pogo interface.

**Charger + power-path (DEVICE board): TI BQ24074**
- Integrated Li-ion charger **with dynamic power-path management** — the system runs from USB *and* charges the battery simultaneously without cycling the cell. This matters because Gravity is "primarily a plugin device" — without power-path, the battery micro-cycles every time it sits in the base, killing its lifespan.
- Programmable charge current via ISET resistor (set ~0.5C ≈ 750 mA for 1500 mAh).
- STAT pin → ESP32 GPIO for charge state (drives the battery glyph logic).
- *Tradeoff vs TP4056:* TP4056 is £0.30 cheaper and what the prototype uses, but has no power-path or load-sharing, so the cell cycles constantly on a plugged-in device. For a desk device that lives on charge, BQ24074 is the right call. MCP73871 is an acceptable second source.

**3.3 V regulator: TI TPS62840 buck**
- **60 nA quiescent current.** This single choice is what makes the multi-week battery target real. WiFi TX peaks ~500 mA, so an LDO would burn ~0.45 W as heat on every sync and waste battery; the buck is >90% efficient under load and effectively invisible in deep sleep.
- 750 mA capable — covers the ESP32 WiFi peak + e-ink refresh boost transient.
- *Tradeoff:* a buck needs an inductor (2.2 µH) and is slightly fiddlier to lay out than an LDO. Given the battery-life requirement, non-negotiable. Keep the inductor/feedback loop tight.

**Fuel gauge: MAX17048**
- I2C, ModelGauge (no sense resistor needed), ~3 µA quiescent. Gives the corner battery glyph a *real* state-of-charge %, not a crude voltage guess.
- *Fallback:* if you want to drop a part, a resistor divider on BAT into an ADC works but reads garbage under load and during charge. Keep the gauge; it's £1 and the battery glyph is a user-facing spec.

### 2.3 E-ink display interface (SPI)

Signals: `SCLK, MOSI, EPD_CS, EPD_DC, EPD_RST, EPD_BUSY` (BUSY is an input, often open-drain — add pull-up). MISO is not used by the panel.

Round e-paper panels (Waveshare 3.71" round and similar, typically SSD16xx / UC825x-class controllers) run an **on-glass charge pump** that needs an external cap network on VGL/VGH/VDH/VDL/VCOM/VPP — usually 1 µF X7R each, plus the boost diode/inductor or the controller's internal pump caps per the panel datasheet. **Copy this network verbatim from your ordered panel's reference schematic** — it varies by controller and getting it wrong is the most common e-paper bring-up failure.

**FPC connector:** typically 24-pin 0.5 mm pitch, flip-lock, bottom-contact — **but confirm against the real panel.** Place it at the board edge nearest the display ribbon exit. Add a 0 Ω/test-pad on each rail for bring-up probing.

### 2.4 Capacitive touch — CST816S

- Single-touch self-cap controller with **hardware gesture recognition** (tap, double-tap, long-press, swipe up/down/left/right) — maps directly to the touch spec in `HARDWARE.md` with no firmware gesture code needed.
- I2C (on the shared bus) + `TOUCH_INT` + `TOUCH_RST`.
- **`TOUCH_INT` routes to an RTC-capable GPIO** so the ESP32 wakes from deep sleep on touch (the "wake on touch" requirement). CST816S has a low-power mode that asserts INT on contact.
- The circular touch overlay is a known risk (`CONSTRAINTS.md`): not off-the-shelf. The controller is on *your* PCB; only the sensor film is on the overlay, connected by its own small FPC. Confirm overlay FPC pinout against the supplied part.

### 2.5 IMU — LIS2DW12

- 3-axis accelerometer, I2C, **down to ~1 µA** in low-power mode with hardware 6D orientation + wake-on-motion interrupt.
- Drives desk-mode vs held-mode detection and UI rotation. `IMU_INT` → RTC GPIO (wake on pick-up).
- *Tradeoff vs MPU-6050 (prototype part):* MPU-6050 is a 6-axis gyro+accel but draws ~3.6 mA active and is EOL-ish. You don't need the gyro for orientation; the LIS2DW12 is ~3 mA cheaper in power budget terms and far better for deep sleep. Swap it in at Stage 4.

### 2.6 Ambient light — VEML7700

- I2C ambient light sensor, Phase 1. Used to adapt contrast / future frontlight. Mount near a light-pipe or bezel aperture so it actually sees ambient light, not the enclosure interior.

### 2.7 Phase 2 sensors (footprints loaded DNP — Do Not Populate)

Lay these down now so you never respin the board for Phase 2:
- **MEMS mic:** PDM mic (e.g. ICS-43434 I2S, or a 2-wire PDM part). ESP32-S3 I2S handles it. Reserve 3 pads + a mic acoustic port hole in the enclosure CAD.
- **Temp sensor:** TMP117 (I2C, ±0.1 °C). Place away from the ESP32 and the buck inductor so it reads room temp, not self-heat.

### 2.8 microSD (optional, DNP)

- "SD card slot (optional) for future firmware expansion" — push-push microSD on the **shared SPI bus** with its own `SD_CS`. DNP by default; populate if needed. E-ink and SD coexist on one SPI bus fine with separate chip-selects.

### 2.9 Programming & debug

- USB-C is **power-only in v1**, so production flashing isn't over USB-C. Provide:
  - A **6-pin programming header / Tag-Connect pad** (`3V3, GND, TXD0, RXD0, EN, IO0`) for a USB-UART adapter.
  - The classic **two-transistor auto-reset circuit** (DTR/RTS → EN/IO0) so esptool flashes without manual button presses.
  - **BOOT button on GPIO0** and **RESET button on EN** (or test pads to save BOM).
  - Native **USB D-/D+ (GPIO19/20)** brought to test pads for recovery/JTAG-over-USB during development.

---

## 3. ESP32-S3 GPIO map

Avoids all flash/PSRAM pins (26–37) and respects strapping pins. RTC-capable pins (0–21) used for all wake sources.

| Function | Net | GPIO | Notes |
|---|---|---|---|
| SPI clock | SCLK | 12 | E-ink + SD shared |
| SPI MOSI | MOSI | 11 | |
| SPI MISO | MISO | 13 | SD only |
| E-ink chip select | EPD_CS | 10 | |
| E-ink data/command | EPD_DC | 9 | |
| E-ink reset | EPD_RST | 8 | |
| E-ink busy | EPD_BUSY | 7 | input, pull-up |
| SD chip select | SD_CS | 14 | DNP path |
| I2C data | SDA | 4 | shared: touch/IMU/ALS/gauge/temp |
| I2C clock | SCL | 5 | 4.7 kΩ pull-ups |
| Touch interrupt | TOUCH_INT | 6 | RTC wake |
| Touch reset | TOUCH_RST | 15 | |
| IMU interrupt | IMU_INT | 16 | RTC wake (pick-up) |
| Charger status | CHG_STAT | 17 | input from BQ24074 STAT |
| Mic I2S BCLK (P2) | I2S_BCLK | 1 | DNP |
| Mic I2S WS (P2) | I2S_WS | 2 | DNP |
| Mic I2S DATA (P2) | I2S_DIN | 42 | DNP |
| UART TX (prog) | TXD0 | 43 | |
| UART RX (prog) | RXD0 | 44 | |
| USB D- | USB_DM | 19 | native USB, test pad |
| USB D+ | USB_DP | 20 | native USB, test pad |
| Boot strap | BOOT | 0 | BOOT button only |

Free/spare for spins: GPIO18, 21, 38, 39, 40, 41, 47, 48.
**Reserved — do not route:** GPIO26–37 (flash + octal PSRAM), GPIO3/45/46 (strapping, leave default).

---

## 4. Power budget (validating the multi-week target)

Battery: 1500 mAh LiPo. Target 2–4 weeks on battery (`HARDWARE.md`).

| State | Current draw | Notes |
|---|---|---|
| Deep sleep | ESP32 ~10 µA + buck 60 nA + gauge ~3 µA + IMU ~1 µA + touch LP ~3 µA + leakage ≈ **~20 µA** | Comfortably under the <1 mA spec |
| E-ink full refresh | ~30–40 mA for ~2 s | Charge-pump transient |
| WiFi sync burst | ~120 mA avg, ~500 mA peak, a few seconds | Limited by sync frequency on battery |
| Touch wake + partial refresh | ~20–30 mA for <0.5 s | |

**Rough battery-life math (battery-only, conservative):**
Assume deep sleep most of the time at ~20 µA, plus ~8 refreshes/day (full+partial) and 4 WiFi syncs/day at a few seconds each.
- Sleep: 0.020 mA × 24 h ≈ 0.48 mAh/day
- Refreshes: 8 × (35 mA × 2 s / 3600) ≈ 0.16 mAh/day
- Syncs: 4 × (120 mA × 5 s / 3600) ≈ 0.67 mAh/day
- **≈ 1.3 mAh/day → 1500 mAh / 1.3 ≈ ~1,100 days theoretical**

Real-world derate hard (self-discharge, WiFi association overhead, regulator inefficiency at µA loads, cold): even at a 30–50× derate you clear weeks easily. The e-ink-holds-image-at-zero-power property is what makes this work — the design lives in deep sleep and the buck's 60 nA Iq keeps the floor low. **The 60 nA buck and the deep-sleep-capable sensor selection are the parts doing the heavy lifting here.** If you'd substituted an LDO + MPU-6050, the floor would be ~4 mA and the multi-week target would be dead.

---

## 5. PCB physical & stackup

- **Layers:** 2-layer (matches the £1.50–4 PCB budget line). Module's onboard antenna means no controlled-impedance RF routing needed.
- **Thickness:** 1.0 mm (lighter — helps the <200 g target — and lets the board sit close behind the display).
- **Stackup:** Top = components + signal; Bottom = solid GND pour + minimal routing; stitch GND with vias, especially around the buck and under the module.
- **Shape:** circular, ~75–85 mm diameter, sitting behind the ~95–105 mm display inside the 110–120 mm enclosure. FPC connector at the board edge under the display ribbon exit.
- **Antenna keepout:** place the ESP32-S3 module at the board edge with its antenna end overhanging into a **plastic-only region** — no copper, no battery, no metal within the module's keepout zone. Battery on the opposite side of the board.
- **Thermal:** keep the ESP32 module and the buck inductor physically away from the LiPo (`HARDWARE.md` calls out heat-near-battery as a known risk). Put the battery on the far side, ideally with the board between heat sources and cell.
- **Pogo contacts:** 2 spring/pogo pads on the *back* of the device board mating to the base, carrying VBUS (5 V) + GND. Size for ~1 A charge current. Add a generous GND pad and a series TVS on VBUS at the entry point.

---

## 6. Bill of materials (key actives — production targets from `CONSTRAINTS.md`)

| Ref | Part | Function | Bus/IF | ~Cost @100 |
|---|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N16R8 | MCU, WiFi/BLE, 16MB/8MB | — | £4–5 |
| U2 | BQ24074 | Charger + power-path | I/O STAT | £1.20 |
| U3 | TPS62840 | 3.3 V buck (60 nA Iq) | — | £0.70 |
| U4 | MAX17048 | Fuel gauge | I2C | £1.00 |
| U5 | CST816S | Cap-touch controller | I2C + INT/RST | £0.60 |
| U6 | LIS2DW12 | Accelerometer/IMU | I2C + INT | £0.80 |
| U7 | VEML7700 | Ambient light | I2C | £0.50 |
| U8 | ICS-43434 (DNP) | MEMS mic (Phase 2) | I2S | £1.20 |
| U9 | TMP117 (DNP) | Temp (Phase 2) | I2C | £1.00 |
| J1 | FPC 24p 0.5mm | E-ink panel | SPI | £0.40 |
| J2 | FPC (per overlay) | Touch overlay | I2C | £0.30 |
| J3 | JST-SH 2p | Battery | — | £0.10 |
| J4 | microSD push-push (DNP) | SD slot | SPI | £0.50 |
| — | L 2.2 µH, caps, resistors, TVS, buttons | passives | — | ~£1.00 |
| **Base board** | USB-C recept + 5.1k CC + TVS + PTC | input | — | ~£0.80 |

Lands inside the `CONSTRAINTS.md` production BOM envelope (custom 2-layer PCB £3–4 @100, falling to £1.50–2 @1k). Note: this active-component spec is slightly richer than the constraints' line-item estimate (you've added power-path + fuel gauge); ~£2–3/unit more, justified by battery longevity and a real battery glyph. Decide that tradeoff explicitly at Stage 4.

---

## 7. I2C bus address check

All on one bus (SDA=GPIO4, SCL=GPIO5, 4.7 kΩ pull-ups):

| Device | Default addr |
|---|---|
| MAX17048 | 0x36 |
| CST816S | 0x15 |
| LIS2DW12 | 0x18 / 0x19 (SDO-selectable) |
| VEML7700 | 0x10 |
| TMP117 (P2) | 0x48–0x4B |

No collisions. If you ever add a second 0x18-class part, use the LIS2DW12 SDO pin to move it to 0x19.

---

## 8. Known risks / call-outs

1. **FPC pinout is a placeholder.** Confirm against the *ordered* panel before routing J1 — e-paper pinouts and the charge-pump cap network are controller-specific. This is gated by the project's "order display first" rule.
2. **Octal PSRAM pins.** GPIO26–37 are gone on N16R8. The GPIO map above already respects this; don't "reclaim" those pins.
3. **Circular touch overlay** remains the riskiest mechanical/sourcing item (per `CONSTRAINTS.md`). The controller being on your PCB de-risks the electronics; the sensor film + its FPC is the unknown. Prototype the overlay-to-board connection early.
4. **Buck layout discipline.** TPS62840 needs a tight inductor + feedback loop and good input cap placement, or you'll get ripple/EMI. This is the one block where a first-time layout most often goes wrong — follow the datasheet layout figure exactly.
5. **Secondary source the ESP32-S3** (intermittent global supply, per `CONSTRAINTS.md`) before committing.

---

## 9. Build path (you have no PCB experience yet — `CONSTRAINTS.md`)

1. **Don't build this yet.** Finish Stage 0 (brain), Stage 1 (backend + app), Stage 2 (RPi breadboard) — prove every interface above in software/breadboard form first.
2. When you reach Stage 4: rebuild the same circuit on **breakout boards wired to an ESP32-S3 devkit** (Adafruit/SparkFun versions of every IC above exist). Get firmware running against real silicon.
3. Only then schematic-capture this in **KiCad**, import footprints (SnapEDA), route the 2-layer board, run DRC.
4. First spin: order 5 boards from JLCPCB/PCBWay (~£2–5 + assembly). Expect a respin — budget for it.
5. Bring-up order: power rails → ESP32 flashing → I2C scan (confirm all addresses) → e-ink → touch → sensors.

---

*This spec is built against `HARDWARE.md`, `CONSTRAINTS.md`, and `PROJECT_CONTEXT.md`. The two highest-leverage design choices — the BQ24074 power-path charger and the 60 nA TPS62840 buck — are what turn the "multi-week battery, primarily-plugged-in" requirement from aspiration into something the hardware actually delivers.*
