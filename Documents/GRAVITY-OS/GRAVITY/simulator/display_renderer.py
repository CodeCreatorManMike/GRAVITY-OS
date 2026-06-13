"""
display_renderer.py — Render pipeline stub.

Connects a layout (from layout_engine) to a display backend (from device_sim).
In production this runs on a loop: poll profile, build layout, render frame,
push to display, sleep.

NOT BUILT — placeholder showing the intended interface.
"""

import time
from PIL import Image


def render_loop(backend, profile, interval_seconds: float = 60.0) -> None:
    """
    Main render loop — NOT BUILT.

    Will:
    1. Load/refresh profile from profiles/
    2. Call layout_engine.build_layout(profile)
    3. For each screen in the layout, call its fn() to get a PIL image
    4. Push the current screen to backend.show()
    5. Handle touch events to advance/retreat the screen index
    6. Re-evaluate nudge engine every 15 min; inject A3 screen if needed
    7. Respect quiet hours from profile.schedule
    """
    raise NotImplementedError("Render loop not yet implemented")


def render_single(screen_fn, profile_dict) -> Image.Image:
    """
    Render a single screen synchronously. Used by tests and the Pygame sim.
    screen_fn: callable(profile_dict) → PIL.Image
    """
    return screen_fn(profile_dict)
