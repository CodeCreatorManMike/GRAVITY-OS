import math
import os
from PIL import Image, ImageDraw, ImageFont

C     = 180
SIZE  = 360
INK   = "#14130d"
PAPER = "#f4f2ea"
RAD   = math.pi / 180

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_FONT_CACHE = {}

def _font(size, weight="Regular", family="JetBrainsMono"):
    key = f"{family}_{size}_{weight}"
    if key not in _FONT_CACHE:
        # Primary: look for exact family match
        candidates = [
            os.path.join(FONT_DIR, f"{family}-{weight}.ttf"),
            os.path.join(FONT_DIR, f"JetBrainsMono-{weight}.ttf"),
        ]
        loaded = False
        for path in candidates:
            try:
                _FONT_CACHE[key] = ImageFont.truetype(path, size)
                loaded = True
                break
            except Exception:
                continue
        if not loaded:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]

def P(r, d):
    return (C + r * math.sin(d * RAD), C - r * math.cos(d * RAD))

def chord_hw(y, r=150):
    return math.sqrt(max(0.0, r * r - (y - C) ** 2))

def new_canvas():
    img  = Image.new("RGB", (SIZE, SIZE), PAPER)
    draw = ImageDraw.Draw(img)
    return img, draw

def apply_circle_mask(img):
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, SIZE-1, SIZE-1], fill=255)
    result = Image.new("RGB", (SIZE, SIZE), PAPER)
    result.paste(img, mask=mask)
    return result

def ring(draw, r, sw=1.0, dash=None, colour=INK):
    if dash is None:
        bb = [C-r, C-r, C+r, C+r]
        draw.arc(bb, start=-90, end=270, fill=colour, width=max(1, round(sw)))
    else:
        on, off = dash
        circ  = 2 * math.pi * r
        total = on + off
        n     = max(1, int(circ / total))
        step  = 360 / n
        on_deg = step * (on / total)
        for i in range(n):
            s  = i * step - 90
            e  = s + on_deg
            bb = [C-r, C-r, C+r, C+r]
            draw.arc(bb, start=s, end=e, fill=colour, width=max(1, round(sw)))

def arc(draw, r, a, b, sw=2.0, colour=INK):
    if b - a >= 359.9:
        ring(draw, r, sw, colour=colour)
        return
    bb = [C-r, C-r, C+r, C+r]
    draw.arc(bb, start=a-90, end=b-90, fill=colour, width=max(1, round(sw)))

def ticks(draw, r, n, long_every, short_len, long_len, colour=INK):
    for i in range(n):
        d  = i * 360 / n
        L  = long_len if (i % long_every == 0) else short_len
        # Heavier weights so short ticks are visibly lighter than long ones
        sw = 2.0 if (i % long_every == 0) else 1.0
        x1, y1 = P(r, d)
        x2, y2 = P(r-L, d)
        draw.line([(x1,y1),(x2,y2)], fill=colour, width=max(1, round(sw)))

def T(draw, x, y, text, s=12, w=400, a="middle", ls=0, colour=INK,
      family="JetBrainsMono"):
    """
    Draw text with y as the typographic baseline (matches SVG dominant-baseline=alphabetic).
    """
    wmap = {300:"Light", 400:"Regular", 500:"Medium", 600:"Bold", 700:"Bold"}
    font = _font(s, wmap.get(w, "Regular"), family)
    chars = list(text)
    if not chars:
        return
    widths  = [draw.textlength(ch, font=font) for ch in chars]
    total_w = sum(widths) + ls * (len(chars)-1)
    cx = x - total_w/2 if a=="middle" else (x - total_w if a=="end" else x)
    # Use font.getmetrics() so y=baseline matches SVG coordinate convention
    try:
        ascent, _ = font.getmetrics()
    except Exception:
        bbox   = font.getbbox("A")
        ascent = bbox[3] - bbox[1]
    cy = y - ascent
    for i, ch in enumerate(chars):
        draw.text((cx, cy), ch, font=font, fill=colour)
        cx += widths[i] + ls

def dot(draw, x, y, r, filled=True, sw=1.1, colour=INK):
    bb = [x-r, y-r, x+r, y+r]
    if filled:
        draw.ellipse(bb, fill=colour)
    else:
        draw.ellipse(bb, outline=colour, width=max(1, round(sw)))

def sq(draw, x, y, size, filled, colour=INK):
    if filled:
        draw.rounded_rectangle([x, y, x+size, y+size], radius=1, fill=colour)
    else:
        draw.rounded_rectangle([x+0.5, y+0.5, x+size-0.5, y+size-0.5], radius=1, outline=colour, width=1)

def arc_sq(draw, r, deg, size, filled, colour=INK):
    cx, cy = P(r, deg)
    half   = size / 2
    a      = deg * RAD
    cos_a, sin_a = math.cos(a), math.sin(a)
    corners = [(-half,-half),(half,-half),(half,half),(-half,half)]
    pts = [(cx + x*cos_a - y*sin_a, cy + x*sin_a + y*cos_a) for x,y in corners]
    if filled:
        draw.polygon(pts, fill=colour)
    else:
        draw.polygon(pts, outline=colour)

def brackets(draw, x, y, w, h, k=9, sw=1.8, colour=INK):
    lw = max(1, round(sw))
    def corner(px, py, dx, dy):
        draw.line([(px+dx,py),(px,py)], fill=colour, width=lw)
        draw.line([(px,py),(px,py+dy)], fill=colour, width=lw)
    corner(x,   y,    k,  k)
    corner(x+w, y,   -k,  k)
    corner(x,   y+h,  k, -k)
    corner(x+w, y+h, -k, -k)

