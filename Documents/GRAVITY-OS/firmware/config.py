# config.py — EDIT THIS FILE BEFORE FLASHING
# All device-specific settings live here.

# ── WiFi ──────────────────────────────────────────────────────────────────────
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourNetworkPassword"

# ── Backend ───────────────────────────────────────────────────────────────────
# WebSocket endpoint.  Replace <host> with your server IP or hostname.
# JWT is loaded from cache at runtime; the value here is the fallback / initial token.
BACKEND_HOST = "192.168.1.100"
BACKEND_PORT = 8000
BACKEND_WS_PATH = "/ws/{user_id}"   # {user_id} substituted at runtime

# Initial JWT — overwritten in flash once auth completes.
# Leave empty if the backend issues tokens via a separate auth flow.
INITIAL_JWT = ""

# ── Device identity ───────────────────────────────────────────────────────────
DEVICE_ID = "gravity-device-001"
USER_ID = "user-001"

# ── Firmware version ──────────────────────────────────────────────────────────
FIRMWARE_VERSION = "0.1.0"

# ── Display ───────────────────────────────────────────────────────────────────
# Set to "lt7683" for eval board, "st7701s" for production panel.
DISPLAY_DRIVER = "lt7683"

# ── Touch ─────────────────────────────────────────────────────────────────────
# Set to "cst816s" for production, "gt911" for eval module.
TOUCH_DRIVER = "gt911"

# ── Backlight ─────────────────────────────────────────────────────────────────
BACKLIGHT_GPIO = 18       # PWM-capable spare GPIO
BACKLIGHT_ACTIVE = 60     # % duty cycle when active
BACKLIGHT_DIM = 20        # % duty cycle when idle >5 min

# ── Power / sleep timings ─────────────────────────────────────────────────────
IDLE_DIM_MS   = 5 * 60 * 1000    # 5 minutes → dim
IDLE_SLEEP_MS = 30 * 60 * 1000   # 30 minutes → deep sleep

# ── Heartbeat / refresh ───────────────────────────────────────────────────────
HEARTBEAT_INTERVAL_MS = 60 * 1000          # 60 s
LAYOUT_REFRESH_INTERVAL_MS = 15 * 60 * 1000  # 15 min

# ── I2C pins ──────────────────────────────────────────────────────────────────
I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 400_000

# ── SPI pins (display) ────────────────────────────────────────────────────────
SPI_SCLK = 12
SPI_MOSI = 11
SPI_MISO = 13
DISPLAY_CS  = 10
DISPLAY_DC  = 9
DISPLAY_RST = 8

# ── Touch pins ────────────────────────────────────────────────────────────────
TOUCH_INT = 6
TOUCH_RST = 15

# ── IMU ───────────────────────────────────────────────────────────────────────
IMU_INT = 16

# ── I2S ───────────────────────────────────────────────────────────────────────
I2S_BCLK = 1
I2S_WS   = 2
I2S_DIN  = 42   # microphone data in
I2S_DOUT = 41   # amplifier data out

# ── I2C device addresses ──────────────────────────────────────────────────────
ADDR_CST816S  = 0x15
ADDR_GT911    = 0x5D
ADDR_LIS2DW12 = 0x18
ADDR_VEML7700 = 0x10
ADDR_MAX17048 = 0x36
