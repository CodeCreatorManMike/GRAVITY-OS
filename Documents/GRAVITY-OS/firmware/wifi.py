# wifi.py — WiFi connection with exponential backoff reconnect

import network
import utime
import config

_RETRY_BASE_MS = 1_000
_RETRY_MAX_MS  = 30_000
_CONNECT_TIMEOUT_MS = 20_000

_wlan = None


def _get_wlan():
    global _wlan
    if _wlan is None:
        _wlan = network.WLAN(network.STA_IF)
    return _wlan


def connect(ssid=None, password=None):
    """Connect to WiFi. Returns True on success, False on failure."""
    ssid     = ssid     or config.WIFI_SSID
    password = password or config.WIFI_PASSWORD

    wlan = _get_wlan()
    wlan.active(True)

    if wlan.isconnected():
        print("[wifi] already connected:", wlan.ifconfig()[0])
        return True

    print(f"[wifi] connecting to {ssid} ...")
    wlan.connect(ssid, password)

    deadline = utime.ticks_add(utime.ticks_ms(), _CONNECT_TIMEOUT_MS)
    while not wlan.isconnected():
        if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
            print("[wifi] connection timed out")
            return False
        utime.sleep_ms(200)

    ip = wlan.ifconfig()[0]
    print(f"[wifi] connected — IP {ip}")
    return True


def ensure_connected(ssid=None, password=None):
    """
    Blocking reconnect with exponential backoff.
    Returns once connected.  Call from main loop before using the network.
    """
    delay = _RETRY_BASE_MS
    attempt = 0
    while True:
        attempt += 1
        if connect(ssid, password):
            return
        print(f"[wifi] retry {attempt} in {delay}ms ...")
        utime.sleep_ms(delay)
        delay = min(delay * 2, _RETRY_MAX_MS)


def is_connected():
    wlan = _get_wlan()
    return wlan.isconnected()


def ip_address():
    wlan = _get_wlan()
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    return None


def disconnect():
    wlan = _get_wlan()
    wlan.disconnect()
    print("[wifi] disconnected")
