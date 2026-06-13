# HARDWARE — GRAVITY

---

## Physical Form Factor

### Reference Object
The closest existing product to Gravity's physical size and presence is the Apple HomePod Mini.

| Apple HomePod Mini | Gravity Target |
|---|---|
| 97mm diameter | ~90–100mm diameter |
| 84mm tall | ~80–95mm tall |
| Spherical / fabric wrapped | Circular front face, plastic body |
| Sits flat, no directionality | Directional — angled front face toward user |
| ~45mm display cutout | 71mm display viewing area (2.8" round LCD) |

Gravity is approximately the same footprint as a HomePod Mini — slightly larger to accommodate the display cutout and bezel. It is not a perfect sphere — it has a defined front (display face) and back (grip surface). The display is slightly larger than the HomePod Mini's top face, which is intentional — it is the product's identity.

---

## Display — Confirmed Spec

**Selected display: 2.8" Round IPS LCD — ST7701S driver**

This is the confirmed display for both prototype and v1 production. E-ink remains the long-term product vision but round e-ink supply is fragile and limited to one primary source (Waveshare). The ST7701S round LCD delivers the same aesthetic through software rendering — paper-coloured background, ink-black elements, 1-bit visual language — with better supply chain stability, lower BOM cost at volume, and instant partial refresh.

| Property | Spec |
|---|---|
| Display type | Round IPS TFT LCD — colour, backlit |
| Driver IC | ST7701S |
| Shape | Circular |
| Viewing area diameter | 71mm (2.8 inches) |
| Resolution | 480 × 480 pixels |
| Pixel density | ~241 PPI |
| Colour depth | 16-bit (65K colours) — rendered in 1-bit palette by software |
| Interface | SPI + RGB (SPI used for prototype, RGB for production) |
| Touch | Capacitive touch layer integrated — GT911 or CST816 controller |
| Viewing angle | 178° all directions (IPS) |
| Brightness | 300–500 nits depending on supplier variant |
| Refresh | Instant — no e-ink flash delay |
| Operating voltage | 3.3V |
| Backlight | LED, dimmable via PWM |

### Display Aesthetic Strategy
The LCD renders the same visual language as the e-ink designs:
- Background: `#F4F2EA` (warm paper white) — not pure white
- Foreground: `#14130D` (near-black ink) — not pure black
- No colour used in v1 UI — strict 1-bit palette enforced in software
- Backlight dimmed to ~30–40% in ambient/idle mode — reduces glare, mimics e-ink flatness
- Night mode: backlight to ~5–10%, warm tint filter applied
- The paper-on-black rendering in a dark room matches e-ink presence closely

### Future Display Path
When a reliable 2.8"–3.0" round e-ink source becomes available at production volumes the driver layer swaps. The entire rendering stack above it is unchanged. This is why the display abstraction layer (HAL) must be built correctly from day one.

### Supplier Notes (To Be Finalised)
- **Prototype source:** BuyDisplay.com (ER-TFT028 series), Makerfabs, or AliExpress single units ~£15–20
- **Production source (TBD):** Shenzhen Chance Technology / Lianxun Optronics — MOQ 50–100 units, ~£5–8 each at 100 units, ~£3–5 at 1,000 units
- Confirm exact FPC connector pitch (0.5mm standard) before PCB design
- Confirm touch controller variant before writing firmware touch driver

---

## Enclosure — Updated for 2.8" Display

### Revised Dimensions
The enclosure has been revised down from the original e-ink spec to match the 2.8" LCD form factor.

| Dimension | Value |
|---|---|
| Total diameter | 90–100mm |
| Total depth (front to back) | 40–50mm |
| Display cutout diameter | 72–74mm (matches 71mm viewing area + 1–2mm bezel ring) |
| Bezel width (display edge to enclosure edge) | 9–13mm all around |
| Base footprint | ~100mm diameter |
| Base height | ~18mm |
| Total height (device in base) | ~95–110mm |
| Weight (device only) | <180g |
| Weight (with base) | <250g |

### Material
- Primary: ABS or PETG plastic (3D printed for prototype, injection moulded for v1)
- Finish: Matte soft-touch coating — not glossy
- Colour: Single colour for v1 — **matte black** (space/terminal aesthetic)
- Future: Consider light grey or off-white variant

### Construction
- Two-piece shell: front face (display side) + back shell
- Front face has circular cutout for display — bezel is part of the front face piece
- Back shell is convex — smooth, ergonomic
- The two pieces clip or screw together — designed for repairability
- Base is a separate third piece — houses USB-C port and angled stand
- Display glass sits flush with or slightly recessed from the front face bezel — no proud edges

### Stand / Base
- The device sits in a small circular base
- The base angles the device at approximately **15–25 degrees** from vertical
- Tilted back so the display faces upward toward the user's eyeline at desk or bedside
- The angle is fixed — not adjustable in v1
- Base contains USB-C port and power management circuitry
- Device seats into base magnetically or friction-fit — lifts out cleanly for holding

---

## Directionality & Orientation

Gravity is not an omnidirectional object. It has a front and a back. It faces the user.

- The display always knows which way is "up" via an onboard accelerometer
- If the device is picked up and held, the UI rotates to match orientation
- When set back in the base, it returns to desk/table display mode automatically

---

## Touch Interface

Touch is the primary physical interaction method.

- Capacitive touch layer integrated into the display module (GT911 or CST816 controller)
- Supports: **tap, double-tap, swipe (left/right/up/down), long press**
- Does NOT need to support multi-touch in v1 — single touch point is sufficient
- Touch zones map to the circular UI:
  - **Centre tap:** confirm / select / acknowledge
  - **Swipe left/right:** navigate between screens
  - **Swipe up:** surface goal detail / expand
  - **Swipe down:** dismiss nudge / snooze
  - **Long press:** enter settings / call up AI check-in

### Touch on LCD vs E-Ink
LCD touch response is instant — no refresh delay to design around. However:
- Touch feedback animations must still be minimal — the product aesthetic is calm, not reactive
- Swipe transitions use a simple state swap, not a slide animation — preserves the e-ink feel
- If/when migrating to e-ink, the touch zone logic is unchanged — only the feedback timing changes

---

## Back of Device — Grip & Comfort

- Back surface is a smooth convex curve — no sharp edges, no protrusions
- Material: matte soft-touch plastic (similar to Kindle Paperwhite back)
- The curvature fits naturally into a cupped palm
- Diameter at widest point (~90–100mm) sits comfortably across an average adult hand
- Weight target: **under 180g**
- No buttons on the back — all interaction via front touch surface
- Single USB-C port on the base unit, not the device body — clean back surface

---

## Power & Battery

Gravity is **primarily a plugin device** — lives in its base, plugged in. Battery is for portability.

| Property | Spec |
|---|---|
| Primary power | USB-C, 5V via base |
| Battery | 1000–1500mAh LiPo |
| Estimated battery life (LCD) | 8–16 hours active, 2–3 days standby with backlight off |
| Charge time | ~1.5 hours via USB-C |
| Battery indicator | Shown on display — one persistent glyph in corner |
| Low battery behaviour | Dims backlight to minimum, sends notification to companion app |

### Power Architecture
- When plugged in: full brightness, full refresh rate, all features active
- On battery: backlight dims to 10–15%, refresh rate reduces, WiFi sync interval increases
- Deep sleep mode: backlight off, display holds last frame, wakes on touch or RTC timer
- Note: LCD requires backlight power to show content — unlike e-ink which holds image at zero power. This is the primary battery life difference between LCD and e-ink for this use case.

---

## Processor & Compute

### Prototype: Raspberry Pi Zero 2W
- Used for Stage 2 prototype only
- Runs full Linux — easy Python development, fast iteration
- WiFi built in
- Drives ST7701S display via SPI
- Downside: higher power draw, longer boot, physically larger than needed

### Production Target: ESP32-S3
- Dual-core 240MHz, 512KB SRAM, supports external PSRAM
- WiFi 802.11 b/g/n + Bluetooth 5.0 built in
- Ultra low power deep sleep (~10µA)
- Drives ST7701S display via SPI/RGB
- Runs MicroPython or C++ firmware
- Physically small — fits comfortably inside enclosure with room for battery

### Memory
| Type | Size |
|---|---|
| Flash (program storage) | 16MB |
| PSRAM (runtime) | 8MB |
| SD card slot (optional) | Future firmware expansion |

---

## Connectivity

| Protocol | Purpose |
|---|---|
| WiFi 802.11 b/g/n | Primary data — syncs with backend, receives nudges, pushes logs |
| Bluetooth 5.0 | Companion app pairing, proximity detection |
| USB-C (base) | Power only in v1 — not data |

### Offline Behaviour
- Device caches today's schedule, non-negotiables, and current goal state locally
- If WiFi drops, device continues to display and accept touch input
- Syncs when connection restored
- All AI processing happens in the cloud — device is a display terminal, not a compute node

---

## Sensors

| Sensor | Purpose | Phase |
|---|---|---|
| Accelerometer (IMU) | Orientation detection — desk mode vs held mode | Phase 1 |
| Ambient light sensor | Auto-dim backlight based on room light level | Phase 1 |
| MEMS Microphone | Voice onboarding, check-ins, ambient sound detection | Phase 2 |
| Camera (small, low-res) | Presence detection — is user at desk? | Phase 3 / TBD |
| Temperature sensor | Passive environmental data — sleep quality correlation | Phase 2 |

---

## Prototype Bill of Materials (BOM) — Updated

| Component | Source | Est. Cost |
|---|---|---|
| 2.8" Round IPS LCD — ST7701S, 480×480, capacitive touch | BuyDisplay / AliExpress | £15–20 |
| Raspberry Pi Zero 2W | Pimoroni | £15 |
| LiPo battery 1000–1500mAh | Adafruit / AliExpress | £5–8 |
| USB-C charging + protection module (TP4056) | AliExpress | £2 |
| Accelerometer (MPU-6050 breakout) | AliExpress | £2 |
| Ambient light sensor (BH1750 breakout) | AliExpress | £1 |
| SPI/FPC wiring, headers, connectors | AliExpress | £3 |
| 3D printed enclosure (PLA/PETG filament) | Local print / filament | £5–10 |
| Misc (resistors, standoffs, thermal tape) | — | £3 |
| **Total** | | **~£51–64** |

Target production BOM (ESP32-S3 + injection moulded + ST7701S at volume): **sub-£18**
Target retail price: **£79–£99**

---

## Hardware Constraints & Known Challenges

| Challenge | Notes |
|---|---|
| LCD backlight battery draw | Primary battery life constraint vs e-ink. Mitigated by aggressive auto-dim and deep sleep. Measure real draw early with actual hardware. |
| ST7701S FPC connector fragility | 0.5mm pitch FPC is delicate — handle carefully during prototyping, add strain relief in enclosure design |
| Display glass flush mount | Getting the display flush with the bezel requires precise enclosure tolerancing — design cutout 0.2–0.3mm larger than display diameter |
| Touch controller firmware | GT911 and CST816 have different I2C address defaults — confirm variant before writing driver |
| Ambient glare on LCD | LCD has surface reflections unlike e-ink. Matte anti-glare coating on display glass is recommended — confirm with supplier |
| Heat from processor near battery | Keep RPi/ESP32 physically away from battery in enclosure — thermal tape on processor |
| WiFi power draw during sync | On battery, limit sync frequency — configurable in firmware |
| Enclosure tolerancing for round display | Round cutout must be machined or printed precisely — test fit with physical display before finalising enclosure design |

---

## Hardware Development Phases

### Phase 1 — Breadboard Prototype
- RPi Zero 2W + 2.8" round ST7701S LCD on breadboard
- No enclosure
- Powered via USB
- Goal: get display rendering, touch input, and WiFi sync working

### Phase 2 — Housed Prototype
- Same electronics, 3D printed enclosure v1
- Integrated battery + charging
- Accelerometer + ambient light sensor added
- Goal: validate form factor, ergonomics, hold feel, desk presence

### Phase 3 — ESP32 Migration
- Port firmware from RPi (Python) to ESP32-S3 (MicroPython or C++)
- Validate power draw, battery life, deep sleep behaviour
- Goal: confirm production chip works end-to-end

### Phase 4 — V1 Hardware
- Refined 3D printed or small-run injection moulded enclosure
- All sensors integrated
- USB-C in base, clean cable routing
- Goal: shippable prototype quality unit

### Phase 5 — Display Revisit (Future)
- If a reliable 2.8"–3.0" round e-ink source becomes available at production volumes
- Swap driver layer only — entire rendering stack above it unchanged
- Evaluate based on supply chain stability, unit cost at volume, and battery life improvement