# display/lt7683.py — LT7683 eval board driver (ER-TFT028-2-6318)
#
# The LT7683 is a graphic controller with a built-in 2D engine.
# On the ER-TFT028-2-6318 eval module it sits between the ESP32-S3 (SPI host)
# and the ST7701S panel (RGB parallel output).  The SSD2828 bridge is
# transparent from the host side — we just talk to LT7683 registers over SPI.
#
# Interface: 4-wire SPI, 8-bit indirect register access.
#   Write cycle: CS low → write register address byte → write data byte(s) → CS high
#   Register 0x00 (STSR) readable for status polling.
#
# Host write pixel data via:
#   1. Set graphic write position (CURH0/CURV0)
#   2. Set Memory Write Command register (MRWC = 0x02)
#   3. Assert DC=data, burst-write RGB565 pixels
#
# Reference: LT7683 datasheet rev 2.3, BuyDisplay application note.

from machine import SPI, Pin
import utime
import config
from display.hal import DisplayHAL, WIDTH, HEIGHT


# ── LT7683 register map (partial — only what we need) ─────────────────────────
_REG_PWRR   = 0x01   # Power and Display Control
_REG_MRWC   = 0x02   # Memory Read/Write Command
_REG_PCSR   = 0x04   # Pixel Clock Setting
_REG_SROC   = 0x05   # Serial Flash/ROM Config
_REG_SFCLR  = 0x06   # Serial Flash Clock
_REG_SYSR   = 0x10   # System Config (color depth, MCU interface)
_REG_GCR    = 0x12   # General-Purpose IO control
_REG_HDISP  = 0x14   # Horizontal display width (pixels/8 - 1)
_REG_HNDFTR = 0x15   # Horizontal non-display fine-tune
_REG_HNDR   = 0x16   # Horizontal non-display period
_REG_HSTR   = 0x17   # HSYNC start position
_REG_HPWR   = 0x18   # HSYNC pulse width
_REG_VDISP0 = 0x19   # Vertical display height, low byte
_REG_VDISP1 = 0x1A   # Vertical display height, high nibble
_REG_VNDR0  = 0x1B   # Vertical non-display period, low
_REG_VNDR1  = 0x1C   # Vertical non-display period, high
_REG_VSTR   = 0x1D   # VSYNC start position
_REG_VPWR   = 0x1E   # VSYNC pulse width
_REG_DPCR   = 0x20   # Display Configuration
_REG_FNCR0  = 0x21   # Font Control 0
_REG_MWCR0  = 0x40   # Memory Write Control 0
_REG_MWCR1  = 0x41   # Memory Write Control 1
_REG_CURH0  = 0x46   # Canvas write cursor X, low
_REG_CURH1  = 0x47   # Canvas write cursor X, high
_REG_CURV0  = 0x48   # Canvas write cursor Y, low
_REG_CURV1  = 0x49   # Canvas write cursor Y, high


