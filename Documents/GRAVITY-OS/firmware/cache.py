# cache.py — LittleFS-backed persistent state
#
# Stores: layout JSON, JWT, user name, today's goal/habits.
# All reads/writes are JSON over LittleFS (MicroPython VFS, built-in on ESP32-S3).

import ujson
import uos

_CACHE_DIR  = "/cache"
_LAYOUT_FILE = _CACHE_DIR + "/layout.json"
_STATE_FILE  = _CACHE_DIR + "/state.json"
_JWT_FILE    = _CACHE_DIR + "/jwt.txt"


def _ensure_dir():
    try:
        uos.mkdir(_CACHE_DIR)
    except OSError:
        pass  # already exists


def _read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except OSError:
        return None


def _write_file(path, text):
    _ensure_dir()
    with open(path, "w") as f:
        f.write(text)


# ── JWT ───────────────────────────────────────────────────────────────────────

def load_jwt():
    return _read_file(_JWT_FILE)


def save_jwt(token):
    _write_file(_JWT_FILE, token)
    print("[cache] JWT saved")


# ── Layout JSON ───────────────────────────────────────────────────────────────

def load_layout():
    """Return the cached layout dict or None."""
    raw = _read_file(_LAYOUT_FILE)
    if raw:
        try:
            return ujson.loads(raw)
        except ValueError:
            print("[cache] layout JSON corrupt — ignoring")
    return None


def save_layout(layout_dict):
    _write_file(_LAYOUT_FILE, ujson.dumps(layout_dict))
    print("[cache] layout saved")


# ── App state (name, goals, habits) ───────────────────────────────────────────

def _load_state():
    raw = _read_file(_STATE_FILE)
    if raw:
        try:
            return ujson.loads(raw)
        except ValueError:
            pass
    return {}


def _save_state(state):
    _write_file(_STATE_FILE, ujson.dumps(state))


def get(key, default=None):
    return _load_state().get(key, default)


def set(key, value):
    state = _load_state()
    state[key] = value
    _save_state(state)
    print(f"[cache] {key} = {value}")


def get_habit_history():
    """Return dict of {habit_name: [bool x 7]} — 7 days, index 0 = oldest."""
    return _load_state().get("habit_history", {})


def record_habit_completed(habit_name):
    """Mark today (index 6) as completed for habit_name."""
    state  = _load_state()
    hh     = state.get("habit_history", {})
    days   = hh.get(habit_name, [False] * 7)
    days[6] = True
    hh[habit_name] = days
    state["habit_history"] = hh
    _save_state(state)
    print(f"[cache] habit completed: {habit_name}")


def advance_day():
    """
    Shift all habit history one day left (call at midnight / on wake after sleep).
    Oldest entry drops off, today (index 6) resets to False.
    """
    state = _load_state()
    hh    = state.get("habit_history", {})
    for name in hh:
        days = hh[name]
        hh[name] = days[1:] + [False]
    state["habit_history"] = hh
    _save_state(state)
    print("[cache] day advanced")
