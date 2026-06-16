/* GRAVITY V1 — hardware breakdown data
   All component facts sourced from GRAVITY_V1_FULL_BUILD_SPEC.md + GRAVITY_V1_PCB_DESIGN.md
   Geometry is a schematic side cross-section: front (display) face points LEFT, back shell RIGHT.
   ViewBox is 1280 x 880. Device body occupies the centre; wide margins L/R hold leader labels. */

window.GEO = {
  vb: { w: 1280, h: 880 },
  // device side-section envelope (front flat at left, convex back at right)
  dev: { frontX: 462, backApex: 752, top: 158, bot: 690, cy: 424 },
  // front -> back depth bands (x positions in user units)
  band: {
    overlay:   [462, 476],   // capacitive touch overlay + bezel face
    panel:     [476, 496],   // round e-ink panel
    gap:       [496, 516],   // air gap / FPC fold
    compFace:  [516, 540],   // ICs mounted on display-side face of board
    board:     [540, 547],   // device PCB
    cavity:    [547, 656],   // battery cavity
    backAir:   [656, 726],   // structural air
    backWall:  [726, 752],   // convex back shell wall
  },
  // base puck below device
  base: { top: 706, bot: 838, left: 470, right: 712 },
  // label columns
  label: { leftX: 308, rightX: 974, topY: 176, botY: 700 },
};

// Spec masthead chips
window.SPEC_META = [
  { k: "COMPUTE", v: "ESP32-S3-WROOM-1" },
  { k: "DIAMETER", v: "110–120 mm" },
  { k: "DEPTH", v: "45–55 mm" },
  { k: "MASS", v: "< 200 g" },
  { k: "DISPLAY", v: "2.8″ LCD · TFT" },
  { k: "BATTERY", v: "1500 mAh LiPo" },
];

/* Each layer: id, idx, code, title, blurb, accent depth (mm) for the cut plane,
   and components[] with: name, mpn (optional), fn, bus (optional), tag (optional badge),
   anchor [x,y] on the section, side 'L'|'R'. */
