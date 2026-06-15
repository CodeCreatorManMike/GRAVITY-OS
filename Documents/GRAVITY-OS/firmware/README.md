# GRAVITY Firmware — ESP32-S3 MicroPython

Cloud display terminal firmware for the GRAVITY habit-tracking device.

---

## 1. Hardware for breadboard bring-up

| Part | Description |
|---|---|
| ESP32-S3-WROOM-1-N16R8 | Main MCU module (16 MB flash, 8 MB octal PSRAM) |
| ER-TFT028-2-6318 | 2.8" 480×480 round IPS eval display (LT7683 + ST7701S + GT911 touch) |
| LIS2DW12 breakout | 3-axis accelerometer, I2C |
| VEML7700 breakout | Ambient light sensor, I2C |
| MAX17048 breakout | Li-Po fuel gauge, I2C |
| 3.3 V regulator | For sensors if not already on breakout |
| USB-C cable | For UART/REPL and flashing |
| Breadboard + jumpers | — |

The display eval module (ER-TFT028-2-6318) comes with the LT7683 controller, GT911 touch, and SSD2828 bridge built in. It connects over 4-wire SPI.

---

## 2. Wiring guide

### SPI (display)

| ESP32-S3 GPIO | Signal | ER-TFT028 pin |
|---|---|---|
| GPIO 12 | SCLK | SCK |
| GPIO 11 | MOSI | SDI (MOSI) |
| GPIO 13 | MISO | SDO (MISO) |
| GPIO 10 | CS | CS |
| GPIO 9 | DC / RS | DC |
| GPIO 8 | RST | RST |
| 3.3 V | VCC | VCC |
| GND | GND | GND |

### I2C (all sensors share one bus)

| ESP32-S3 GPIO | Signal |
|---|---|
| GPIO 4 | SDA |
| GPIO 5 | SCL |

Connect SDA + SCL lines to:
- LIS2DW12 breakout (addr 0x18)
- VEML7700 breakout (addr 0x10)
- MAX17048 breakout (addr 0x36)
- GT911 touch (addr 0x5D) — if not already on the display module ribbon

### Touch interrupt / reset (eval module)

| ESP32-S3 GPIO | Signal |
|---|---|
| GPIO 6 | TOUCH_INT |
| GPIO 15 | TOUCH_RST |

### IMU interrupt

| ESP32-S3 GPIO | Signal |
|---|---|
| GPIO 16 | IMU_INT1 |

### Backlight PWM

| ESP32-S3 GPIO | Signal |
|---|---|
| GPIO 18 | BL_PWM (to display backlight enable or LED+ via resistor) |

### Power / USB

| ESP32-S3 GPIO | Signal |
|---|---|
| GPIO 19 | USB D- |
| GPIO 20 | USB D+ |
| GPIO 0 | BOOT (pull low to enter flash mode) |

> **PSRAM note**: GPIO 26–37 are used internally for octal PSRAM on the N16R8 module. Never route anything there.

---

## 3. Flash MicroPython to ESP32-S3

### 3a. Download firmware

Get the latest ESP32-S3 MicroPython firmware (SPIRAM variant, for the N16R8):

```
https://micropython.org/download/ESP32_GENERIC_S3/
```

Download the `.bin` file labelled **SPIRAM** (octal PSRAM / OPI variant).

### 3b. Install esptool

```bash
pip install esptool
```

### 3c. Enter download mode

Hold the **BOOT** button (GPIO 0) while pressing and releasing **RESET** (EN pin). Release BOOT after reset.

### 3d. Erase and flash

```bash
# Erase flash first
esptool.py --chip esp32s3 --port /dev/tty.usbserial-* erase_flash

# Flash MicroPython
esptool.py --chip esp32s3 --port /dev/tty.usbserial-* \
  --baud 921600 write_flash -z 0x0 \
  ESP32_GENERIC_S3-SPIRAM_OCT-20250101-v1.24.1.bin
```

Replace the port and filename with your actual values.

---

## 4. Configure `config.py`

Before uploading, edit `firmware/config.py`:

```python
WIFI_SSID     = "YourNetworkName"
WIFI_PASSWORD = "YourNetworkPassword"
BACKEND_HOST  = "192.168.1.100"   # IP or hostname of GRAVITY backend
BACKEND_PORT  = 8000
USER_ID       = "user-001"        # must match the user in the backend DB
INITIAL_JWT   = "eyJ..."          # paste the JWT from your backend /auth endpoint
DISPLAY_DRIVER = "lt7683"         # "lt7683" for eval, "st7701s" for production panel
TOUCH_DRIVER   = "gt911"          # "gt911" for eval, "cst816s" for production
```

