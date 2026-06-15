# display/hal.py — Abstract display HAL
#
# All rendering code (renderer.py, components.py) calls ONLY these methods.
# Concrete drivers (st7701s.py, lt7683.py) subclass DisplayHAL and implement
# the _hw_* primitives.  The framebuffer lives here so the swap is invisible
# to callers.
#
# Coordinate system: (0,0) top-left, (479,479) bottom-right, 480×480 px.
# Colour format: RGB565 big-endian (two bytes per pixel) stored in bytearray.

import config

WIDTH  = 480
HEIGHT = 480
_BUF_SIZE = WIDTH * HEIGHT * 2   # 460 800 bytes — fits in 8MB PSRAM


# ── Palette (1-bit, V1) ───────────────────────────────────────────────────────
# #F4F2EA → RGB888 (244, 242, 234) → RGB565 big-endian
# R: 244>>3=30 (0x1E), G: 242>>2=60 (0x3C), B: 234>>3=29 (0x1D)
# RGB565: (30<<11)|(60<<5)|29 = 0xF79D  → bytes: 0xF7, 0x9D
COLOR_BG  = 0xF79D   # warm paper
COLOR_FG  = 0x1082   # near-black ink
# #14130D → R:20>>3=2, G:19>>2=4, B:13>>3=1 → (2<<11)|(4<<5)|1 = 0x1081 ≈ 0x1082

_BG_HI = (COLOR_BG >> 8) & 0xFF
_BG_LO = COLOR_BG & 0xFF
_FG_HI = (COLOR_FG >> 8) & 0xFF
_FG_LO = COLOR_FG & 0xFF


class DisplayHAL:
    """
    Abstract display HAL.  Concrete drivers must implement:
      _hw_init()           — configure SPI/parallel bus, reset panel
      _hw_push_buffer()    — transfer self._buf to the panel

    Everything else (pixel ops, fill, text stub, show) is implemented here.
    """

    def __init__(self):
        self._buf = bytearray(_BUF_SIZE)
        self._width  = WIDTH
        self._height = HEIGHT
        self._initialized = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def init(self):
        """Initialize hardware and clear screen."""
        self._hw_init()
        self.clear()
        self.show()
        self._initialized = True
        print("[hal] display initialized")

    def show(self):
        """Push the framebuffer to the panel."""
        self._hw_push_buffer()

    # ── Drawing primitives ────────────────────────────────────────────────────

    def clear(self, color=None):
        """Fill entire buffer with color (default = background)."""
        if color is None:
            color = COLOR_BG
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        for i in range(0, _BUF_SIZE, 2):
            self._buf[i]   = hi
            self._buf[i+1] = lo

    def draw_pixel(self, x, y, color):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = (y * WIDTH + x) * 2
            self._buf[idx]   = (color >> 8) & 0xFF
            self._buf[idx+1] = color & 0xFF

    def fill_rect(self, x, y, w, h, color):
        """Fill an axis-aligned rectangle."""
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(WIDTH,  x + w)
        y2 = min(HEIGHT, y + h)
        for row in range(y1, y2):
            base = (row * WIDTH + x1) * 2
            for col in range(x2 - x1):
                self._buf[base + col*2]   = hi
                self._buf[base + col*2+1] = lo

    def draw_hline(self, x, y, length, color):
        self.fill_rect(x, y, length, 1, color)

    def draw_vline(self, x, y, length, color):
        self.fill_rect(x, y, 1, length, color)

    def get_pixel(self, x, y):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = (y * WIDTH + x) * 2
            return (self._buf[idx] << 8) | self._buf[idx+1]
        return COLOR_BG

    def get_buffer(self):
        return self._buf

    # ── Abstract ──────────────────────────────────────────────────────────────

    def _hw_init(self):
        raise NotImplementedError("DisplayHAL._hw_init must be implemented by driver")

    def _hw_push_buffer(self):
        raise NotImplementedError("DisplayHAL._hw_push_buffer must be implemented by driver")

    # ── Factory ───────────────────────────────────────────────────────────────

    @staticmethod
    def create(driver_name=None):
        """
        Instantiate the correct concrete driver based on config.DISPLAY_DRIVER.
        Call this instead of constructing a driver directly.
        """
        name = driver_name or config.DISPLAY_DRIVER
        if name == "st7701s":
            from display.st7701s import ST7701SDisplay
            return ST7701SDisplay()
        elif name == "lt7683":
            from display.lt7683 import LT7683Display
            return LT7683Display()
        else:
            raise ValueError(f"Unknown display driver: {name}")