def scan(draw, y, r=150, dash=(1.5,4), sw=1.0, colour=INK):
    hw    = chord_hw(y, r)
    x1,x2 = C-hw, C+hw
    on,off = dash
    total  = on+off
    px     = x1
    while px < x2:
        seg_end = min(px+on, x2)
        draw.line([(px,y),(seg_end,y)], fill=colour, width=max(1,round(sw)))
        px += total

def moon(draw, cx, cy, R, sw=1.5, colour=INK):
    lw  = max(1, round(sw))
    bb1 = [cx-R, cy-R, cx+R, cy+R]
    draw.arc(bb1, start=90, end=270, fill=colour, width=lw)
    R2  = R * 1.65
    bb2 = [cx-R2, cy-R2, cx+R2, cy+R2]
    draw.arc(bb2, start=270, end=90, fill=colour, width=lw)
    dot(draw, cx, cy-R, 0.8, filled=True, colour=colour)
    dot(draw, cx, cy+R, 0.8, filled=True, colour=colour)

def star(draw, x, y, r=2.4, colour=INK):
    draw.line([(x, y-r),(x, y+r)], fill=colour, width=1)
    draw.line([(x-r, y),(x+r, y)], fill=colour, width=1)

def _paste_char(img, ch, font, cx, cy, rot_deg, r_val, g_val, b_val):
    from PIL import Image
    bbox = font.getbbox(ch)
    cw   = max(1, bbox[2]-bbox[0])
    ch_h = max(1, bbox[3]-bbox[1])
    pad  = max(cw, ch_h) + 14
    tmp  = Image.new("RGBA", (pad*2, pad*2), (0,0,0,0))
    from PIL import ImageDraw
    ImageDraw.Draw(tmp).text(
        (pad - cw//2, pad - ch_h//2 - bbox[1]),
        ch, font=font, fill=(r_val, g_val, b_val, 255)
    )
    rotated = tmp.rotate(-rot_deg, expand=False, resample=Image.BICUBIC, center=(pad,pad))
    img.paste(rotated, (int(cx-pad), int(cy-pad)), mask=rotated)

def _place_curved_text(img, text, r, centre_deg, font_size=10,
                        weight="Bold", letter_spacing=4, colour="#14130d", top=True,
                        family="JetBrainsMono"):
    import math
    from PIL import Image, ImageDraw
    font     = _font(font_size, weight, family)
    draw_tmp = ImageDraw.Draw(Image.new("RGB",(1,1)))
    chars    = list(text)
    if not chars:
        return
    # Use cap-height from getbbox("A") for offset: centres caps on the rim arc
    cap_bbox = font.getbbox("A")
    cap_h    = cap_bbox[3] - cap_bbox[1]
    RAD_ = math.pi / 180
    def px_to_deg(px): return math.degrees(px / r)
    char_w_px  = [draw_tmp.textlength(ch, font=font) for ch in chars]
    char_w_deg = [px_to_deg(w) for w in char_w_px]
    space_deg  = px_to_deg(letter_spacing)
    total_deg  = sum(char_w_deg) + space_deg * (len(chars)-1)
    r_val = int(colour[1:3],16)
    g_val = int(colour[3:5],16)
    b_val = int(colour[5:7],16)
    # Place character centres so cap tops sit at radius r (hugging the rim from inside)
    offset_r = r - cap_h * 0.5 - 1
    def Ploc(radius, d):
        C_ = 180
        return (C_ + radius * math.sin(d * RAD_), C_ - radius * math.cos(d * RAD_))
    if top:
        cur_deg = centre_deg - total_deg / 2
        for i, ch in enumerate(chars):
            char_centre_deg = cur_deg + char_w_deg[i] / 2
            cx, cy = Ploc(offset_r, char_centre_deg)
            _paste_char(img, ch, font, cx, cy, char_centre_deg, r_val, g_val, b_val)
            cur_deg += char_w_deg[i] + space_deg
    else:
        cur_deg = centre_deg + total_deg / 2
        for i, ch in enumerate(chars):
            char_centre_deg = cur_deg - char_w_deg[i] / 2
            cx, cy = Ploc(offset_r, char_centre_deg)
            _paste_char(img, ch, font, cx, cy, char_centre_deg + 180, r_val, g_val, b_val)
            cur_deg -= char_w_deg[i] + space_deg

def top_label(img, draw, text, font_size=10, weight="Bold", letter_spacing=4,
              r=159, span=52, colour="#14130d", family="JetBrainsMono"):
    _place_curved_text(img, text, r=r, centre_deg=0, font_size=font_size,
                        weight=weight, letter_spacing=letter_spacing,
                        colour=colour, top=True, family=family)

def bot_label(img, draw, text, font_size=10, weight="Bold", letter_spacing=4,
              r=152, span=52, colour="#14130d", family="JetBrainsMono"):
    _place_curved_text(img, text, r=r, centre_deg=180, font_size=font_size,
                        weight=weight, letter_spacing=letter_spacing,
                        colour=colour, top=False, family=family)

def prog_arc(draw, r, pct, sw=5, colour="#14130d"):
    ring(draw, r, sw=1.0, dash=(1.5,4), colour=colour)
    end_deg = 360 * pct
    arc(draw, r, 0, end_deg, sw=sw, colour=colour)
    ex, ey = P(r, end_deg)
    dot(draw, ex, ey, 4.2, filled=True,  colour="#f4f2ea")
    dot(draw, ex, ey, 4.2, filled=False, sw=2.0, colour=colour)