---

## 5. Upload firmware files

### Using mpremote (recommended)

```bash
pip install mpremote

# Upload all files
cd firmware/
mpremote connect /dev/tty.usbserial-* cp boot.py        :boot.py
mpremote connect /dev/tty.usbserial-* cp main.py        :main.py
mpremote connect /dev/tty.usbserial-* cp config.py      :config.py
mpremote connect /dev/tty.usbserial-* cp wifi.py        :wifi.py
mpremote connect /dev/tty.usbserial-* cp websocket_client.py :websocket_client.py
mpremote connect /dev/tty.usbserial-* cp cache.py       :cache.py
mpremote connect /dev/tty.usbserial-* cp touch.py       :touch.py
mpremote connect /dev/tty.usbserial-* cp imu.py         :imu.py
mpremote connect /dev/tty.usbserial-* cp als.py         :als.py
mpremote connect /dev/tty.usbserial-* cp power.py       :power.py
mpremote connect /dev/tty.usbserial-* cp ota.py         :ota.py
mpremote connect /dev/tty.usbserial-* mkdir :display
mpremote connect /dev/tty.usbserial-* cp display/__init__.py  :display/__init__.py
mpremote connect /dev/tty.usbserial-* cp display/hal.py       :display/hal.py
mpremote connect /dev/tty.usbserial-* cp display/st7701s.py   :display/st7701s.py
mpremote connect /dev/tty.usbserial-* cp display/lt7683.py    :display/lt7683.py
mpremote connect /dev/tty.usbserial-* cp display/renderer.py  :display/renderer.py
mpremote connect /dev/tty.usbserial-* cp display/components.py :display/components.py
```

### Using rshell

```bash
pip install rshell
rshell --port /dev/tty.usbserial-* rsync firmware/ /pyboard/
```

### Using Thonny

Open each file in Thonny, choose **File → Save copy → MicroPython device**, matching the path.

---

## 6. What to expect in serial output

Connect a terminal at **115200 baud** to the USB serial port (or use `mpremote connect ... repl`).

Normal boot output:

```
[main] GRAVITY OS v0.1.0
[main] reset cause: power_on
[main] init display ...
[hal] display initialized
[lt7683] panel init complete
[main] init I2C ...
[touch] GT911 initialised
[imu] LIS2DW12 initialised
[als] backlight PWM on GPIO18
[als] VEML7700 initialised
[power] MAX17048 version: 0x0010
[main] battery: 87%
[main] connecting WiFi ...
[wifi] connecting to YourNetworkName ...
[wifi] connected — IP 192.168.1.42
[main] connecting WebSocket ...
[ws] connecting to ws://192.168.1.100:8000/ws/user-001?token=eyJ...
[ws] connected
[main] boot complete — entering main loop
[main] heartbeat sent
[ws] LAYOUT_UPDATE received
[cache] layout saved
[renderer] loaded 5 screens, direction=A
```

Gestures are logged:

```
[main] gesture=swipe_left x=380 y=240
[main] gesture=tap x=200 y=250
[main] habit completed: music
```

Deep sleep entry:

```
[main] idle 1800s — entering deep sleep
[imu] wake-on-motion configured
[power] entering deep sleep — wake on touch or motion
```

On wake from deep sleep, the device resets and reprints the boot banner with `reset cause: deepsleep_wake`.

---

## 7. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Display stays white | Wrong `DISPLAY_DRIVER` in config, or SPI wiring error. Check CS/DC/RST polarity. |
| "WHO_AM_I mismatch" on IMU | Wrong I2C address or wiring. Verify SDA/SCL continuity. |
| WebSocket loops "connect error" | Wrong `BACKEND_HOST` / `BACKEND_PORT`, or JWT expired. |
| `OSError: ENOMEM` on display init | MicroPython build without SPIRAM. Must use the SPIRAM_OCT variant. |
| Touch not responding | Check `TOUCH_DRIVER` in config; verify INT + RST wiring. |
| Screen blank after 5 min | Normal — backlight dimmed to 20%. Touch to wake. After 30 min, deep sleep. |
