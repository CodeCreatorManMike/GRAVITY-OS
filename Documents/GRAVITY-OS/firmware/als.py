# als.py — VEML7700 ambient light sensor + backlight PWM control
#
# I2C address: 0x10
# Reads lux and maps it to a PWM duty cycle on the backlight GPIO (GPIO18).
# Reference: VEML7700 Application Note Rev 1.1

from machine import Pin, PWM
import utime
import config

# ── VEML7700 registers ────────────────────────────────────────────────────────
_ALS_CONF  = 0x00   # configuration word
_ALS_WH    = 0x01   # high threshold window
_ALS_WL    = 0x02   # low threshold window
_ALS_PSM   = 0x03   # power saving mode
_ALS_OUT   = 0x04   # ALS output (raw counts)
_WHITE_OUT = 0x05   # white channel output

# Gain / integration time for _ALS_CONF
# Bits[12:11] = gain, bits[9:6] = integration time
# Gain x1 = 00, x2 = 01, x(1/8) = 10, x(1/4) = 11
# IT 25ms=1100, 50ms=1000, 100ms=0000, 200ms=0001, 400ms=0010, 800ms=0011
_CONF_GAIN_1   = 0x0000
_CONF_IT_100MS = 0x0000
_CONF_POWER_ON = 0x0000  # ALS_SD = 0 → on

# Resolution at gain=1, IT=100ms: 0.0576 lux/count
_LUX_RESOLUTION = 0.0576

# ── Backlight mapping ─────────────────────────────────────────────────────────
_LUX_BRIGHT = 1000   # above this → max brightness
_LUX_DIM    =   10   # below this → min brightness
_DUTY_MIN   =  10    # % PWM minimum (never fully off)
_DUTY_MAX   = 100    # % PWM maximum

_PWM_FREQ   = 1000   # Hz — above flicker threshold


class ALS:

    def __init__(self):
        self._i2c   = None
        self._addr  = config.ADDR_VEML7700
        self._ok    = False
        self._pwm   = None
        self._duty  = config.BACKLIGHT_ACTIVE  # current duty %

    def init(self, i2c):
        self._i2c = i2c

        # Initialise backlight PWM
        try:
            bl_pin = Pin(config.BACKLIGHT_GPIO, Pin.OUT)
            self._pwm = PWM(bl_pin, freq=_PWM_FREQ)
            self._set_duty(config.BACKLIGHT_ACTIVE)
            print(f"[als] backlight PWM on GPIO{config.BACKLIGHT_GPIO}")
        except Exception as e:
            print(f"[als] backlight PWM error: {e}")

        # Initialise VEML7700
        try:
            conf = _CONF_GAIN_1 | _CONF_IT_100MS | _CONF_POWER_ON
            self._write_reg(_ALS_CONF, conf)
            utime.sleep_ms(5)
            self._ok = True
            print("[als] VEML7700 initialised")
        except Exception as e:
            print(f"[als] VEML7700 init error: {e}")

    def read_lux(self):
        """Return ambient lux as a float, or None on error."""
        if not self._ok:
            return None
        try:
            counts = self._read_reg(_ALS_OUT)
            return counts * _LUX_RESOLUTION
        except Exception as e:
            print(f"[als] read error: {e}")
            return None

    def auto_brightness(self):
        """
        Read lux, compute appropriate backlight duty, apply it.
        Returns duty % actually set.
        """
        lux = self.read_lux()
        if lux is None:
            return self._duty

        # Linear interpolation between dim and bright
        if lux <= _LUX_DIM:
            duty = _DUTY_MIN
        elif lux >= _LUX_BRIGHT:
            duty = _DUTY_MAX
        else:
            duty = int(_DUTY_MIN + (_DUTY_MAX - _DUTY_MIN) *
                       (lux - _LUX_DIM) / (_LUX_BRIGHT - _LUX_DIM))

        self._set_duty(duty)
        return duty

    def set_brightness(self, pct):
        """Manually set backlight to pct (0–100)."""
        self._set_duty(max(0, min(100, pct)))

    def backlight_off(self):
        if self._pwm:
            self._pwm.duty_u16(0)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _set_duty(self, pct):
        self._duty = pct
        if self._pwm:
            duty_u16 = int(pct / 100 * 65535)
            self._pwm.duty_u16(duty_u16)

    def _read_reg(self, reg):
        self._i2c.writeto(self._addr, bytes([reg]))
        buf = self._i2c.readfrom(self._addr, 2)
        return buf[0] | (buf[1] << 8)

    def _write_reg(self, reg, val):
        self._i2c.writeto(self._addr, bytes([reg, val & 0xFF, (val >> 8) & 0xFF]))
