# display/st7701s.py — ST7701S bare panel driver (production)
#
# The ST7701S is configured over a 3-wire/4-wire SPI command channel.
# Pixel data is clocked out over an 8-bit or 16-bit RGB parallel interface
# (MIPI DBI Type C / SPI 16-bit mode depending on IM pins).
#
# For the ESP32-S3 eval bring-up we use SPI mode:
#   - Command/data via 4-wire SPI (CS, DC, SCLK, MOSI)
#   - Pixel data also via SPI (DMA-backed for speed)
#
# The ST7701S datasheet init sequence is derived from the ER-TFT028-2 reference
# init script and common open-source drivers.

from machine import SPI, Pin
import utime
import config
from display.hal import DisplayHAL, WIDTH, HEIGHT, COLOR_BG


class ST7701SDisplay(DisplayHAL):

    def _hw_init(self):
        # ── GPIO setup ────────────────────────────────────────────────────────
        self._cs  = Pin(config.DISPLAY_CS,  Pin.OUT, value=1)
        self._dc  = Pin(config.DISPLAY_DC,  Pin.OUT, value=1)
        self._rst = Pin(config.DISPLAY_RST, Pin.OUT, value=1)

        # ── SPI bus ───────────────────────────────────────────────────────────
        # 40 MHz is within spec for ST7701S command bus; pixel DMA can go higher.
        self._spi = SPI(
            1,
            baudrate=40_000_000,
            polarity=0,
            phase=0,
            sck=Pin(config.SPI_SCLK),
            mosi=Pin(config.SPI_MOSI),
            miso=Pin(config.SPI_MISO),
        )

        # ── Hardware reset ────────────────────────────────────────────────────
        self._rst(0)
        utime.sleep_ms(10)
        self._rst(1)
        utime.sleep_ms(120)

        # ── Init sequence ─────────────────────────────────────────────────────
        self._init_sequence()
        print("[st7701s] panel init complete")

    def _cs_low(self):
        self._cs(0)

    def _cs_high(self):
        self._cs(1)

    def _write_cmd(self, cmd):
        self._dc(0)
        self._cs_low()
        self._spi.write(bytes([cmd]))
        self._cs_high()

    def _write_data(self, data):
        self._dc(1)
        self._cs_low()
        if isinstance(data, int):
            self._spi.write(bytes([data]))
        else:
            self._spi.write(bytes(data))
        self._cs_high()

    def _write_cmd_data(self, cmd, *args):
        self._write_cmd(cmd)
        for a in args:
            self._write_data(a)

    def _init_sequence(self):
        """
        ST7701S bring-up sequence.
        Page 0 (CMD2_BK0) for display timing; Page 1 (CMD2_BK1) for power;
        Page 3 (CMD2_BK3) for MIPI; back to CMD1 for MADCTL / COLMOD / display on.
        """
        # Enable CMD2, Bank 0
        self._write_cmd_data(0xFF, 0x77, 0x01, 0x00, 0x00, 0x10)

        # Display line setting: 480 lines (0x3B = 480/8 - 1 = 59)
        self._write_cmd_data(0xC0, 0x3B, 0x00)
        # Porch control
        self._write_cmd_data(0xC1, 0x0D, 0x02)
        # Inversion selection, pixel clock
        self._write_cmd_data(0xC2, 0x21, 0x08)
        # RGB/MIPI control
        self._write_cmd_data(0xCC, 0x10)

        # Positive gamma (14 bytes)
        self._write_cmd_data(0xB0,
            0x00, 0x11, 0x18, 0x0E, 0x11, 0x06,
            0x07, 0x08, 0x07, 0x22, 0x04, 0x12,
            0x0F, 0xAA)

        # Negative gamma (14 bytes)
        self._write_cmd_data(0xB1,
            0x00, 0x11, 0x19, 0x0E, 0x12, 0x07,
            0x08, 0x08, 0x08, 0x22, 0x04, 0x11,
            0x11, 0xA9)

        # Enable CMD2, Bank 1
        self._write_cmd_data(0xFF, 0x77, 0x01, 0x00, 0x00, 0x11)

        # VCOM amplitude
        self._write_cmd_data(0xB0, 0x60)
        # VGH
        self._write_cmd_data(0xB1, 0x30)
        # VGHS/VGLS
        self._write_cmd_data(0xB2, 0x87)
        # VGS/VSN
        self._write_cmd_data(0xB3, 0x80)
        # VOPH
        self._write_cmd_data(0xB5, 0x49)
        # VFP/VBP source
        self._write_cmd_data(0xB7, 0x85)
        # AVDD/AVEE
        self._write_cmd_data(0xB8, 0x21)
        # VREG1
        self._write_cmd_data(0xC1, 0x78)
        # VREG2
        self._write_cmd_data(0xC2, 0x78)

        utime.sleep_ms(20)

        # GIP 1
        self._write_cmd_data(0xE0, 0x00, 0x1B, 0x02)
        # GIP 2
        self._write_cmd_data(0xE1, 0x08, 0xA0, 0x00, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x44, 0x44)
        # GIP 3
        self._write_cmd_data(0xE2, 0x11, 0x11, 0x44, 0x44,
                              0xED, 0xA0, 0x00, 0x00, 0xEC, 0xA0, 0x00, 0x00)
        self._write_cmd_data(0xE3, 0x00, 0x00, 0x11, 0x11)
        self._write_cmd_data(0xE4, 0x44, 0x44)
        self._write_cmd_data(0xE5,
            0x0A, 0xE9, 0xD8, 0xA0, 0x0C, 0xEB, 0xD8, 0xA0,
            0x0E, 0xED, 0xD8, 0xA0, 0x10, 0xEF, 0xD8, 0xA0)
        self._write_cmd_data(0xE6, 0x00, 0x00, 0x11, 0x11)
        self._write_cmd_data(0xE7, 0x44, 0x44)
        self._write_cmd_data(0xE8,
            0x09, 0xE8, 0xD8, 0xA0, 0x0B, 0xEA, 0xD8, 0xA0,
            0x0D, 0xEC, 0xD8, 0xA0, 0x0F, 0xEE, 0xD8, 0xA0)
        self._write_cmd_data(0xEB, 0x02, 0x00, 0xE4, 0xE4, 0x88, 0x00, 0x40)
        self._write_cmd_data(0xEC, 0x3C, 0x00)
        self._write_cmd_data(0xED,
            0xAB, 0x89, 0x76, 0x54, 0x02, 0xFF, 0xFF, 0xFF,
            0xFF, 0xFF, 0xFF, 0x20, 0x45, 0x67, 0x98, 0xBA)

        # Back to CMD1
        self._write_cmd_data(0xFF, 0x77, 0x01, 0x00, 0x00, 0x00)

        # Color mode: 16-bit RGB565
        self._write_cmd_data(0x3A, 0x55)

        # Memory access control: BGR, row-col swap as needed for 480×480
        self._write_cmd_data(0x36, 0x00)

        # Sleep out
        self._write_cmd(0x11)
        utime.sleep_ms(120)

        # Display on
        self._write_cmd(0x29)
        utime.sleep_ms(20)

    def _hw_push_buffer(self):
        """
        Write full framebuffer to panel over SPI.
        Set column/page addresses for full 480×480 window, then bulk-write pixels.
        """
        # Column address set: 0..479
        self._write_cmd(0x2A)
        self._write_data([0x00, 0x00, 0x01, 0xDF])

        # Page address set: 0..479
        self._write_cmd(0x2B)
        self._write_data([0x00, 0x00, 0x01, 0xDF])

        # Memory write
        self._write_cmd(0x2C)
        self._dc(1)
        self._cs_low()
        # Write in 4KB chunks to avoid large stack allocations
        chunk = 4096
        buf = self._buf
        for offset in range(0, len(buf), chunk):
            self._spi.write(buf[offset:offset + chunk])
        self._cs_high()
