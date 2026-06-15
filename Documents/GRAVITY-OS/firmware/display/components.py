# display/components.py — reusable drawing primitives
#
# All functions accept a DisplayHAL instance as first argument.
# Coordinates are in the 480×480 canvas space.
# All shapes respect the circular mask (r=230, centre=240,240) —
# pixels outside the circle are never touched; callers pass mask=True to enforce.

import math
from display.hal import COLOR_BG, COLOR_FG, WIDTH, HEIGHT

_CX = WIDTH  // 2   # 240
_CY = HEIGHT // 2   # 240
_MASK_R = 230       # max radius for content


# ── Circular mask helper ──────────────────────────────────────────────────────

def _in_circle(x, y, cx=_CX, cy=_CY, r=_MASK_R):
    dx = x - cx
    dy = y - cy
    return dx*dx + dy*dy <= r*r


def apply_circle_mask(hal, cx=_CX, cy=_CY, r=_MASK_R):
    """
    Paint all pixels outside the circle with COLOR_BG.
    Call once after rendering a full screen before hal.show().
    """
    for y in range(HEIGHT):
        dy = y - cy
        if abs(dy) > r:
            # Entire row outside circle
            hal.fill_rect(0, y, WIDTH, 1, COLOR_BG)
            continue
        # Find the x range inside the circle at this row
        dx = int(math.sqrt(r*r - dy*dy))
        x_left  = cx - dx
        x_right = cx + dx
        if x_left > 0:
            hal.fill_rect(0, y, x_left, 1, COLOR_BG)
        if x_right < WIDTH - 1:
            hal.fill_rect(x_right + 1, y, WIDTH - x_right - 1, 1, COLOR_BG)


# ── Arc / ring ────────────────────────────────────────────────────────────────

def draw_arc(hal, cx, cy, radius, start_deg, end_deg, thickness=8, color=COLOR_FG):
    """
    Draw a thick arc from start_deg to end_deg (clockwise, 0=top).
    Uses pixel-level plotting — suitable for a 1-2 second render.
    """
    start_rad = math.radians(start_deg - 90)
    end_rad   = math.radians(end_deg   - 90)
    if end_rad < start_rad:
        end_rad += 2 * math.pi

    step = 1.0 / (radius * 2 * math.pi)  # ~1 pixel arc-length per step
    angle = start_rad
    while angle <= end_rad:
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        for t in range(thickness):
            r = radius - thickness // 2 + t
            x = int(cx + r * cos_a)
            y = int(cy + r * sin_a)
            if _in_circle(x, y):
                hal.draw_pixel(x, y, color)
        angle += step


def draw_progress_ring(hal, cx, cy, radius, pct, thickness=12, color=COLOR_FG, bg_color=COLOR_BG):
    """
    Draw a full background ring, then overlay a progress arc for pct (0.0–1.0).
    """
    draw_arc(hal, cx, cy, radius, 0, 360, thickness, bg_color)
    if pct > 0:
        end_deg = min(360, pct * 360)
        draw_arc(hal, cx, cy, radius, 0, end_deg, thickness, color)


# ── Bitmap font (5×7 proportional) ───────────────────────────────────────────
# Minimal built-in charset: ASCII 32–126.
# Each char is 5 columns of 7 bits, MSB = top row.
# Sourced from public-domain 5×7 font data.

