# main.py — GRAVITY OS boot sequence and main loop
# Version: 0.1.0
#
# Boot order:
#   1. UART hello
#   2. Load config / cache
#   3. Render boot screen
#   4. Init hardware (display, I2C, touch, IMU, ALS, power)
#   5. Connect WiFi
#   6. Connect WebSocket, register event handlers
#   7. Restore cached layout (no blank-wait)
#   8. Enter main loop

import utime
import machine
import config
import cache
import wifi
from websocket_client import WebSocketClient
from display.hal import DisplayHAL
from display.renderer import Renderer
import touch as touch_mod
import imu as imu_mod
import als as als_mod
import power as power_mod
import ota

# ── Version banner ────────────────────────────────────────────────────────────
print(f"[main] GRAVITY OS v{config.FIRMWARE_VERSION}")
print(f"[main] reset cause: {power_mod.Power().reset_cause()}")

# ── Global objects (initialised in boot sequence) ─────────────────────────────
_hal      = None
_renderer = None
_ws       = None
_touch    = None
_imu      = None
_als      = None
_power    = None

# ── Loop state ────────────────────────────────────────────────────────────────
_last_heartbeat_ms      = 0
_last_layout_refresh_ms = 0
_last_activity_ms       = 0     # timestamp of last touch or incoming message
_current_nudge_id       = None  # if a nudge is displayed


# ══════════════════════════════════════════════════════════════════════════════
# Event handlers (called by WebSocketClient._dispatch)
# ══════════════════════════════════════════════════════════════════════════════

def _on_layout_update(data):
    global _last_activity_ms
    print("[main] LAYOUT_UPDATE received")
    cache.save_layout(data)
    _renderer.load_layout(data)
    _last_activity_ms = utime.ticks_ms()
    _reset_backlight()


def _on_nudge(data):
    global _current_nudge_id, _last_activity_ms
    nudge_id = data.get("nudge_id")
    print(f"[main] NUDGE received id={nudge_id}")
    _current_nudge_id = nudge_id
    _renderer.show_nudge(data)
    _last_activity_ms = utime.ticks_ms()
    _reset_backlight()


def _on_heartbeat(data):
    # Echo it back immediately
    _ws.send_event("HEARTBEAT", {})


def _on_firmware_update(data):
    ver = data.get("version", "?")
    print(f"[main] FIRMWARE_UPDATE_AVAILABLE: {ver}")
    ota.check_and_apply(data)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _reset_backlight():
    if _als:
        _als.set_brightness(config.BACKLIGHT_ACTIVE)


def _handle_touch_gesture(gesture, x, y):
    global _current_nudge_id, _last_activity_ms

    _last_activity_ms = utime.ticks_ms()
    _reset_backlight()

    if gesture is None:
        return

    print(f"[main] gesture={gesture} x={x} y={y}")
    current = _renderer.current_screen()
    screen_type = current.get("type", "") if current else ""

    # Nudge dismiss
    if _renderer.is_nudge_active():
        if gesture in ("tap", "long_press", "swipe_left", "swipe_right"):
            if _current_nudge_id is not None:
                _ws.send_event("NUDGE_ACKNOWLEDGED", {"nudge_id": _current_nudge_id})
                _current_nudge_id = None
            _renderer.dismiss_nudge()
        return

    # Navigation
    if gesture == "swipe_left":
        _renderer.next_screen()
        _ws.send_event("TOUCH_EVENT", {"gesture": "swipe_left", "screen": screen_type})
        return

    if gesture in ("swipe_right", "long_press"):
        _renderer.prev_screen()
        _ws.send_event("TOUCH_EVENT", {"gesture": gesture, "screen": screen_type})
        return

    if gesture == "tap":
        _ws.send_event("TOUCH_EVENT", {"gesture": "tap", "screen": screen_type})
        # On A2: detect checklist tap → HABIT_COMPLETED
        if screen_type == "A2":
            _handle_a2_tap(x, y, current.get("data", {}))


def _handle_a2_tap(x, y, data):
    """
    Determine which checklist item was tapped on screen A2.
    Items are stacked vertically; approximate row from y position.
    """
    from display.components import _CHAR_H
    nonneg    = data.get("nonneg", [])
    completed = set(data.get("nonneg_completed", []))

    # Checklist starts around y=160 (after task text + divider), each row ~12px
    ITEM_H = (_CHAR_H + 4)   # matches draw_checklist_item spacing
    y_start = 160
    idx = (y - y_start) // ITEM_H
    if 0 <= idx < len(nonneg):
        habit = nonneg[idx]
        if habit not in completed:
            print(f"[main] habit completed: {habit}")
            cache.record_habit_completed(habit)
            _ws.send_event("HABIT_COMPLETED", {"habit_name": habit})
            # Update local data so the checkmark shows immediately
            data.setdefault("nonneg_completed", []).append(habit)
            _renderer.render_current()


# ══════════════════════════════════════════════════════════════════════════════
# Boot sequence
# ══════════════════════════════════════════════════════════════════════════════

