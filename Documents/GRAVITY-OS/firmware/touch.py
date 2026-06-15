# touch.py — Touch controller driver
#
# Supports:
#   CST816S  (production, I2C 0x15) — single-touch capacitive, gesture decode built-in
#   GT911    (eval module, I2C 0x5D) — multi-touch, 5-point
#
# The active driver is selected via config.TOUCH_DRIVER.
# INT pin (GPIO6) fires on touch — polled via pin.value() in the main loop.
# RST pin (GPIO15) used for hardware reset.
#
# Public interface:
#   touch = Touch()
#   touch.init(i2c)
#   gesture, x, y = touch.read()   → gesture is "tap"|"swipe_left"|"swipe_right"|"long_press"|None

from machine import Pin
import utime
import config

# ── CST816S registers ─────────────────────────────────────────────────────────
_CST_GESTURE  = 0x01
_CST_FINGER   = 0x02
_CST_XH       = 0x03
_CST_XL       = 0x04
_CST_YH       = 0x05
_CST_YL       = 0x06

_CST_GESTURE_NONE       = 0x00
_CST_GESTURE_SWIPE_UP   = 0x01
_CST_GESTURE_SWIPE_DOWN = 0x02
_CST_GESTURE_SWIPE_LEFT = 0x03
_CST_GESTURE_SWIPE_RIGHT= 0x04
_CST_GESTURE_CLICK      = 0x05
_CST_GESTURE_DCLICK     = 0x0B
_CST_GESTURE_LONG       = 0x0C

# CST816S → normalised gesture string
_CST_MAP = {
    _CST_GESTURE_SWIPE_LEFT:  "swipe_left",
    _CST_GESTURE_SWIPE_RIGHT: "swipe_right",
    _CST_GESTURE_CLICK:       "tap",
    _CST_GESTURE_DCLICK:      "tap",
    _CST_GESTURE_LONG:        "long_press",
    _CST_GESTURE_SWIPE_UP:    "swipe_up",
    _CST_GESTURE_SWIPE_DOWN:  "swipe_down",
}

# ── GT911 registers ───────────────────────────────────────────────────────────
_GT911_STATUS   = 0x814E
_GT911_PT1_XL   = 0x8150
_GT911_PT1_XH   = 0x8151
_GT911_PT1_YL   = 0x8152
_GT911_PT1_YH   = 0x8153


class _CST816SDriver:

    def __init__(self, i2c, addr, int_pin, rst_pin):
        self._i2c  = i2c
        self._addr = addr
        self._int  = int_pin
        self._rst  = rst_pin
        self._last_gesture = None
        self._last_x = 0
        self._last_y = 0

    def init(self):
        self._rst(0)
        utime.sleep_ms(10)
        self._rst(1)
        utime.sleep_ms(50)
        # Wake on all gestures, continuous reporting
        try:
            # IRQ control: enable gesture + continuous touch
            self._i2c.writeto_mem(self._addr, 0xFA, bytes([0x30]))
        except Exception as e:
            print(f"[touch/cst816s] init warning: {e}")
        print("[touch] CST816S initialised")

    def has_data(self):
        return self._int.value() == 0

    def read(self):
        try:
            buf = self._i2c.readfrom_mem(self._addr, _CST_GESTURE, 6)
        except Exception as e:
            print(f"[touch/cst816s] read error: {e}")
            return None, 0, 0

        gesture_id = buf[0]
        fingers    = buf[1] & 0x0F
        if fingers == 0:
            return None, 0, 0

        x = ((buf[2] & 0x0F) << 8) | buf[3]
        y = ((buf[4] & 0x0F) << 8) | buf[5]
        gesture = _CST_MAP.get(gesture_id, "tap" if fingers else None)
        return gesture, x, y


