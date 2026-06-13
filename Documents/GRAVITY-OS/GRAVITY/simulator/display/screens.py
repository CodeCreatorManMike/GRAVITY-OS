"""screens.py — Direction A/B/C screen renders, ported from gravity-build.js"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from simulator.display.primitives import (
    new_canvas, apply_circle_mask, C, INK, PAPER, P,
    ring, arc, ticks, T, dot, sq, arc_sq,
    brackets, scan, moon, star, top_label, bot_label, prog_arc,
)

# ── shared test data ───────────────────────────────────────────────────────────
STREAK14 = [1,1,0,1,1,1,1,1,1,1,1,1,1,1]
WEEK = [
    [1,0,1,1,1,1,1], [1,1,0,1,1,0,1], [0,1,1,1,1,1,1],
    [1,1,1,0,1,1,1], [1,1,1,1,0,1,1],
]

# ══════════════════════════════════════════════════════════════════════════════
# DIRECTION A — TERMINAL (JetBrains Mono)
# ══════════════════════════════════════════════════════════════════════════════

def A1(time="09:14", date="FRI 13 JUN 2026", streak=47):
    img, d = new_canvas()
    ticks(d, 176, 60, 5, 4, 9)
    top_label(img, d, "GRAVITY OS · SYS OK", font_size=9, weight="Bold", letter_spacing=4, r=159)
    # Clock: s=72 matches JS; y tuned so baseline sits at visual centre mass
    T(d, C, 170, time, s=72, w=600, a="middle", ls=-1)
    T(d, C, 206, date, s=13, w=400, a="middle", ls=3)
    # 14-day streak ribbon — size=10 to be visible in PIL (JS renders 8 crisper)
    n, span_deg, r_sq = len(STREAK14), 86, 128
    for i in range(n):
        deg = 180 - span_deg/2 + i * (span_deg / (n - 1))
        arc_sq(d, r_sq, deg, 10, bool(STREAK14[i]))
    bot_label(img, d, f"{streak}-DAY STREAK", font_size=10, weight="Bold", letter_spacing=4, r=152)
    return apply_circle_mask(img)

def A2(task="Finish Q3 roadmap",
       nonneg=None,
       focus="> ship before noon. one block."):
    if nonneg is None:
        nonneg = ["[x] 16K LONG RUN", "[ ] 2L WATER", "[ ] LIGHTS OUT 22:30"]
    img, d = new_canvas()
    ticks(d, 176, 60, 15, 3, 8)
    top_label(img, d, "07:42 // MORNING BRIEF", font_size=9, weight="Bold", letter_spacing=2, r=159)
    brackets(d, 86, 72, 188, 46, k=9, sw=1.8)
    T(d, C, 90,  "TOP PRIORITY", s=9,  w=600, a="middle", ls=4)
    T(d, C, 110, task,           s=13, w=500, a="middle", ls=0)
    T(d, C, 148, "NON-NEGOTIABLES", s=9, w=600, a="middle", ls=3)
    for i, item in enumerate(nonneg[:3]):
        T(d, C, 173 + i * 21, item, s=13, w=400, a="middle", ls=0)
    bot_label(img, d, focus, font_size=9, weight="Medium", letter_spacing=1, r=152)
    return apply_circle_mask(img)

def A3(message="STAND", sub="UP.", alert="! MOVEMENT ALERT !",
       reason="YOU HAVEN'T MOVED", reason2="IN 4 HOURS.",
       dismiss="TAP SNOOZE · HOLD DISMISS"):
    img, d = new_canvas()
    ring(d, 176, sw=1.8, dash=(3, 4))
    ring(d, 170, sw=0.9, dash=(1.5, 5))
    def chev(cy, up):
        sign = 1 if up else -1
        pts = [(C-9, cy+sign*(-6)), (C, cy+sign*3), (C+9, cy+sign*(-6))]
        d.line([pts[0], pts[1]], fill=INK, width=2)
        d.line([pts[1], pts[2]], fill=INK, width=2)
    chev(40, True); chev(320, False)
    top_label(img, d, alert, font_size=10, weight="Bold", letter_spacing=3, r=159)
    T(d, C, 115, reason,  s=12, w=400, a="middle", ls=1)
    T(d, C, 133, reason2, s=12, w=400, a="middle", ls=1)
    T(d, C, 194, message, s=52, w=700, a="middle", ls=1)
    T(d, C, 237, sub,     s=52, w=700, a="middle", ls=1)
    bot_label(img, d, dismiss, font_size=9, weight="Medium", letter_spacing=1, r=152)
    return apply_circle_mask(img)

def A4(pct=0.62, label="HALF MARATHON", days_left=94):
    img, d = new_canvas()
    ticks(d, 176, 48, 4, 4, 8)
    end_deg = 360 * pct
    # Arc track + filled progress arc at r=160
    ring(d, 160, sw=1.0, dash=(1.5, 4))
    arc(d, 160, 0, end_deg, sw=5)
    ex, ey = P(160, end_deg)
    dot(d, ex, ey, 4.5, filled=True,  colour=PAPER)
    dot(d, ex, ey, 4.5, filled=False, sw=2.0)
    # Top label inside the arc ring (r=145) to avoid PIL raster collision at r=160
    top_label(img, d, "GOAL // 6 MONTHS", font_size=9, weight="Bold", letter_spacing=3, r=145)
    T(d, C, 153, f"{int(pct*100)}%", s=56, w=700, a="middle", ls=-1)
    T(d, C, 179, label,              s=12, w=500, a="middle", ls=2)
    T(d, C, 198, f"T-{days_left} DAYS", s=9, w=400, a="middle", ls=1)
    subtasks = [("[x] LONG RUN", "16/16K"), ("[~] STRENGTH", "2/3"), ("[ ] SLEEP 7H", "5/7")]
    lx, rx = C - 80, C + 80
    for i, (left, right) in enumerate(subtasks):
        y = 224 + i * 20
        T(d, lx, y, left,  s=10, w=400, a="start", ls=0)
        T(d, rx, y, right, s=10, w=500, a="end",   ls=0)
        scan(d, y - 3, r=78, dash=(1, 3), sw=0.8)
    return apply_circle_mask(img)

def A5():
    img, d = new_canvas()
    ticks(d, 176, 60, 30, 3, 7)
    top_label(img, d, "WEEK 24 // LAST 7 DAYS", font_size=9, weight="Bold", letter_spacing=2, r=159)
    days   = ['S','S','M','T','W','T','F']
    habits = ['MOVE','READ','FOCUS','SLEEP','CALM']
    cz, gap, cols, rows = 18, 6.5, 7, 5
    gw  = cols * cz + (cols - 1) * gap
    gh  = rows * cz + (rows - 1) * gap
    gx  = C - gw / 2 + 14
    gy  = 200 - gh / 2
    for c in range(cols):
        T(d, gx + c*(cz+gap) + cz/2, gy - 8, days[c], s=10, w=700 if c==6 else 400, a="middle", ls=0)
    tcx = gx + 6 * (cz + gap)
    brackets(d, tcx - 4, gy - 4.5, cz + 8, gh + 9, k=6, sw=1.8)
    for r_i in range(rows):
        ry = gy + r_i * (cz + gap)
        T(d, gx - 9, ry + cz/2 + 3, habits[r_i], s=9, w=500, a="end", ls=0)
        for c in range(cols):
            filled = bool(WEEK[r_i][c]) if r_i < len(WEEK) else False
            sq(d, gx + c * (cz + gap), ry, cz, filled)
    bot_label(img, d, "30 / 35 DONE · 86%", font_size=10, weight="Bold", letter_spacing=1, r=152)
    return apply_circle_mask(img)

def A6(time_remaining="24:18", task="Q3 roadmap deck", session="SESSION 02",
       dnd=True, pct_remaining=0.27):
    img, d = new_canvas()
    ticks(d, 176, 60, 5, 3, 8)
    end_deg = 360 * pct_remaining
    ring(d, 160, sw=1.0, dash=(1.5, 4))
    arc(d, 160, 0, end_deg, sw=5)
    ex, ey = P(160, end_deg)
    dot(d, ex, ey, 4.5, filled=True,  colour=PAPER)
    dot(d, ex, ey, 4.5, filled=False, sw=2.0)
    top_label(img, d, f"FOCUS // {session}", font_size=9, weight="Bold", letter_spacing=3, r=145)
    T(d, C, 163, time_remaining, s=52, w=600, a="middle", ls=-1)
    T(d, C, 189, "REMAINING",    s=9,  w=400, a="middle", ls=4)
    if dnd:
        d.rectangle([C-58, 201, C+58, 223], outline=INK, width=1)
        T(d, C, 217, "DND ACTIVE", s=9, w=600, a="middle", ls=2)
    T(d, C, 249, task, s=11, w=400, a="middle", ls=0)
    bot_label(img, d, "TAP PAUSE · HOLD END", font_size=9, weight="Medium", letter_spacing=1, r=152)
    return apply_circle_mask(img)

def A7(lights_out="00:00", in_min=22, alarm="06:30", sleep_h=8, sleep_m=22,
       tomorrow="16K LONG RUN"):
    img, d = new_canvas()
    ticks(d, 176, 60, 30, 3, 6)
    top_label(img, d, "22:08 // WIND DOWN", font_size=9, weight="Bold", letter_spacing=3, r=159)
    moon(d, C, 86, 16, sw=2.0)
    star(d, C-30, 74, r=2.4); star(d, C+28, 92, r=2.0); star(d, C+36, 66, r=1.8)
    T(d, C, 150, "LIGHTS OUT",        s=11, w=500, a="middle", ls=3)
    T(d, C, 183, f"IN {in_min} MIN",  s=30, w=700, a="middle", ls=1)
    scan(d, 202, r=120, dash=(1.5, 4), sw=1.0)
    T(d, C, 222, f"ALARM {alarm} · {sleep_h}H {sleep_m}M", s=10, w=400, a="middle", ls=1)
    T(d, C, 248, "[x] SCREENS DOWN", s=10, w=400, a="middle", ls=0)
    T(d, C, 267, "[ ] STRETCH",      s=10, w=400, a="middle", ls=0)
    bot_label(img, d, f"TOMORROW · {tomorrow}", font_size=9, weight="Medium", letter_spacing=1, r=152)
    return apply_circle_mask(img)


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTION B — ORBITAL (Space Grotesk, falls back to JetBrains Mono)
# ══════════════════════════════════════════════════════════════════════════════
# Fonts: place SpaceGrotesk-Regular.ttf etc. in simulator/display/fonts/ to
# activate the intended rendering; JetBrainsMono is used as fallback.

_GEO = "SpaceGrotesk"   # family name for _font()

def B1(time="9:14", date="Friday 12 June", streak=47):
    img, d = new_canvas()
    ring(d, 176, sw=1.2)
    ring(d, 150, sw=1.0)
    ring(d, 118, sw=0.9, dash=(1, 5))
    # Cardinal marks
    for deg in [0, 90, 180, 270]:
        x1, y1 = P(176, deg); x2, y2 = P(168, deg)
        d.line([(x1,y1),(x2,y2)], fill=INK, width=2)
    # Day-progress arc: fraction of day elapsed
    frac = (9 + 14/60) / 24
    end_deg = 360 * frac
    arc(d, 150, 0, end_deg, sw=2.5)
    ring(d, 150, sw=1.0, dash=(1.5, 5))
    px, py = P(150, end_deg)
    dot(d, px, py, 4.5, filled=True)
    dot(d, px, py, 8.5, filled=False, sw=1.0)
    T(d, C, 182, time,   s=60, w=300, a="middle", ls=-1, family=_GEO)
    T(d, C, 212, date,   s=13, w=400, a="middle", ls=2,  family=_GEO)
    bot_label(img, d, f"{streak} DAY STREAK", font_size=10, weight="Regular", letter_spacing=4, r=134, family=_GEO)
    top_label(img, d, "GRAVITY", font_size=9, weight="Bold", letter_spacing=8, r=162, family=_GEO)
    return apply_circle_mask(img)

def B2(task="Finish the Q3 roadmap deck", nonneg=None, focus="One deep block before noon"):
    if nonneg is None:
        nonneg = ["16K long run", "2L water", "lights out 22:30"]
    img, d = new_canvas()
    ring(d, 176, sw=1.2, dash=(1, 4))
    ring(d, 150, sw=1.0)
    top_label(img, d, "MORNING · 07:42", font_size=9, weight="Bold", letter_spacing=5, r=159, family=_GEO)
    # Sunrise mark
    sy = 78
    d.line([(C-24, sy), (C+24, sy)], fill=INK, width=2)
    d.arc([C-13, sy-13, C+13, sy], start=0, end=180, fill=INK, width=2)
    T(d, C, 125, "TOP TODAY",    s=9,  w=600, a="middle", ls=5, family=_GEO)
    # Split long task into two lines if needed
    words = task.split(); mid = len(words)//2
    T(d, C, 152, " ".join(words[:mid]),  s=19, w=500, a="middle", family=_GEO)
    T(d, C, 176, " ".join(words[mid:]),  s=19, w=500, a="middle", family=_GEO)
    for i, item in enumerate(nonneg[:3]):
        cy = 208 + i * 22
        dot(d, C-74, cy-4, 3.3, filled=(i==0))
        T(d, C-62, cy, item, s=12, w=400, a="start", family=_GEO)
    bot_label(img, d, focus.upper(), font_size=9, weight="Regular", letter_spacing=2, r=152, family=_GEO)
    return apply_circle_mask(img)

def B4(pct=0.62, label="HALF MARATHON", days_left=94):
    img, d = new_canvas()
    rings = [(150, pct), (124, 0.70), (98, 0.71)]
    for r_val, p in rings:
        end = 360 * p
        ring(d, r_val, sw=1.0, dash=(1.5, 4))
        arc(d, r_val, 0, end, sw=3.5)
        ex, ey = P(r_val, end)
        dot(d, ex, ey, 3.6, filled=True,  colour=PAPER)
        dot(d, ex, ey, 3.6, filled=False, sw=1.8)
    T(d, C, 178, f"{int(pct*100)}%", s=44, w=500, a="middle", ls=-1, family=_GEO)
    T(d, C, 202, label,               s=10, w=600, a="middle", ls=3,  family=_GEO)
    T(d, C, 218, f"{days_left} days left", s=10, w=400, a="middle", ls=1, family=_GEO)
    for i, lbl in enumerate(["GOAL", "TRAIN", "SLEEP"]):
        T(d, C, 36 + i * 26, lbl, s=8, w=600, a="middle", ls=2, family=_GEO)
    return apply_circle_mask(img)

def B5():
    img, d = new_canvas()
    days   = ['S','S','M','T','W','T','F']
    habits = ['M','R','F','S','C']
    radii  = [50, 72, 94, 116, 138]
    for r_val in radii:
        ring(d, r_val, sw=0.9, dash=(1, 4))
    for c in range(7):
        deg = c * 360 / 7
        x1, y1 = P(38, deg); x2, y2 = P(146, deg)
        sw = 1.6 if c==6 else 0.8
        if c == 6:
            d.line([(x1,y1),(x2,y2)], fill=INK, width=2)
        else:
            # dashed spoke
            steps = 8
            for s in range(steps):
                t0 = s / steps; t1 = (s+0.5) / steps
                xa = x1 + (x2-x1)*t0; ya = y1 + (y2-y1)*t0
                xb = x1 + (x2-x1)*t1; yb = y1 + (y2-y1)*t1
                d.line([(xa,ya),(xb,yb)], fill=INK, width=1)
        lx, ly = P(163, deg)
        T(d, lx, ly+3, days[c], s=9, w=700 if c==6 else 400, a="middle", family=_GEO)
    for r_i, r_val in enumerate(radii):
        for c in range(7):
            x, y = P(r_val, c * 360 / 7)
            dot(d, x, y, 3.4, filled=bool(WEEK[r_i][c]))
    for i, lbl in enumerate(habits):
        T(d, C-11, C-radii[i]+3, lbl, s=8, w=600, a="end", family=_GEO)
    T(d, C, C-2, "WK", s=8, w=600, a="middle", family=_GEO)
    T(d, C, C+10, "24", s=9, w=500, a="middle", family=_GEO)
    return apply_circle_mask(img)

def B7(in_min=22, alarm="06:30", sleep_h=8, sleep_m=22):
    img, d = new_canvas()
    ring(d, 176, sw=1.2, dash=(1, 5))
    ring(d, 150, sw=1.0, dash=(1, 4))
    deg = 360 * 0.78
    arc(d, 150, 0, deg, sw=2.2, colour=INK)
    moon(d, C, C-6, 26, sw=2.0)
    stars = [(C-58,96),(C+62,108),(C+74,150),(C-72,150),(C+40,72),(C-44,210),(C+60,232)]
    for i, (sx, sy) in enumerate(stars):
        star(d, sx, sy, r=2.4 if i%2 else 1.8)
    T(d, C, 200, "Wind down", s=24, w=400, a="middle", family=_GEO)
    T(d, C, 224, f"{in_min} minutes to lights out", s=10, w=400, a="middle", ls=1, family=_GEO)
    top_label(img, d, "GOOD EVENING", font_size=9, weight="Bold", letter_spacing=6, r=159, family=_GEO)
    bot_label(img, d, f"ALARM {alarm} · {sleep_h}H {sleep_m}M", font_size=9, weight="Regular", letter_spacing=2, r=152, family=_GEO)
    return apply_circle_mask(img)


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTION C — MINIMAL TYPE (Sora, falls back to JetBrains Mono)
# ══════════════════════════════════════════════════════════════════════════════
# Fonts: place Sora-Regular.ttf etc. in simulator/display/fonts/ to activate.

_SORA = "Sora"

def C1(time="9:14", date="fri 12 jun", streak=47):
    img, d = new_canvas()
    # Single orientation tick at 12 o'clock
    d.line([(C, 22), (C, 32)], fill=INK, width=2)
    T(d, C, 192, time, s=86, w=300, a="middle", ls=-2, family=_SORA)
    T(d, C, 228, date, s=12, w=300, a="middle", ls=6,  family=_SORA)
    dot(d, C-13, 292, 2.3, filled=True)
    T(d, C+4, 297, str(streak), s=13, w=400, a="start", ls=2, family=_SORA)
    return apply_circle_mask(img)

def C2(task="Finish the Q3 roadmap deck.", nonneg=None, focus="One deep block before noon."):
    if nonneg is None:
        nonneg = "long run · 2L water · lights 22:30"
    img, d = new_canvas()
    T(d, C, 100, "TODAY", s=10, w=500, a="middle", ls=8, family=_SORA)
    words = task.split(); mid = len(words) // 2
    T(d, C, 150, " ".join(words[:mid]),  s=26, w=400, a="middle", ls=-0.3, family=_SORA)
    T(d, C, 181, " ".join(words[mid:]),  s=26, w=400, a="middle", ls=-0.3, family=_SORA)
    d.line([(C-26, 204), (C+26, 204)], fill=INK, width=1)
    T(d, C, 236, nonneg if isinstance(nonneg, str) else " · ".join(nonneg[:3]),
      s=10, w=300, a="middle", ls=1, family=_SORA)
    T(d, C, 264, focus, s=12, w=300, a="middle", family=_SORA)
    return apply_circle_mask(img)

def C4(pct=0.62, label="HALF MARATHON", days_left=94):
    img, d = new_canvas()
    # Single fine perimeter arc
    ring(d, 162, sw=0.8, dash=(1, 5))
    end_deg = 360 * pct
    arc(d, 162, 0, end_deg, sw=1.8)
    ex, ey = P(162, end_deg)
    dot(d, ex, ey, 2.6, filled=True)
    T(d, C, 122, label,             s=10, w=500, a="middle", ls=6, family=_SORA)
    T(d, C, 192, f"{int(pct*100)}%", s=76, w=300, a="middle", ls=-2, family=_SORA)
    T(d, C, 220, f"{days_left} days left", s=11, w=300, a="middle", ls=2, family=_SORA)
    T(d, C, 266, "long run ✓   strength 2/3   sleep 5/7", s=10, w=300, a="middle", ls=0.5, family=_SORA)
    return apply_circle_mask(img)

def C5():
    img, d = new_canvas()
    T(d, C, 64, "THIS WEEK", s=10, w=500, a="middle", ls=8, family=_SORA)
    days   = ['s','s','m','t','w','t','f']
    habits = ['move','read','focus','sleep','calm']
    gx0, gy0, dx, dy = 134, 120, 19, 20.5
    for c in range(7):
        T(d, gx0+c*dx, gy0-12, days[c], s=9, w=600 if c==6 else 300, a="middle", ls=1, family=_SORA)
    for r_i in range(5):
        T(d, gx0-26, gy0+r_i*dy+3, habits[r_i], s=9, w=300, a="end", ls=1, family=_SORA)
        for c in range(7):
            dot(d, gx0+c*dx, gy0+r_i*dy, 3.1, filled=bool(WEEK[r_i][c]))
    T(d, C, 300, "30 of 35 · 86%", s=11, w=300, a="middle", ls=2, family=_SORA)
    return apply_circle_mask(img)

def C7(in_min=22, lights_out="22:30"):
    img, d = new_canvas()
    moon(d, C, 122, 30, sw=1.8)
    star(d, C-46, 100, r=2.2); star(d, C+50, 134, r=1.8); star(d, C+40, 88, r=1.6)
    T(d, C, 218, "Wind down.", s=38, w=300, a="middle", ls=-1, family=_SORA)
    T(d, C, 254, f"lights out {lights_out}", s=11, w=300, a="middle", ls=2, family=_SORA)
    return apply_circle_mask(img)


# ══════════════════════════════════════════════════════════════════════════════
# Direction helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_direction(profile: dict | None) -> str:
    """
    Choose display direction from profile personality.
      direct/analytical → A (Terminal)
      creative/fluid    → C (Minimal)
      default           → B (Orbital)
    """
    if not profile:
        return "A"
    fp = profile.get("feedback_preference", "")
    fr = profile.get("failure_response", "")
    ps = profile.get("personality_summary", "").lower()
    if fp in ("direct", "factual") or fr in ("analyse", "rationalise"):
        return "A"
    if any(w in ps for w in ("creative", "fluid", "artist", "music", "expressive")):
        return "C"
    return "B"


# ══════════════════════════════════════════════════════════════════════════════
# Contact sheet (run directly)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from PIL import Image as _Img, ImageDraw as _IDraw
    from simulator.display.primitives import _font

    out = "/tmp/gravity_screens"
    os.makedirs(out, exist_ok=True)

    screens = [
        ("A1_ambient",    A1()),
        ("A2_morning",    A2()),
        ("A3_nudge",      A3()),
        ("A4_goal",       A4()),
        ("A5_heatmap",    A5()),
        ("A6_focus",      A6()),
        ("A7_winddown",   A7()),
        ("B1_ambient",    B1()),
        ("B2_morning",    B2()),
        ("B4_goal",       B4()),
        ("B5_heatmap",    B5()),
        ("B7_winddown",   B7()),
        ("C1_ambient",    C1()),
        ("C2_morning",    C2()),
        ("C4_goal",       C4()),
        ("C5_heatmap",    C5()),
        ("C7_winddown",   C7()),
    ]

    cols, PAD = 4, 20
    rows = (len(screens) + cols - 1) // cols
    W    = cols * 360 + (cols + 1) * PAD
    H    = rows * 360 + (rows + 1) * PAD + 60
    sheet   = _Img.new("RGB", (W, H), "#0b0b0d")
    sd      = _IDraw.Draw(sheet)
    lf      = _font(12, "Regular")

    for i, (name, img) in enumerate(screens):
        img.save(os.path.join(out, f"{name}.png"))
        col, row = i % cols, i // cols
        x = PAD + col * (360 + PAD)
        y = PAD + row * (360 + PAD)
        bezel = _Img.new("RGB", (360, 360), "#1a1a1e")
        bm    = _Img.new("L",   (360, 360), 0)
        _IDraw.Draw(bm).ellipse([0,0,359,359], fill=255)
        bezel.paste(img, (0, 0), mask=bm)
        sheet.paste(bezel, (x, y))
        sd.text((x + 180, y + 365), name.replace("_"," ").upper(), font=lf, fill="#5a5a60", anchor="mt")

    sheet.save(os.path.join(out, "_contact_sheet.png"))
    print("Done. Contact sheet at /tmp/gravity_screens/_contact_sheet.png")
    print("Open with: open /tmp/gravity_screens/_contact_sheet.png")