class LT7683Display(DisplayHAL):

    def _hw_init(self):
        self._cs  = Pin(config.DISPLAY_CS,  Pin.OUT, value=1)
        self._dc  = Pin(config.DISPLAY_DC,  Pin.OUT, value=1)
        self._rst = Pin(config.DISPLAY_RST, Pin.OUT, value=1)

        self._spi = SPI(
            1,
            baudrate=20_000_000,   # LT7683 SPI max ~30 MHz; 20 MHz is safe
            polarity=0,
            phase=0,
            sck=Pin(config.SPI_SCLK),
            mosi=Pin(config.SPI_MOSI),
            miso=Pin(config.SPI_MISO),
        )

        # Hardware reset
        self._rst(0)
        utime.sleep_ms(10)
        self._rst(1)
        utime.sleep_ms(100)

        self._init_controller()
        print("[lt7683] panel init complete")

    # ── Register access ───────────────────────────────────────────────────────

    def _write_reg(self, reg, val):
        self._cs(0)
        self._dc(0)
        self._spi.write(bytes([reg]))
        self._dc(1)
        self._spi.write(bytes([val]))
        self._cs(1)

    def _read_reg(self, reg):
        self._cs(0)
        self._dc(0)
        self._spi.write(bytes([reg]))
        self._dc(1)
        buf = bytearray(1)
        self._spi.readinto(buf)
        self._cs(1)
        return buf[0]

    def _wait_idle(self, timeout_ms=200):
        """Wait until LT7683 is not busy (bit 7 of STSR = 0)."""
        deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            if not (self._read_reg(0x00) & 0x80):
                return
            utime.sleep_ms(1)
        print("[lt7683] wait_idle timeout")

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_controller(self):
        # Software reset
        self._write_reg(_REG_PWRR, 0x01)
        utime.sleep_ms(50)
        self._write_reg(_REG_PWRR, 0x00)
        utime.sleep_ms(10)

        # System: 16-bit color, 8-bit MCU interface (SPI), little-endian pixels
        # SYSR[3:2]=00 → 16 bpp; SYSR[1:0]=10 → 8-bit SPI host
        self._write_reg(_REG_SYSR, 0x0C)

        # Pixel clock: LSHIFT = 1 → use full PCLK
        self._write_reg(_REG_PCSR, 0x80)
        utime.sleep_ms(1)

        # Horizontal timing for 480px panel
        # HDISP = 480/8 - 1 = 59 = 0x3B
        self._write_reg(_REG_HDISP,  0x3B)
        self._write_reg(_REG_HNDFTR, 0x00)  # fine tune = 0
        self._write_reg(_REG_HNDR,   0x03)  # non-display = 32 clocks
        self._write_reg(_REG_HSTR,   0x01)  # HSYNC start
        self._write_reg(_REG_HPWR,   0x03)  # HSYNC pulse width

        # Vertical timing for 480px panel
        self._write_reg(_REG_VDISP0, 0xDF)  # 479 low  (480-1)
        self._write_reg(_REG_VDISP1, 0x01)  # 479 high
        self._write_reg(_REG_VNDR0,  0x0F)  # non-display lines
        self._write_reg(_REG_VNDR1,  0x00)
        self._write_reg(_REG_VSTR,   0x01)
        self._write_reg(_REG_VPWR,   0x01)

        # Display config: one layer, no rotation
        self._write_reg(_REG_DPCR, 0x00)

        # Memory write control: left→right, top→bottom
        self._write_reg(_REG_MWCR0, 0x00)

        # Canvas start address: 0x000000 (internal SDRAM offset 0)
        self._write_reg(0x50, 0x00)
        self._write_reg(0x51, 0x00)
        self._write_reg(0x52, 0x00)

        # Canvas width = 480
        self._write_reg(0x53, 0xE0)  # 480 low
        self._write_reg(0x54, 0x01)  # 480 high

        # Active window = full screen
        self._write_reg(0x56, 0x00)
        self._write_reg(0x57, 0x00)
        self._write_reg(0x58, 0x00)
        self._write_reg(0x59, 0x00)
        self._write_reg(0x5A, 0xDF)  # 479 low
        self._write_reg(0x5B, 0x01)  # 479 high
        self._write_reg(0x5C, 0xDF)
        self._write_reg(0x5D, 0x01)

        # Power on display
        self._write_reg(_REG_PWRR, 0x80)
        utime.sleep_ms(10)

    # ── Buffer push ───────────────────────────────────────────────────────────

    def _hw_push_buffer(self):
        """
        Write entire 480×480 framebuffer to LT7683 canvas starting at (0,0).
        LT7683 auto-increments the write cursor.
        """
        # Set cursor to (0, 0)
        self._write_reg(_REG_CURH0, 0x00)
        self._write_reg(_REG_CURH1, 0x00)
        self._write_reg(_REG_CURV0, 0x00)
        self._write_reg(_REG_CURV1, 0x00)

        # Trigger memory write mode
        self._cs(0)
        self._dc(0)
        self._spi.write(bytes([_REG_MRWC]))
        self._dc(1)

        # Burst-write pixel data in 4KB chunks
        buf   = self._buf
        chunk = 4096
        for offset in range(0, len(buf), chunk):
            self._spi.write(buf[offset:offset + chunk])

        self._cs(1)
        self._wait_idle()
