# power.py — Deep sleep, wake sources, battery state-of-charge via MAX17048
#
# MAX17048 I2C address: 0x36
# Deep sleep: esp32.deepsleep(ms) — but we use machine.deepsleep() in MicroPython
# Wake sources: EXT0 on TOUCH_INT (GPIO6) or EXT0 on IMU_INT (GPIO16).
# On ESP32-S3 with MicroPython use machine.wake_on_ext0 / wake_on_ext1.
#
# Reference: MAX17048 datasheet rev 4; ESP32-S3 TRM chapter on RTC GPIO.

import machine
import utime
import config

# ── MAX17048 registers ────────────────────────────────────────────────────────
_REG_VCELL  = 0x02   # battery voltage (16-bit, 78.125µV/LSB)
_REG_SOC    = 0x04   # state of charge (MSB = integer %, LSB = 1/256 %)
_REG_MODE   = 0x06   # mode control (quick-start, hibernate)
_REG_VERSION= 0x08   # IC version
_REG_CONFIG = 0x0C   # alert threshold, sleep, etc.
_REG_CMD    = 0xFE   # special commands


class Power:

    def __init__(self):
        self._i2c = None
        self._addr = config.ADDR_MAX17048
        self._ok   = False

    def init(self, i2c):
        self._i2c = i2c
        try:
            ver = self._read16(_REG_VERSION)
            print(f"[power] MAX17048 version: 0x{ver:04X}")
            self._ok = True
        except Exception as e:
            print(f"[power] MAX17048 init error: {e}")

    # ── Battery ───────────────────────────────────────────────────────────────

    def battery_pct(self):
        """Return state-of-charge as integer 0–100, or None on error."""
        if not self._ok:
            return None
        try:
            raw = self._read16(_REG_SOC)
            return (raw >> 8) & 0xFF   # integer part
        except Exception as e:
            print(f"[power] SOC read error: {e}")
            return None

    def battery_voltage(self):
        """Return cell voltage in millivolts, or None on error."""
        if not self._ok:
            return None
        try:
            raw = self._read16(_REG_VCELL)
            # 78.125 µV per LSB, right-shifted by 4
            mv = (raw >> 4) * 78125 // 1000000
            return mv * 1000  # convert to mV properly
        except Exception as e:
            print(f"[power] voltage read error: {e}")
            return None

    def is_charging(self):
        """Read CHG_STAT pin (active-low open drain from charge controller)."""
        try:
            chg_pin = machine.Pin(config.CHG_STAT if hasattr(config, 'CHG_STAT') else 17,
                                  machine.Pin.IN, machine.Pin.PULL_UP)
            return chg_pin.value() == 0
        except Exception:
            return False

    # ── Sleep ─────────────────────────────────────────────────────────────────

    def enter_deep_sleep(self, imu=None):
        """
        Configure wake sources and enter ESP32-S3 deep sleep.
        Wakes on:
          - TOUCH_INT (GPIO6) — EXT0, active-low
          - IMU_INT   (GPIO16) — EXT1, active-high (wake-on-motion)
        This function does not return (device resets on wake).
        """
        print("[power] entering deep sleep — wake on touch or motion")

        if imu is not None:
            try:
                imu.configure_wake_on_motion()
            except Exception as e:
                print(f"[power] IMU wake config error: {e}")

        # Give UART time to flush
        utime.sleep_ms(100)

        # Configure EXT0 wakeup on TOUCH_INT (low level)
        touch_pin = machine.Pin(config.TOUCH_INT, machine.Pin.IN, machine.Pin.PULL_UP)
        machine.wake_on_ext0(pin=touch_pin, level=machine.WAKEUP_ALL_LOW)

        # Configure EXT1 wakeup on IMU_INT (high level)
        imu_pin = machine.Pin(config.IMU_INT, machine.Pin.IN)
        machine.wake_on_ext1(pins=(imu_pin,), level=machine.WAKEUP_ANY_HIGH)

        machine.deepsleep()   # does not return

    def reset_cause(self):
        """Return a string describing why we woke up."""
        cause = machine.reset_cause()
        causes = {
            machine.PWRON_RESET:    "power_on",
            machine.HARD_RESET:     "hard_reset",
            machine.WDT_RESET:      "watchdog",
            machine.DEEPSLEEP_RESET:"deepsleep_wake",
            machine.SOFT_RESET:     "soft_reset",
        }
        return causes.get(cause, f"unknown({cause})")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _read16(self, reg):
        self._i2c.writeto(self._addr, bytes([reg]))
        buf = self._i2c.readfrom(self._addr, 2)
        return (buf[0] << 8) | buf[1]

    def _write16(self, reg, val):
        self._i2c.writeto(self._addr, bytes([reg, (val >> 8) & 0xFF, val & 0xFF]))