def boot():
    global _hal, _renderer, _ws, _touch, _imu, _als, _power
    global _last_heartbeat_ms, _last_layout_refresh_ms, _last_activity_ms

    now = utime.ticks_ms()
    _last_heartbeat_ms      = now
    _last_layout_refresh_ms = now
    _last_activity_ms       = now

    # ── 1. Display init ───────────────────────────────────────────────────────
    print("[main] init display ...")
    try:
        _hal = DisplayHAL.create()
        _hal.init()
    except Exception as e:
        print(f"[main] FATAL: display init failed: {e}")
        # Cannot recover without display — reset after delay
        utime.sleep(5)
        machine.reset()

    _renderer = Renderer(_hal)

    # ── 2. Boot screen ────────────────────────────────────────────────────────
    _renderer.render_boot("STARTING...")

    # ── 3. I2C bus ────────────────────────────────────────────────────────────
    print("[main] init I2C ...")
    i2c = machine.I2C(0,
                      sda=machine.Pin(config.I2C_SDA),
                      scl=machine.Pin(config.I2C_SCL),
                      freq=config.I2C_FREQ)

    # ── 4. Peripheral drivers ─────────────────────────────────────────────────
    _touch = touch_mod.Touch()
    try:
        _touch.init(i2c)
    except Exception as e:
        print(f"[main] touch init error (non-fatal): {e}")
        _touch = None

    _imu = imu_mod.IMU()
    try:
        _imu.init(i2c)
    except Exception as e:
        print(f"[main] IMU init error (non-fatal): {e}")

    _als = als_mod.ALS()
    try:
        _als.init(i2c)
    except Exception as e:
        print(f"[main] ALS init error (non-fatal): {e}")

    _power = power_mod.Power()
    try:
        _power.init(i2c)
        batt = _power.battery_pct()
        if batt is not None:
            print(f"[main] battery: {batt}%")
    except Exception as e:
        print(f"[main] power init error (non-fatal): {e}")

    # ── 5. Load cached layout ─────────────────────────────────────────────────
    cached_layout = cache.load_layout()
    if cached_layout:
        print("[main] restoring cached layout ...")
        _renderer.load_layout(cached_layout)
    else:
        _renderer.render_boot("CONNECTING...")

    # ── 6. WiFi ───────────────────────────────────────────────────────────────
    print("[main] connecting WiFi ...")
    _renderer.render_boot("WIFI...")
    wifi.ensure_connected()
    _renderer.render_boot("CONNECTED")
    utime.sleep_ms(500)

    # ── 7. WebSocket ──────────────────────────────────────────────────────────
    print("[main] connecting WebSocket ...")
    _ws = WebSocketClient()

    # Set JWT from cache (or initial config token)
    jwt = cache.load_jwt() or config.INITIAL_JWT
    if jwt:
        _ws.set_token(jwt)
        cache.save_jwt(jwt)

    # Register event handlers
    _ws.register("LAYOUT_UPDATE",            _on_layout_update)
    _ws.register("NUDGE",                    _on_nudge)
    _ws.register("HEARTBEAT",                _on_heartbeat)
    _ws.register("FIRMWARE_UPDATE_AVAILABLE",_on_firmware_update)

    _ws.connect()

    # ── 8. Request fresh layout ───────────────────────────────────────────────
    # Send HEARTBEAT — backend will push LAYOUT_UPDATE in response.
    utime.sleep_ms(500)
    if _ws.is_connected():
        _ws.send_event("HEARTBEAT", {})
    elif cached_layout:
        # If WS fails but we have cache, still show cached layout
        _renderer.load_layout(cached_layout)
    else:
        _renderer.render_boot("WAITING...")

    print("[main] boot complete — entering main loop")


# ══════════════════════════════════════════════════════════════════════════════
# Main loop
# ══════════════════════════════════════════════════════════════════════════════

def main_loop():
    global _last_heartbeat_ms, _last_layout_refresh_ms, _last_activity_ms

    dimmed = False

    while True:
        now = utime.ticks_ms()

        # ── Poll WebSocket (non-blocking) ─────────────────────────────────────
        if _ws:
            _ws.poll()

        # ── Poll touch ────────────────────────────────────────────────────────
        if _touch and _touch.has_data():
            gesture, x, y = _touch.read()
            _handle_touch_gesture(gesture, x, y)

        # ── Heartbeat ─────────────────────────────────────────────────────────
        if utime.ticks_diff(now, _last_heartbeat_ms) >= config.HEARTBEAT_INTERVAL_MS:
            _last_heartbeat_ms = now
            if _ws and _ws.is_connected():
                _ws.send_event("HEARTBEAT", {})
                print("[main] heartbeat sent")

        # ── Layout refresh ────────────────────────────────────────────────────
        if utime.ticks_diff(now, _last_layout_refresh_ms) >= config.LAYOUT_REFRESH_INTERVAL_MS:
            _last_layout_refresh_ms = now
            if _ws and _ws.is_connected():
                _ws.send_event("HEARTBEAT", {})   # triggers server to push LAYOUT_UPDATE
                print("[main] layout refresh requested")

        # ── Idle management ───────────────────────────────────────────────────
        idle_ms = utime.ticks_diff(now, _last_activity_ms)

        if idle_ms >= config.IDLE_SLEEP_MS:
            print(f"[main] idle {idle_ms//1000}s — entering deep sleep")
            if _als:
                _als.backlight_off()
            if _power:
                _power.enter_deep_sleep(imu=_imu)
            # enter_deep_sleep does not return; if power module is unavailable:
            machine.deepsleep()

        elif idle_ms >= config.IDLE_DIM_MS:
            if not dimmed:
                dimmed = True
                if _als:
                    _als.set_brightness(config.BACKLIGHT_DIM)
                print("[main] backlight dimmed")
        else:
            if dimmed:
                dimmed = False
                if _als:
                    _als.set_brightness(config.BACKLIGHT_ACTIVE)

        utime.sleep_ms(50)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

try:
    boot()
    main_loop()
except Exception as e:
    import sys
    sys.print_exception(e)
    print("[main] UNHANDLED EXCEPTION — rebooting in 10s")
    utime.sleep(10)
    machine.reset()