class _GT911Driver:

    def __init__(self, i2c, addr, int_pin, rst_pin):
        self._i2c  = i2c
        self._addr = addr
        self._int  = int_pin
        self._rst  = rst_pin
        self._prev_x = 0
        self._prev_y = 0
        self._touch_start = 0
        self._touching    = False

    def _reg16_write(self, reg, val):
        data = bytes([(reg >> 8) & 0xFF, reg & 0xFF, val])
        self._i2c.writeto(self._addr, data)

    def _reg16_read(self, reg, n):
        self._i2c.writeto(self._addr, bytes([(reg >> 8) & 0xFF, reg & 0xFF]))
        return self._i2c.readfrom(self._addr, n)

    def init(self):
        self._rst(0)
        utime.sleep_ms(10)
        self._int(0)
        utime.sleep_ms(1)
        self._rst(1)
        utime.sleep_ms(50)
        # Release INT
        self._int.init(Pin.IN)
        utime.sleep_ms(50)
        print("[touch] GT911 initialised")

    def has_data(self):
        return self._int.value() == 0

    def read(self):
        try:
            status = self._reg16_read(_GT911_STATUS, 1)[0]
        except Exception as e:
            print(f"[touch/gt911] read error: {e}")
            return None, 0, 0

        if not (status & 0x80):
            return None, 0, 0   # buffer not ready

        fingers = status & 0x0F
        # Clear status
        self._reg16_write(_GT911_STATUS, 0x00)

        if fingers == 0:
            if self._touching:
                self._touching = False
                elapsed = utime.ticks_diff(utime.ticks_ms(), self._touch_start)
                if elapsed > 600:
                    return "long_press", self._prev_x, self._prev_y
                # Detect swipe vs tap by displacement
                return "tap", self._prev_x, self._prev_y
            return None, 0, 0

        try:
            pt = self._reg16_read(_GT911_PT1_XL, 4)
        except Exception as e:
            print(f"[touch/gt911] point read error: {e}")
            return None, 0, 0

        x = (pt[1] << 8) | pt[0]
        y = (pt[3] << 8) | pt[2]

        if not self._touching:
            self._touching    = True
            self._touch_start = utime.ticks_ms()
            self._prev_x      = x
            self._prev_y      = y
            return None, x, y   # finger down — no gesture yet

        # Compute swipe
        dx = x - self._prev_x
        if abs(dx) > 40:
            gesture = "swipe_left" if dx < 0 else "swipe_right"
            self._prev_x = x
            self._prev_y = y
            return gesture, x, y

        self._prev_x = x
        self._prev_y = y
        return None, x, y


class Touch:
    """
    Unified touch interface.  Selects CST816S or GT911 based on config.TOUCH_DRIVER.
    """

    def __init__(self):
        self._driver = None
        self._int_pin = None
        self._rst_pin = None

    def init(self, i2c):
        self._int_pin = Pin(config.TOUCH_INT, Pin.IN)
        self._rst_pin = Pin(config.TOUCH_RST, Pin.OUT, value=1)

        driver_name = config.TOUCH_DRIVER
        if driver_name == "cst816s":
            self._driver = _CST816SDriver(
                i2c, config.ADDR_CST816S, self._int_pin, self._rst_pin)
        elif driver_name == "gt911":
            self._driver = _GT911Driver(
                i2c, config.ADDR_GT911, self._int_pin, self._rst_pin)
        else:
            raise ValueError(f"Unknown touch driver: {driver_name}")

        try:
            self._driver.init()
        except Exception as e:
            print(f"[touch] init error: {e}")
            self._driver = None

    def has_data(self):
        """Returns True if the INT pin indicates a touch event is pending."""
        if self._driver is None:
            return False
        try:
            return self._driver.has_data()
        except Exception:
            return False

    def read(self):
        """
        Read one touch event.
        Returns (gesture_str_or_None, x, y).
        gesture is one of: "tap", "swipe_left", "swipe_right", "long_press", None
        """
        if self._driver is None:
            return None, 0, 0
        try:
            return self._driver.read()
        except Exception as e:
            print(f"[touch] read error: {e}")
            return None, 0, 0
