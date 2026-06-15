"""
Boot animation — terminal-style line-by-line reveal.

Runs before WiFi connect. Uses only the display HAL and components module
so it works with any display driver. The animation plays once and returns.

Sequence (mimics a real system boot):
  GRAVITY OS v0.1.0
  ──────────────────
  INIT DISPLAY      [OK]
  INIT TOUCH        [OK]
  INIT IMU          [OK]
  INIT ALS          [OK]
  INIT CACHE        [OK]
  ──────────────────
  CONNECTING WIFI...
"""

import utime

# Column positions for the 480px wide display (monospace font ~10px per char)
LEFT_MARGIN = 60
LINE_HEIGHT = 32
START_Y = 100
OK_X = 340

INK_RGB565 = 0x1082      # #14130D approximation in RGB565
PAPER_RGB565 = 0xF7F5    # #F4F2EA approximation in RGB565


def run(hal, components, version: str = "0.1.0"):
    """
    Play the boot animation on the given HAL instance.

    Args:
        hal: DisplayHAL instance (already initialised)
        components: the display.components module
        version: firmware version string
    """
    hal.fill_rect(0, 0, 480, 480, PAPER_RGB565)

    lines = []
    y = START_Y

    def add_line(text: str, right_text: str = "", delay_ms: int = 60):
        lines.append((y, text, right_text, delay_ms))

    add_line(f"GRAVITY OS v{version}", delay_ms=0)
    add_line("─" * 22, delay_ms=40)           # ─────────────────────────
    add_line("INIT DISPLAY",  "[OK]", delay_ms=80)
    add_line("INIT TOUCH",    "[OK]", delay_ms=80)
    add_line("INIT IMU",      "[OK]", delay_ms=80)
    add_line("INIT ALS",      "[OK]", delay_ms=80)
    add_line("INIT CACHE",    "[OK]", delay_ms=80)
    add_line("─" * 22, delay_ms=40)
    add_line("CONNECTING WIFI...", delay_ms=120)

    current_y = START_Y
    for (_, text, right_text, delay_ms) in lines:
        components.draw_text(hal, LEFT_MARGIN, current_y, text, INK_RGB565, scale=1)
        if right_text:
            components.draw_text(hal, OK_X, current_y, right_text, INK_RGB565, scale=1)
        hal.show()
        if delay_ms:
            utime.sleep_ms(delay_ms)
        current_y += LINE_HEIGHT

    # Hold the last frame briefly
    utime.sleep_ms(200)


def show_wifi_connected(hal, components, ssid: str = ""):
    """Replace the last line with 'WIFI OK' after successful connect."""
    y = START_Y + LINE_HEIGHT * 8  # position of the CONNECTING line
    hal.fill_rect(LEFT_MARGIN, y, 360, LINE_HEIGHT, PAPER_RGB565)
    msg = f"WIFI OK  {ssid[:16]}" if ssid else "WIFI OK"
    components.draw_text(hal, LEFT_MARGIN, y, msg, INK_RGB565, scale=1)
    components.draw_text(hal, OK_X, y, "[OK]", INK_RGB565, scale=1)
    hal.show()
    utime.sleep_ms(400)


def show_wifi_failed(hal, components):
    """Show 'WIFI FAIL — OFFLINE MODE' if WiFi can't connect."""
    y = START_Y + LINE_HEIGHT * 8
    hal.fill_rect(LEFT_MARGIN, y, 360, LINE_HEIGHT, PAPER_RGB565)
    components.draw_text(hal, LEFT_MARGIN, y, "WIFI FAIL  OFFLINE MODE", INK_RGB565, scale=1)
    components.draw_text(hal, OK_X, y, "[!!]", INK_RGB565, scale=1)
    hal.show()
    utime.sleep_ms(1000)
