# imu.py — LIS2DW12 accelerometer driver
#
# I2C address: 0x18
# Used for:
#   - Orientation detection (portrait / landscape)
#   - Wake-on-motion interrupt on INT1 (GPIO16)
#   - Configuring deep sleep wakeup source
#
# Reference: LIS2DW12 datasheet DS12441 rev 7

import utime
import config

# ── Register addresses ────────────────────────────────────────────────────────
_WHO_AM_I   = 0x0F   # expected 0x44
_CTRL1      = 0x20
_CTRL2      = 0x21
_CTRL4_INT1 = 0x23   # INT1 routing
_CTRL5_INT2 = 0x24   # INT2 routing
_CTRL6      = 0x25
_STATUS     = 0x27
_OUT_X_L    = 0x28
_OUT_X_H    = 0x29
_OUT_Y_L    = 0x2A
_OUT_Y_H    = 0x2B
_OUT_Z_L    = 0x2C
_OUT_Z_H    = 0x2D
_WAKE_UP_THS= 0x34   # wake-up threshold
_WAKE_UP_DUR= 0x35   # wake-up duration
_WAKE_UP_SRC= 0x38   # wake-up event source

_WHO_AM_I_VAL = 0x44

# CTRL1: ODR + mode
_ODR_OFF  = 0b0000
_ODR_12HZ = 0b0010
_MODE_LP  = 0b00   # low-power mode
_LP_MODE1 = 0b00

# ── Orientation constants ─────────────────────────────────────────────────────
ORIENT_PORTRAIT    = "portrait"
ORIENT_LANDSCAPE_L = "landscape_left"
ORIENT_LANDSCAPE_R = "landscape_right"
ORIENT_FACE_UP     = "face_up"
ORIENT_FACE_DOWN   = "face_down"


class IMU:

    def __init__(self):
        self._i2c  = None
        self._addr = config.ADDR_LIS2DW12
        self._ok   = False

    def init(self, i2c):
        self._i2c = i2c
        try:
            who = self._read_reg(_WHO_AM_I)
            if who != _WHO_AM_I_VAL:
                print(f"[imu] WHO_AM_I mismatch: 0x{who:02X} (expected 0x44)")
                return
        except Exception as e:
            print(f"[imu] init error: {e}")
            return

        # Soft reset
        self._write_reg(_CTRL2, 0x40)
        utime.sleep_ms(10)

        # CTRL6: full-scale ±2g, low-noise off, BW = ODR/2
        self._write_reg(_CTRL6, 0x00)

        # CTRL1: 12.5 Hz, low-power mode 1 (12-bit)
        self._write_reg(_CTRL1, (_ODR_12HZ << 4) | (_MODE_LP << 2) | _LP_MODE1)

        # Wake-up threshold: ~156 mg (8 * 1LSB at 1/64 FS = 31.25mg/LSB → ~250mg)
        self._write_reg(_WAKE_UP_THS, 0x04)

        # Wake-up duration: 2 ODR cycles
        self._write_reg(_WAKE_UP_DUR, 0x02)

        # Route wake-up to INT1
        self._write_reg(_CTRL4_INT1, 0x20)

        self._ok = True
        print("[imu] LIS2DW12 initialised")

    def is_ok(self):
        return self._ok

    # ── Readings ──────────────────────────────────────────────────────────────

    def read_accel(self):
        """Return (x, y, z) in raw LSB (12-bit left-justified, divide by 16 for signed 12-bit)."""
        if not self._ok:
            return 0, 0, 0
        try:
            buf = bytearray(6)
            self._i2c.readfrom_mem_into(self._addr, _OUT_X_L | 0x80, buf)
            x = self._s16(buf[1], buf[0]) >> 4
            y = self._s16(buf[3], buf[2]) >> 4
            z = self._s16(buf[5], buf[4]) >> 4
            return x, y, z
        except Exception as e:
            print(f"[imu] read error: {e}")
            return 0, 0, 0

    def orientation(self):
        """Return one of the ORIENT_* constants based on strongest axis."""
        x, y, z = self.read_accel()
        ax, ay, az = abs(x), abs(y), abs(z)
        if az > ax and az > ay:
            return ORIENT_FACE_UP if z > 0 else ORIENT_FACE_DOWN
        if ay >= ax:
            return ORIENT_PORTRAIT
        return ORIENT_LANDSCAPE_L if x > 0 else ORIENT_LANDSCAPE_R

    def woke_from_motion(self):
        """True if wake-up was triggered by motion (reads and clears WAKE_UP_SRC)."""
        if not self._ok:
            return False
        try:
            src = self._read_reg(_WAKE_UP_SRC)
            return bool(src & 0x08)  # WU_IA bit
        except Exception:
            return False

    def configure_wake_on_motion(self):
        """
        Put the IMU into wake-on-motion mode (lowest-power 1.6 Hz ODR).
        Call before entering deep sleep.
        """
        if not self._ok:
            return
        # ODR = 1.6 Hz (0001), LP mode
        self._write_reg(_CTRL1, (0b0001 << 4) | (_MODE_LP << 2) | _LP_MODE1)
        # Ensure wake-up int on INT1
        self._write_reg(_CTRL4_INT1, 0x20)
        print("[imu] wake-on-motion configured")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _read_reg(self, reg):
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _write_reg(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes([val]))

    @staticmethod
    def _s16(hi, lo):
        val = (hi << 8) | lo
        return val - 65536 if val >= 32768 else val