_FONT_5X7 = {
    ' ': [0x00,0x00,0x00,0x00,0x00],
    '!': [0x00,0x5F,0x00,0x00,0x00],
    '"': [0x07,0x00,0x07,0x00,0x00],
    '#': [0x14,0x7F,0x14,0x7F,0x14],
    '$': [0x24,0x2A,0x7F,0x2A,0x12],
    '%': [0x23,0x13,0x08,0x64,0x62],
    '&': [0x36,0x49,0x56,0x20,0x50],
    "'": [0x07,0x00,0x00,0x00,0x00],
    '(': [0x1C,0x22,0x41,0x00,0x00],
    ')': [0x41,0x22,0x1C,0x00,0x00],
    '*': [0x2A,0x1C,0x7F,0x1C,0x2A],
    '+': [0x08,0x08,0x3E,0x08,0x08],
    ',': [0x58,0x38,0x00,0x00,0x00],
    '-': [0x08,0x08,0x08,0x08,0x08],
    '.': [0x60,0x60,0x00,0x00,0x00],
    '/': [0x20,0x10,0x08,0x04,0x02],
    '0': [0x3E,0x51,0x49,0x45,0x3E],
    '1': [0x00,0x42,0x7F,0x40,0x00],
    '2': [0x62,0x51,0x49,0x49,0x46],
    '3': [0x21,0x41,0x49,0x4D,0x33],
    '4': [0x18,0x14,0x12,0x7F,0x10],
    '5': [0x27,0x45,0x45,0x45,0x39],
    '6': [0x3C,0x4A,0x49,0x49,0x30],
    '7': [0x01,0x71,0x09,0x05,0x03],
    '8': [0x36,0x49,0x49,0x49,0x36],
    '9': [0x06,0x49,0x49,0x29,0x1E],
    ':': [0x36,0x36,0x00,0x00,0x00],
    ';': [0x56,0x36,0x00,0x00,0x00],
    '<': [0x08,0x14,0x22,0x41,0x00],
    '=': [0x14,0x14,0x14,0x14,0x14],
    '>': [0x41,0x22,0x14,0x08,0x00],
    '?': [0x02,0x01,0x59,0x05,0x02],
    '@': [0x3E,0x41,0x5D,0x55,0x1E],
    'A': [0x7E,0x09,0x09,0x09,0x7E],
    'B': [0x7F,0x49,0x49,0x49,0x36],
    'C': [0x3E,0x41,0x41,0x41,0x22],
    'D': [0x7F,0x41,0x41,0x41,0x3E],
    'E': [0x7F,0x49,0x49,0x49,0x41],
    'F': [0x7F,0x09,0x09,0x09,0x01],
    'G': [0x3E,0x41,0x41,0x49,0x7A],
    'H': [0x7F,0x08,0x08,0x08,0x7F],
    'I': [0x41,0x7F,0x41,0x00,0x00],
    'J': [0x20,0x41,0x41,0x3F,0x01],
    'K': [0x7F,0x08,0x14,0x22,0x41],
    'L': [0x7F,0x40,0x40,0x40,0x40],
    'M': [0x7F,0x02,0x04,0x02,0x7F],
    'N': [0x7F,0x04,0x08,0x10,0x7F],
    'O': [0x3E,0x41,0x41,0x41,0x3E],
    'P': [0x7F,0x09,0x09,0x09,0x06],
    'Q': [0x3E,0x41,0x51,0x21,0x5E],
    'R': [0x7F,0x09,0x19,0x29,0x46],
    'S': [0x26,0x49,0x49,0x49,0x32],
    'T': [0x01,0x01,0x7F,0x01,0x01],
    'U': [0x3F,0x40,0x40,0x40,0x3F],
    'V': [0x1F,0x20,0x40,0x20,0x1F],
    'W': [0x3F,0x40,0x30,0x40,0x3F],
    'X': [0x63,0x14,0x08,0x14,0x63],
    'Y': [0x07,0x08,0x70,0x08,0x07],
    'Z': [0x61,0x51,0x49,0x45,0x43],
    '[': [0x7F,0x41,0x41,0x00,0x00],
    '\\': [0x02,0x04,0x08,0x10,0x20],
    ']': [0x41,0x41,0x7F,0x00,0x00],
    '^': [0x04,0x02,0x01,0x02,0x04],
    '_': [0x40,0x40,0x40,0x40,0x40],
    '`': [0x01,0x02,0x04,0x00,0x00],
    'a': [0x20,0x54,0x54,0x54,0x78],
    'b': [0x7F,0x48,0x44,0x44,0x38],
    'c': [0x38,0x44,0x44,0x44,0x20],
    'd': [0x38,0x44,0x44,0x48,0x7F],
    'e': [0x38,0x54,0x54,0x54,0x18],
    'f': [0x08,0x7E,0x09,0x01,0x02],
    'g': [0x18,0xA4,0xA4,0xA4,0x7C],
    'h': [0x7F,0x08,0x04,0x04,0x78],
    'i': [0x00,0x44,0x7D,0x40,0x00],
    'j': [0x40,0x80,0x84,0x7D,0x00],
    'k': [0x7F,0x10,0x28,0x44,0x00],
    'l': [0x00,0x41,0x7F,0x40,0x00],
    'm': [0x7C,0x04,0x18,0x04,0x78],
    'n': [0x7C,0x08,0x04,0x04,0x78],
    'o': [0x38,0x44,0x44,0x44,0x38],
    'p': [0xFC,0x24,0x24,0x24,0x18],
    'q': [0x18,0x24,0x24,0x24,0xFC],
    'r': [0x7C,0x08,0x04,0x04,0x08],
    's': [0x48,0x54,0x54,0x54,0x24],
    't': [0x04,0x3F,0x44,0x40,0x20],
    'u': [0x3C,0x40,0x40,0x40,0x7C],
    'v': [0x1C,0x20,0x40,0x20,0x1C],
    'w': [0x3C,0x40,0x30,0x40,0x3C],
    'x': [0x44,0x28,0x10,0x28,0x44],
    'y': [0x1C,0xA0,0xA0,0xA0,0x7C],
    'z': [0x44,0x64,0x54,0x4C,0x44],
    '{': [0x08,0x36,0x41,0x00,0x00],
    '|': [0x00,0x7F,0x00,0x00,0x00],
    '}': [0x41,0x36,0x08,0x00,0x00],
    '~': [0x08,0x04,0x08,0x10,0x08],
}

