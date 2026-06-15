# HARDWARE — GRAVITY V1

> Detailed, research-backed hardware specification. Every major component has a selected part, exact
> measurements, a primary + backup supplier with links, current pricing, a datasheet link, and design
> notes. Prices are single-unit / low-qty as of mid-2026 and move — treat them as planning figures, not
> quotes. **Always confirm the FPC connector pitch and touch-controller variant against the physical
> panel before committing the PCB.**

---

## 0. Decision Summary

| Decision | Choice | Why |
|---|---|---|
| Display | **2.8" round IPS LCD, ST7701S** (e-ink = future path) | Round e-ink supply is thin (≈1 source). LCD renders the same 1-bit paper-on-ink aesthetic with stable supply, lower volume cost, and instant refresh. |
| Compute | **ESP32-S3-WROOM-1-N16R8** (module) | Pre-certified antenna (no RF cert/tuning), 16 MB flash / 8 MB PSRAM, WiFi+BLE, AI acceleration for on-device wake-word. |
| Charger | **TI BQ24074** (charger + power-path) | Runs from USB while charging without micro-cycling the cell — right for a desk device. |
| Regulator | **TI TPS62840** (60 nA Iq buck) | Lowest practical sleep-floor; the single biggest lever on standby battery life. |
| Fuel gauge | **MAX17048** | Real state-of-charge for the battery glyph, ~3 µA. |
| Architecture | Device = cloud display terminal; 2-board split (device + base) | All AI runs server-side; USB-C lives in base, charger lives with the battery. |

**Critical correction to prior spec:** at 0.146 mm dot pitch on a Ø70.13 mm active area with 480×480 px,
the real pixel density is **≈174 PPI**, not 241 PPI. Use 174 PPI in all rendering/DPI calculations.

---

## 1. Physical Form Factor

Reference object: Apple HomePod Mini (97 mm dia × 84 mm tall). Gravity is a similar footprint, with a
defined front (display) and back (grip), seated in an angled base.

| Dimension | Value | Notes |
|---|---|---|
| Total diameter | 90–100 mm | Driven by the 73 mm panel + 9–13 mm bezel |
| Total depth (front→back) | 40–50 mm | |
| Display cutout diameter | 72–74 mm | Panel outline Ø ≈73 mm + 0.2–0.3 mm clearance |
| Bezel width | 9–13 mm | Display edge → enclosure edge |
| Base footprint | ~100 mm dia | Weighted for stability |
| Base height | ~18 mm | |
| Total height in base | ~95–110 mm | At 15–25° tilt |
| Weight (device only) | < 180 g | |
| Weight (with base) | < 250 g | |

It is not a sphere — convex soft-touch back, circular display face, fixed 15–25° backward tilt so the
screen meets the user's eyeline at a desk or bedside.

---

## 2. Display — 2.8" Round IPS LCD (ST7701S)

This is the most supplier-sensitive component, so it's specified in the most depth. There are **two
distinct things** you can buy, and conflating them is the classic mistake:

### 2A. The bare production panel (what goes in the product)

A raw 2.8" round IPS TFT glass with an **ST7701S** driver-on-glass and an FPC tail. This is what you
design the enclosure and PCB around.

| Property | Value |
|---|---|
| Driver IC | **ST7701S** (on-glass) |
| Shape / type | Circular IPS TFT, colour, LED backlit |
| Resolution | 480 × 480 px |
| Dot pitch | 0.146 × 0.146 mm → **≈174 PPI** |
| Active area | **Ø 70.13 mm** |
| Visual area | Ø 70.73 mm |
| Outline (panel) | **≈73.0 (W) × 76.5 (H) × 2.28 (T) mm** |
| Interface | 3-wire SPI + RGB (SPI for config, RGB for pixel data on ESP32) |
| Brightness | 250–300 cd/m² typ (4× backlight LEDs, ~80 mA @ 3 V) |
| Viewing angle | IPS, ~80° all directions |
| Operating voltage | 2.8–3.3 V logic; backlight ~3 V via PWM |
| Operating temp | −20 to +70 °C |