window.GRAVITY_LAYERS = [
  {
    code: "00", title: "EXTERIOR", depthMm: 0,
    blurb: "What the customer sees. A circular matte-black calm-display object that sits in a small angled base — or free-stands on its own flip-out backstand. No visible electronics, no loose wires. Everything case-side is 3D-printed (PETG) for the demo.",
    components: [
      { name: "Front shell + bezel", fn: "ABS / PETG, matte-black soft-touch · ~22 mm bezel around the 2.8″ LCD", anchor: [470, 250], side: "L" },
      { name: "Display face", fn: "2.8″ round LCD (TFT) · backlit · ~Ø71 mm active", tag: "GLANCE", anchor: [464, 410], side: "L" },
      { name: "Back shell", fn: "Convex soft-touch, cupped-palm · no buttons, no ports", anchor: [742, 360], side: "R" },
      { name: "Flip-out backstand", fn: "Recessed kickstand moulded into the back shell · pop out with a fingernail to free-stand the device at ~18° when it is off the base", tag: "NEW", anchor: [728, 576], side: "R" },
      { name: "Shell fasteners", fn: "M2 brass threaded inserts + screws · front/back clip-screw, no glue — battery stays replaceable", anchor: [700, 250], side: "R" },
      { name: "Angled base", fn: "Separate weighted puck · tilts device 15–25°", anchor: [560, 770], side: "L" },
      { name: "USB-C", fn: "Power-only in V1 · lives in the base", tag: "5 V", anchor: [690, 792], side: "R" },
    ],
  },
  {
    code: "01", title: "DISPLAY ASSEMBLY", depthMm: 4,
    blurb: "The front shell lifts away. A 2.8″ round LCD (TFT) bonded into the bezel with its LED backlight, a capacitive overlay laminated over it, FPC ribbons folding back to the board.",
    components: [
      { name: "Capacitive touch overlay", fn: "Circular sensor film, laminated over active area", tag: "RISK", anchor: [469, 232], side: "L" },
      { name: "2.8″ round LCD (TFT)", mpn: "SPI TFT · ST77xx / GC9A01-class", fn: "Backlit colour TFT, round-masked · ~Ø71 mm active · rendered in calm B/W", bus: "SPI", anchor: [486, 410], side: "L" },
      { name: "LCD backlight + driver", fn: "White-LED backlight · PWM brightness via constant-current driver · dims to ambient (ALS)", tag: "NEW", anchor: [486, 300], side: "L" },
      { name: "LCD FPC", mpn: "≈ 0.5 mm pitch", fn: "Panel ribbon → board J1 (SPI + backlight)", anchor: [496, 196], side: "L" },
      { name: "Touch FPC", fn: "Overlay sensor film → board J2", bus: "I²C", anchor: [496, 624], side: "R" },
      { name: "ALS light-pipe", fn: "Bezel aperture feeds the VEML7700 room light", anchor: [466, 588], side: "R" },
      { name: "Optical / VHB bond", fn: "Panel bonded into bezel cutout", anchor: [474, 318], side: "L" },
    ],
  },
  {
    code: "02", title: "MAIN PCB + SENSORS", depthMm: 18,
    blurb: "The circular 2-layer board on standoffs behind the display. The S3 module at the board edge, antenna overhanging plastic-only keep-out. One I²C bus, one SPI bus, one shared I²S clock pair.",
    components: [
      { name: "ESP32-S3-WROOM-1", mpn: "ESP32-S3-WROOM-1-N16R8", fn: "240 MHz dual-core · WiFi b/g/n + BLE 5.0 · 16 MB flash / 8 MB PSRAM", tag: "MCU", anchor: [524, 214], side: "L" },
      { name: "Touch controller", mpn: "CST816S", fn: "Single-touch + HW gestures · wake-on-touch", bus: "I²C 0x15", anchor: [524, 286], side: "L" },
      { name: "Accelerometer / IMU", mpn: "LIS2DW12", fn: "3-axis · ~1 µA · 6D orient + wake-on-pickup", bus: "I²C 0x18", anchor: [524, 350], side: "R" },
      { name: "Ambient light sensor", mpn: "VEML7700", fn: "Adapts contrast / future frontlight", bus: "I²C 0x10", anchor: [524, 410], side: "R" },
      { name: "I²S MEMS microphone", mpn: "ICS-43434", fn: "Voice + wake-word on-device · acoustic port", bus: "I²S", anchor: [524, 472], side: "R" },
      { name: "I²S class-D amp", mpn: "MAX98357A", fn: "Mono ~3 W · spoken replies + rewards", bus: "I²S", anchor: [524, 534], side: "R" },
      { name: "Speaker", fn: "8 Ω · 20–28 mm · behind acoustic-mesh grille", anchor: [520, 612], side: "R" },
      { name: "FPC connectors J1 / J2", fn: "E-ink + touch ribbons at board edge", anchor: [512, 656], side: "L" },
      { name: "Programming header", mpn: "6-pad / Tag-Connect", fn: "USB-UART + 2-transistor auto-reset", anchor: [528, 244], side: "L" },
      { name: "microSD slot", fn: "Push-push, shared SPI · firmware expansion", tag: "DNP", anchor: [532, 588], side: "L" },
      { name: "BOOT / RESET buttons", fn: "Tact buttons + test pads · GPIO0 (BOOT) + EN (RESET) · recovery / flashing", anchor: [528, 264], side: "L" },
      { name: "Temperature sensor", mpn: "TMP117", fn: "±0.1 °C · placed away from MCU + buck to read room temp", bus: "I²C 0x48", tag: "DNP · P2", anchor: [556, 504], side: "R" },
      { name: "Presence / ToF aperture", fn: "Blanked bezel aperture for a future low-pin I²C ToF presence sensor", tag: "P3 · DNP", anchor: [466, 336], side: "R" },
      { name: "Device PCB", fn: "Circular 2-layer · Ø75–85 mm · 1.0 mm", anchor: [543, 410], side: "R" },
    ],
  },
  {
    code: "03", title: "POWER CORE", depthMm: 34,
    blurb: "The parts that make a long idle life real. A power-path charger so the cell never micro-cycles on the desk, a 60 nA buck so deep sleep costs ~20 µA, a fuel gauge so the battery glyph is real. The backlit LCD is the main active draw — it sleeps on inactivity and wakes on touch / pick-up.",
    components: [
      { name: "LiPo battery", mpn: "1500 mAh · JST-SH", fn: "Far side of the board from the S3 (thermal)", anchor: [600, 410], side: "R" },
      { name: "Charger + power-path", mpn: "BQ24074", fn: "Runs from USB while charging · ~750 mA · STAT→GPIO", anchor: [524, 318], side: "L" },
      { name: "3.3 V buck", mpn: "TPS62840 + 2.2 µH", fn: "60 nA quiescent · 750 mA · >90% under load · keeps deep-sleep idle tiny", tag: "60 nA", anchor: [524, 558], side: "L" },
      { name: "Fuel gauge", mpn: "MAX17048", fn: "ModelGauge · real state-of-charge %", bus: "I²C 0x36", anchor: [524, 494], side: "L" },
      { name: "Pogo contacts ×2", fn: "VBUS + GND · ~1 A · on board back, mate to base", anchor: [556, 680], side: "R" },
    ],
  },
  {
    code: "04", title: "BASE", depthMm: 55,
    blurb: "A separate weighted puck. Only VBUS + GND cross the lift-out joint via two spring contacts — the device runs on battery when lifted, charges when seated at a 15–25° tilt.",
    components: [
      { name: "USB-C receptacle", fn: "Power in · 5.1 kΩ CC1/CC2 pulldowns (5 V sink)", tag: "5 V", anchor: [688, 760], side: "R" },
      { name: "Base PCB", fn: "Small 2-layer input board", anchor: [600, 748], side: "R" },
      { name: "TVS array + PTC fuse", fn: "ESD / surge protection · ~1 A resettable", anchor: [636, 792], side: "R" },
      { name: "Pogo receptacles ×2", fn: "Mate to the device's spring contacts when seated", anchor: [546, 716], side: "L" },
      { name: "Magnets / friction ribs", fn: "Seat + hold the device at 15–25° tilt", anchor: [496, 738], side: "L" },
      { name: "Weighted floor", fn: "Stability ballast + rubber foot ring", anchor: [560, 824], side: "L" },
    ],
  },
];