_CHAR_W = 5   # glyph columns
_CHAR_H = 7   # glyph rows
_CHAR_GAP = 1 # pixel gap between chars


def char_width(scale=1):
    return (_CHAR_W + _CHAR_GAP) * scale


def text_width(text, scale=1):
    return len(text) * char_width(scale)


def draw_char(hal, x, y, ch, color=COLOR_FG, scale=1):
    """Draw a single character at (x,y) top-left. Returns new x after char."""
    cols = _FONT_5X7.get(ch, _FONT_5X7.get(' '))
    for col_idx, col_bits in enumerate(cols):
        for row_idx in range(_CHAR_H):
            if col_bits & (1 << (_CHAR_H - 1 - row_idx)):
                px = x + col_idx * scale
                py = y + row_idx * scale
                if scale == 1:
                    if _in_circle(px, py):
                        hal.draw_pixel(px, py, color)
                else:
                    hal.fill_rect(px, py, scale, scale, color)
    return x + (_CHAR_W + _CHAR_GAP) * scale


def draw_text(hal, x, y, text, color=COLOR_FG, scale=1):
    """Draw a string left-aligned at (x,y). Returns x after last char."""
    cx = x
    for ch in str(text):
        cx = draw_char(hal, cx, y, ch, color=color, scale=scale)
    return cx


def draw_text_centred(hal, text, y, color=COLOR_FG, scale=1):
    """Draw text horizontally centred on the canvas at vertical position y."""
    w = text_width(str(text), scale)
    x = (_CX) - w // 2
    draw_text(hal, x, y, text, color=color, scale=scale)


# ── Checklist item ────────────────────────────────────────────────────────────

def draw_checklist_item(hal, x, y, label, completed, scale=1):
    """Draw a checkbox + label. Returns bottom-left y of item."""
    box_size = _CHAR_H * scale
    # Outer box
    hal.draw_hline(x, y, box_size, COLOR_FG)
    hal.draw_hline(x, y + box_size - 1, box_size, COLOR_FG)
    hal.draw_vline(x, y, box_size, COLOR_FG)
    hal.draw_vline(x + box_size - 1, y, box_size, COLOR_FG)
    # Tick mark if completed
    if completed:
        # Simple cross tick: two diagonals inside the box
        for i in range(2, box_size - 2):
            hal.draw_pixel(x + i, y + i, COLOR_FG)
            hal.draw_pixel(x + box_size - 1 - i, y + i, COLOR_FG)
    draw_text(hal, x + box_size + 4, y, label, scale=scale)
    return y + box_size + 4


# ── Heatmap grid ──────────────────────────────────────────────────────────────

def draw_heatmap(hal, habits, cx=_CX, cy=_CY, cell_size=20, gap=4):
    """
    Draw a 7-column × N-row heatmap centred at (cx, cy).
    habits: dict of {name: [bool x 7]}
    """
    names  = list(habits.keys())
    rows   = len(names)
    cols   = 7

    cell_total = cell_size + gap
    grid_w = cols * cell_total - gap
    grid_h = rows * cell_total - gap
    x0 = cx - grid_w // 2
    y0 = cy - grid_h // 2

    for r, name in enumerate(names):
        days = habits[name]
        for c, done in enumerate(days):
            rx = x0 + c * cell_total
            ry = y0 + r * cell_total
            color = COLOR_FG if done else COLOR_BG
            # Draw filled cell with border
            hal.fill_rect(rx, ry, cell_size, cell_size, color)
            # Border always in FG
            hal.draw_hline(rx,              ry,              cell_size, COLOR_FG)
            hal.draw_hline(rx,              ry + cell_size-1, cell_size, COLOR_FG)
            hal.draw_vline(rx,              ry,              cell_size, COLOR_FG)
            hal.draw_vline(rx + cell_size-1, ry,              cell_size, COLOR_FG)


# ── Divider line ──────────────────────────────────────────────────────────────

def draw_divider(hal, y, margin=40, color=COLOR_FG):
    hal.draw_hline(margin, y, WIDTH - 2 * margin, color)