**Suppliers (bare panel):**
- **TSD / TSLCD — TST028WVBS-33** (2.8" round, 480×480, ST7701S, SPI+RGB, 73.03×76.48×2.28 mm, active Ø70.13). Manufacturer-direct, customisable touch, MOQ-friendly for small runs. [tslcd.com](https://www.tslcd.com/tsd-ips-2-8-inch-round-480x480-resolution-300-nits-spi-rgb-interface-tft-lcd-display-module_p763.html)
- **GL Electronics** — 2.8" round ST7701S, RGB interface, ODM touch/FPC customisation, 3–5 yr supply commitment. [lcdscreenmfg.com](https://lcdscreenmfg.com/product/2-8inch-round-ips-tft-lcd-display-480480-rgb-interface-st7701s-2-76-lcd-screen/)
- **EastRising/BuyDisplay** bare-panel SKUs (ST7701S, MIPI/RGB). Single-unit ~US$17.86. [buydisplay.com](https://www.buydisplay.com/2-8-inch-480x480-mipi-round-circle-screen-ips-tft-lcd-display-st7701s)

> Production cost guide: ~£5–8 each at 100 units, ~£3–5 at 1,000 (manufacturer-direct, MOQ 50–100).

### 2B. The prototyping module (what you breadboard with first)

BuyDisplay's **ER-TFT028-2-6318** Arduino-shield module is the easiest bring-up path, but **note it is not
a bare ST7701S board** — it carries an **LT7683 controller + SSD2828 bridge** and a **GT911** capacitive
touch controller, and its outline is much bigger (64.6 × 117.43 mm) because it's a shield.

| Property | Value |
|---|---|
| Part | **ER-TFT028-2-6318** (EastRising) |
| Controller | LT7683 (+ SSD2828 bridge) |
| Touch | **GT911** capacitive (multi-touch, I²C) |
| Active / visual | Ø70.13 / Ø70.73 mm |
| Interface | I²C, 3-/4-wire SPI |
| Supply current (LCM max) | 220 mA @ 3.3/5 V |
| Price | US$30.29 (1) → US$27.17 (100) |
| Bundle | Arduino shield + ESP32 example code + datasheets |
| Link | [buydisplay.com/round-2-8…](https://www.buydisplay.com/round-2-8-inch-480x480-tft-module-spi-i2c-opt-capacitive-touch-arduino-shield) · datasheet updated Jan-2026 |

**Implication:** firmware written against the eval module's LT7683/GT911 will **not** port 1:1 to a bare
ST7701S + CST816S production panel. Validate the *rendering and touch-zone logic* on the eval module, but
budget driver-layer rework for the production panel. This is exactly why the display HAL (abstraction
layer) must be clean from day one.

### 2C. Aesthetic rendering strategy
Render the e-ink look in software: background `#F4F2EA` (warm paper), foreground `#14130D` (near-black
ink), strict 1-bit palette in V1, backlight PWM'd to ~30–40 % in idle and ~5–10 % at night. Swap
transitions are state swaps, never slides — preserves the calm e-ink feel.

### 2D. Future e-ink path
When a reliable 2.8–3.0" round e-ink source exists at volume, swap **only** the driver layer beneath the
HAL. Everything above is unchanged.

---

## 3. Compute — ESP32-S3-WROOM-1-N16R8

| Property | Value |
|---|---|
| Part | **ESP32-S3-WROOM-1-N16R8** (PCB antenna) / **-1U-N16R8** (U.FL ext. antenna) |
| Core | Xtensa dual-core LX7 @ 240 MHz, vector/AI acceleration (wake-word, person-detect) |
| Memory | 16 MB Quad SPI flash + **8 MB octal PSRAM** |
| Radio | WiFi 802.11 b/g/n + Bluetooth 5 (LE) |
| GPIO | 36, deep sleep ~10 µA |
| Price (1 off) | **US$6.76** (DigiKey/Mouser); ~£2.50–3.50 at volume |
| Datasheet/links | [DigiKey -1-N16R8](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-WROOM-1-N8R8/15295891) · [Mouser -1U-N16R8](https://www.mouser.com/ProductDetail/Espressif-Systems/ESP32-S3-WROOM-1U-N16R8?qs=Li%2BoUPsLEns6V0Pr5KRJtw%3D%3D) · [Espressif](https://www.espressif.com/en/module/esp32-s3-wroom-1u-en) |

**Hard pin caveat:** on the **-N16R8** (octal PSRAM) the PSRAM + flash consume **GPIO26–37 — never route
to those pins.** Keep strapping pins (GPIO0/3/45/46) at default loading. Default to the **-1** (PCB
antenna); only move to **-1U** if in-enclosure range testing disappoints (same price, adds a U.FL cable +
antenna). Secondary-source the module before production (intermittent S3 supply).

Prototype bring-up devkit: **ESP32-S3-DevKitC-1-N8R8** (~US$15, [DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-DEVKITC-1-N8/15199021)).

---

## 4. Power Chain

LCD changes the power story vs e-ink: the **backlight must be on to show anything** (~80 mA), so this is
an hours-to-days device on battery, not weeks. The base is the home; battery is for portability/outage.

### 4A. USB-C input (base board)
- USB-C receptacle (e.g. JAE **DX07S016JA1R1500**, ~US$1.70, [DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-WROOM-1U-N8R8/16162638)) + **5.1 kΩ** CC1/CC2 pulldowns (configures 5 V sink).
- TVS ESD array + ~1 A resettable PTC fuse. Only VBUS + GND cross to the device via 2 pogo contacts.

### 4B. Charger + power-path — TI BQ24074
- Li-ion linear charger with **dynamic power-path**: system runs from USB *and* charges simultaneously, so the cell doesn't micro-cycle every time it sits in the base.
- Programmable charge current via ISET (set ~0.5 C). STAT pin → ESP32 GPIO for charge state.
- Part **BQ24074RGTR** (VQFN-16). [Mouser](https://www.mouser.com/ProductDetail/Texas-Instruments/BQ24074RGTR?qs=ZV%2Fxhq4oszp2Nll7fIx5wg%3D%3D)
- *Budget alt:* TP4056 (no power-path) — fine for prototype, not ideal for an always-plugged device.

### 4C. 3.3 V regulator — TI TPS62840
- **60 nA quiescent**, 1.8–6.5 V in, **750 mA** out, DCS-Control, 1.8 MHz, 16 resistor-selectable output voltages via VSET. Tiny 1.5×2.0 mm package. Needs a 2.2 µH inductor + 4.7 µF input cap; follow the datasheet single-layer layout exactly.
- Part **TPS62840DLCR**. [Mouser](https://www.mouser.com/ProductDetail/Texas-Instruments/TPS62840DLCR?qs=%2B6g0mu59x7L1%2Fxo1joT%2Bvg%3D%3D) · [TI datasheet](https://www.ti.com/product/TPS62840)

### 4D. Fuel gauge — MAX17048
- ModelGauge (no sense resistor), **~3 µA**, **I²C 0x36**, ALRT interrupt → GPIO for low-battery. [datasheet PDF](https://www.mouser.com/datasheet/2/609/MAX17048_MAX17049-3126952.pdf)

### 4E. Battery
- **1000–1500 mAh single-cell LiPo**, JST-PH/SH, with protection.
- Sources: Adafruit **1200 mAh #258**, **2000 mAh #2011** ([adafruit.com](https://www.adafruit.com/product/2011)); or AliExpress 503450-class cells.

| Power property | Spec |
|---|---|
| Primary power | USB-C 5 V via base |
| Battery life (active, backlight on) | ~8–16 h |
| Battery life (standby, backlight off, holds frame) | ~2–3 days |
| Charge time | ~1.5 h |
| On-battery behaviour | dim backlight 10–15 %, slow refresh, increase WiFi sync interval, deep sleep on idle |

---

## 5. Touch Controller

Touch is the primary interaction (tap, double-tap, swipe ×4, long-press; single-touch is enough for V1).

| Option | Part | Touch | Bus | Use |
|---|---|---|---|---|
| Production (recommended) | **CST816S** | single-point + HW gestures, low-power **wake-on-touch** | I²C **0x15** + INT/RST | Cheapest, gesture engine in HW, INT wakes ESP32 from deep sleep |
| Eval / off-the-shelf | **GT911** | up to 5-point | I²C (0x5D/0x14) | Ships on the BuyDisplay eval module |

**Watch-out:** GT911 and CST816 have different default I²C addresses and register maps — confirm the
variant on the *actual* panel before writing the touch driver. `TOUCH_INT` must land on an RTC-capable
GPIO (0–21) for wake-on-touch.

---

## 6. Sensors

| Sensor | Part | Function | Bus / addr | Phase | Link |
|---|---|---|---|---|---|
| Accelerometer / IMU | **LIS2DW12** (ST) | Desk-vs-held orientation, UI rotation, wake-on-pickup; ~1 µA low-power | I²C **0x18/0x19** + INT | 1 | [ST community](https://community.st.com/t5/mems-sensors/lis2dw12-accelerometers-i2c-address-and-read-data/td-p/200812) |
| Ambient light | **VEML7700** (Vishay) | Auto-dim backlight; 0–120k lux, 16-bit, 0.0036 lx/ct | I²C **0x10** | 1 | [Vishay datasheet](https://www.vishay.com/docs/84286/veml7700.pdf) · [Adafruit #4162](https://www.adafruit.com/product/4162) |
| MEMS microphone | **ICS-43434** (TDK) | Voice onboarding/check-ins; on-device wake-word via S3 AI accel | I²S | 2 | [Adafruit #6049 breakout](https://www.mouser.com/ProductDetail/Adafruit/6049?qs=olJun0bQHM88XeFsw90dVw%3D%3D) |
| Temperature | TMP117 (TI) | Passive environment / sleep correlation | I²C 0x48 | 2 | — |
| Camera | OV-class / ToF | Presence / behaviour detection (TBD) | DVP/SPI/I²C | 3 | See §6A |

*Prototype IMU alt:* MPU-6050 breakout (cheap, ~£2) — but it's ~3.6 mA active vs ~1 µA for the LIS2DW12,
so swap to LIS2DW12 for the production board. ALS prototype alt: BH1750 (I²C 0x23).

### 6A. Camera (Phase 3) — honest constraint
A full parallel DVP camera (e.g. OV2640) needs ~13 GPIO and **does not fit** on a WROOM-1 alongside
display + audio + sensors. For presence-only, use a low-pin I²C ToF/presence sensor (~2 pins). If real
imaging is required, use a camera board variant that drops the microSD slot. Not populated in V1.

---

## 7. Audio

| Block | Part | Detail | Bus | Link |
|---|---|---|---|---|
| Mic in | **ICS-43434** | I²S MEMS, needs an acoustic port hole | I²S #0 | [Adafruit #6049](https://www.mouser.com/ProductDetail/Adafruit/6049?qs=olJun0bQHM88XeFsw90dVw%3D%3D) |
| Amp out | **MAX98357A** | I²S Class-D, mono ~3 W, filterless, drives **4 Ω+** speakers | I²S #1 | [Adafruit #3006](https://www.adafruit.com/product/3006) |
| Speaker | 8 Ω, 20–28 mm | Behind acoustic-mesh grille | — | generic |

ESP32-S3 has **two** I²S peripherals → mic-in and speaker-out run simultaneously without contention.
**Design note:** product philosophy is "silent by default" — keep audio for spoken replies + rare
rewards, not nudge alarms. Treat the amp + speaker as populate-optional if you want a silent demo unit.

---

## 8. Connectivity

| Protocol | Purpose |
|---|---|
| WiFi 802.11 b/g/n | Primary data — backend sync (WebSocket), nudge delivery, log push |
| Bluetooth 5 (LE) | Companion-app pairing, proximity |
| USB-C (base) | **Power only in V1** (not data) |

Offline: device caches today's schedule, non-negotiables, goal state in flash; keeps displaying and
accepting touch with WiFi down; syncs on reconnect. All AI is cloud-side — the device is a display
terminal, not a compute node.

---

## 9. Enclosure, Base & Mechanical

**Materials:** ABS or PETG (3D-printed prototype → injection-moulded V1), matte black soft-touch coat,
non-glossy. Anti-glare coating on the display window recommended (LCD reflects more than e-ink).

**Construction:** two-piece shell (front face + bezel / convex back), clip or screw for repairability.
Display recessed flush with the bezel — design the cutout **0.2–0.3 mm larger** than the panel Ø.

**Board layout rules:**
- ESP32 module at the board edge, antenna end overhanging a **plastic-only keep-out** (no copper/metal/battery near it).
- ESP32 + buck on the opposite side from the LiPo (thermal — heat-near-battery is a flagged risk).
- 0.5 mm-pitch FPC is fragile — add strain relief in the enclosure.

**Base:** separate weighted puck, USB-C + protection board inside, 2 pogo receptacles mate the device's
spring contacts, magnets/friction ribs seat it at 15–25° tilt. Charges when seated, runs on battery when
lifted. Rubber foot ring.

---

## 10. Bill of Materials — with links

### 10A. Prototype (Stage 2 — RPi Zero 2W + eval display)

| # | Component | Part / source | Qty | Unit £ | Link |
|---|---|---|---|---|---|
| 1 | 2.8" round LCD eval module | ER-TFT028-2-6318 (BuyDisplay) | 1 | ~£22 | [link](https://www.buydisplay.com/round-2-8-inch-480x480-tft-module-spi-i2c-opt-capacitive-touch-arduino-shield) |
| 2 | Raspberry Pi Zero 2W | Pimoroni | 1 | ~£15 | pimoroni.com |
| 3 | LiPo 1200–2000 mAh | Adafruit #258 / #2011 | 1 | £5–8 | [link](https://www.adafruit.com/product/2011) |
| 4 | USB-C charger module | TP4056 (AliExpress) | 1 | ~£2 | — |
| 5 | Accelerometer breakout | MPU-6050 (proto) | 1 | ~£2 | — |
| 6 | Ambient light breakout | BH1750 / VEML7700 | 1 | £1–4 | [VEML7700 #4162](https://www.adafruit.com/product/4162) |
| 7 | I²S mic breakout | ICS-43434 (Adafruit #6049) | 1 | ~£6 | [link](https://www.mouser.com/ProductDetail/Adafruit/6049?qs=olJun0bQHM88XeFsw90dVw%3D%3D) |
| 8 | I²S amp + speaker | MAX98357A #3006 + 8 Ω | 1 | ~£7 | [link](https://www.adafruit.com/product/3006) |
| 9 | Wiring / headers / FPC | AliExpress | — | ~£3 | — |
| 10 | 3D-printed enclosure | PETG filament | — | £5–10 | — |
| 11 | Misc (R/standoffs/tape) | — | — | ~£3 | — |
| | **Prototype total** | | | **~£71–90** | |

### 10B. Production V1 (ESP32-S3, custom PCB) — key actives

| Component | Part | ~£ @100 | Link |
|---|---|---|---|
| MCU module | ESP32-S3-WROOM-1-N16R8 | 4–5 | [DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-WROOM-1-N8R8/15295891) |
| Round LCD (bare ST7701S) | TSLCD TST028WVBS-33 / GL Electronics | 5–8 | [TSLCD](https://www.tslcd.com/tsd-ips-2-8-inch-round-480x480-resolution-300-nits-spi-rgb-interface-tft-lcd-display-module_p763.html) |
| Touch controller | CST816S | 0.6 | — |
| Charger + power-path | BQ24074RGTR | 1.50 | [Mouser](https://www.mouser.com/ProductDetail/Texas-Instruments/BQ24074RGTR?qs=ZV%2Fxhq4oszp2Nll7fIx5wg%3D%3D) |
| 3.3 V buck + 2.2 µH | TPS62840DLCR | 0.70 | [Mouser](https://www.mouser.com/ProductDetail/Texas-Instruments/TPS62840DLCR?qs=%2B6g0mu59x7L1%2Fxo1joT%2Bvg%3D%3D) |
| Fuel gauge | MAX17048 | 1.00 | [datasheet](https://www.mouser.com/datasheet/2/609/MAX17048_MAX17049-3126952.pdf) |
| Accelerometer | LIS2DW12 | 0.80 | ST |
| Ambient light | VEML7700 | 0.50 | [Vishay](https://www.vishay.com/docs/84286/veml7700.pdf) |
| I²S mic | ICS-43434 | 1.20 | TDK |
| I²S amp | MAX98357A | 1.20 | Analog/Maxim |
| Speaker 8 Ω | generic 20–28 mm | 1.50 | — |
| USB-C recept. (base) | JAE DX07S016JA1R1500 | 1.70 | [DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-WROOM-1U-N8R8/16162638) |
| Custom 2-layer PCB | JLCPCB/PCBWay | 2–4 | jlcpcb.com |
| Passives/FPC/pogo/JST | LCSC | ~3 | lcsc.com |

> Production BOM target: **~£25–33** at volume (sub-£18 was the original aspiration; the audio + power-path
> + fuel-gauge additions push it up — decide those explicitly). Retail target **£79–£99**.

---

## 11. Power Budget (LCD reality)

| State | Draw |
|---|---|
| Deep sleep (backlight off, frame held, ESP32 ~10 µA + buck 60 nA + gauge 3 µA + IMU ~1 µA + touch LP ~3 µA) | **~20 µA** |
| Idle, backlight ~35 % | ~40–70 mA |
| Active, full backlight + WiFi | ~150–250 mA (WiFi TX peaks ~500 mA) |
| Voice reply (mic + amp + WiFi) | ~200–350 mA |

The dominant battery variable is **backlight on-time**, not compute. Aggressive auto-dim + deep sleep on
idle is what gets you to the 8–16 h active / 2–3 day standby figures. **Measure real draw on the first
hardware** — backlight current varies by panel batch.

---

## 12. Risks & Procurement Notes

| Risk | Mitigation |
|---|---|
| Eval module ≠ production panel (LT7683/GT911 vs ST7701S/CST816S) | Build a clean display HAL; validate logic on eval, expect driver rework for the bare panel |
| 0.5 mm FPC fragility | Strain relief in enclosure; handle with care; confirm exact pitch before PCB |
| Touch controller variant / I²C address | Confirm GT911 vs CST816 on the actual panel before driver work |
| LCD glare | Anti-glare coating on window; confirm with supplier |
| LCD backlight battery draw | Auto-dim + deep sleep; measure real draw early |
| Octal-PSRAM pins (GPIO26–37) | Never route them; respected in the PCB pin map |
| TPS62840 layout sensitivity | Follow datasheet layout figure exactly |
| ESP32-S3 supply intermittency | Identify a second authorised distributor pre-production |
| Heat near battery | ESP32 + buck on opposite side from LiPo |

---

## 13. Development Phases

1. **Breadboard** — RPi Zero 2W + ER-TFT028 eval display: get rendering, touch, WiFi sync working.
2. **Housed prototype** — same electronics, 3D-printed enclosure v1, battery + charging, IMU + ALS.
3. **ESP32 migration** — port firmware RPi→ESP32-S3 (MicroPython or C++/ESP-IDF); validate power draw, deep sleep; move to bare ST7701S panel + CST816S.
4. **V1 hardware** — custom 2-layer PCB (KiCad 8), all sensors, USB-C base, clean routing. Order ~5 boards (JLCPCB/PCBWay), expect one respin.
5. **Display revisit (future)** — swap driver layer to round e-ink when a volume source exists; HAL unchanged.

---

## 14. Source Index

Display: [BuyDisplay ER-TFT028](https://www.buydisplay.com/round-2-8-inch-480x480-tft-module-spi-i2c-opt-capacitive-touch-arduino-shield) · [TSLCD bare panel](https://www.tslcd.com/tsd-ips-2-8-inch-round-480x480-resolution-300-nits-spi-rgb-interface-tft-lcd-display-module_p763.html) · [GL Electronics](https://lcdscreenmfg.com/product/2-8inch-round-ips-tft-lcd-display-480480-rgb-interface-st7701s-2-76-lcd-screen/)
Compute: [Espressif WROOM-1U](https://www.espressif.com/en/module/esp32-s3-wroom-1u-en) · [DigiKey](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-WROOM-1-N8R8/15295891)
Power: [TPS62840 (TI)](https://www.ti.com/product/TPS62840) · [BQ24074 (Mouser)](https://www.mouser.com/ProductDetail/Texas-Instruments/BQ24074RGTR?qs=ZV%2Fxhq4oszp2Nll7fIx5wg%3D%3D) · [MAX17048 datasheet](https://www.mouser.com/datasheet/2/609/MAX17048_MAX17049-3126952.pdf)
Sensors/Audio: [VEML7700 (Vishay)](https://www.vishay.com/docs/84286/veml7700.pdf) · [LIS2DW12 (ST)](https://community.st.com/t5/mems-sensors/lis2dw12-accelerometers-i2c-address-and-read-data/td-p/200812) · [ICS-43434 (Adafruit)](https://www.mouser.com/ProductDetail/Adafruit/6049?qs=olJun0bQHM88XeFsw90dVw%3D%3D) · [MAX98357A (Adafruit)](https://www.adafruit.com/product/3006)

*Prices are single-unit / low-qty planning figures (mid-2026) and will vary by region, tariff, and
quantity. Confirm against the live supplier page before ordering, and confirm FPC pitch + touch variant
against the physical panel before PCB layout.*
