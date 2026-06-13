"""
gravity_sim.py — Pygame device simulator for Gravity OS.

Controls:
  LEFT / RIGHT arrow  — previous / next screen
  Mouse click         — left-half = previous, right-half = next
  Mouse drag (≥40px)  — swipe left/right gesture
  N                   — fire a test nudge (uses real nudge engine if profile loaded)
  O                   — print onboarding hint (profile reload)
  R                   — force re-render current screen
  Q / ESC             — quit

The simulator watches profiles/ for changes and hot-reloads automatically.
"""

import pygame
import sys
import os
import json
import time

# Resolve paths regardless of cwd
_SIM_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.abspath(os.path.join(_SIM_DIR, "../.."))

# Insert project root first so core/ is findable, then sim dir so local
# imports (screens, layout_engine) shadow any root-level stale copies.
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, _SIM_DIR)

from PIL import Image
from screens import A1, A2, A3, A4, A5, A7

DISPLAY_SIZE = 480
DISC_SIZE    = 360
DISC_OFFSET  = (DISPLAY_SIZE - DISC_SIZE) // 2
BG_COLOUR    = (11, 11, 13)
FPS          = 30

# Drag threshold in pixels to count as a swipe
DRAG_THRESHOLD = 40


# ── Profile / layout loading ─────────────────────────────────────────────────

def load_profile_dict() -> dict | None:
    profiles_dir = os.path.join(_PROJECT_DIR, "profiles")
    try:
        files = [f for f in os.listdir(profiles_dir) if f.endswith(".json")]
        if files:
            with open(os.path.join(profiles_dir, files[0])) as f:
                return json.load(f)
    except Exception:
        pass
    return None


def load_profile_obj(profile_dict: dict | None):
    """Load a UserProfile pydantic object from raw dict."""
    if not profile_dict:
        return None
    try:
        from core.profile import UserProfile
        return UserProfile(**profile_dict)
    except Exception as e:
        print(f"  Profile load error: {e}")
        return None


def get_profiles_mtime() -> float:
    """Return mtime of the most recently modified profile file."""
    profiles_dir = os.path.join(_PROJECT_DIR, "profiles")
    try:
        files = [os.path.join(profiles_dir, f)
                 for f in os.listdir(profiles_dir) if f.endswith(".json")]
        if files:
            return max(os.path.getmtime(fp) for fp in files)
    except Exception:
        pass
    return 0.0


def build_screens(profile_dict, profile_obj, nudge_result=None):
    """
    Build the ordered screen list from the profile using layout_engine.
    Falls back to a hardcoded default list if the profile is missing.
    """
    if profile_obj:
        try:
            from layout_engine import build_layout
            screens = build_layout(profile_obj, nudge_result=nudge_result)
            # Convert {screen, label, fn} dicts to (label, fn) tuples for the renderer
            return [(sc["label"], sc["fn"]) for sc in screens]
        except Exception as e:
            print(f"  layout_engine error: {e}")

    # Fallback hardcoded list
    p = profile_dict
    return [
        ("A1  Ambient",   lambda _p: A1(time=time.strftime("%H:%M"),
                                         date=time.strftime("%a %d %b %Y").upper(),
                                         streak=47)),
        ("A2  Morning",   lambda _p: A2(
                                         task=(p["goal"]["statement"][:28] if p else "Work on your goal"),
                                         nonneg=[f"[ ] {n[:20].upper()}" for n in
                                                 (p.get("non_negotiables", []) if p else [])[:3]])),
        ("A3  Nudge",     lambda _p: A3()),
        ("A4  Goal",      lambda _p: A4(
                                         pct=(p["goal"]["likelihood_score"] if p else 0.6),
                                         label=(p["goal"]["statement"][:16].upper() if p else "GOAL"),
                                         days_left=180)),
        ("A5  Heatmap",   lambda _p: A5()),
        ("A7  Wind-down", lambda _p: A7()),
    ]


# ── Pygame helpers ────────────────────────────────────────────────────────────

def pil_to_surface(img: Image.Image) -> pygame.Surface:
    img = img.convert("RGB")
    return pygame.image.fromstring(img.tobytes(), img.size, "RGB")


def render_screen(fn, profile_dict) -> pygame.Surface | None:
    try:
        img = fn(profile_dict)
        if img.size[0] != DISC_SIZE:
            img = img.resize((DISC_SIZE, DISC_SIZE), Image.LANCZOS)
        return pil_to_surface(img)
    except Exception as e:
        print(f"  Render error: {e}")
        return None


def apply_circular_clip(surface: pygame.Surface) -> pygame.Surface:
    size   = surface.get_size()
    circle = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(circle, (255,255,255,255), (size[0]//2, size[1]//2), size[0]//2)
    result = pygame.Surface(size, pygame.SRCALPHA)
    result.blit(surface, (0,0))
    result.blit(circle,  (0,0), special_flags=pygame.BLEND_RGBA_MIN)
    return result


def fire_test_nudge(profile_obj) -> dict | None:
    """Call the real nudge engine with a test scenario."""
    if not profile_obj:
        return None
    try:
        from core.nudge_engine import evaluate_nudge
        result = evaluate_nudge(
            profile=profile_obj,
            habits_completed_today=[],
            habits_pending_today=profile_obj.non_negotiables,
            steps_today=800,
            sleep_last_night_hours=6.0,
            current_time=time.strftime("%H:%M"),
            days_since_goal_progress=3,
            non_negotiables_completed=[],
            non_negotiables_pending=profile_obj.non_negotiables,
        )
        return result
    except Exception as e:
        print(f"  Nudge engine error: {e}")
        return None


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Gravity — Device Simulator")
    win   = pygame.display.set_mode((DISPLAY_SIZE, DISPLAY_SIZE))
    clock = pygame.time.Clock()

    profile_dict  = load_profile_dict()
    profile_obj   = load_profile_obj(profile_dict)
    last_mtime    = get_profiles_mtime()
    nudge_result  = None

    screens      = build_screens(profile_dict, profile_obj, nudge_result)
    current_idx  = 0
    surface      = None
    needs_render = True
    last_time    = ""

    # Drag tracking
    drag_start_x   = None
    dragging       = False

    hud_font = pygame.font.SysFont("monospace", 11)

    print("Gravity Simulator ready.")
    print("Controls: LEFT/RIGHT = nav  Mouse L/R click = nav  N = nudge  O = onboard  R = refresh  Q = quit")
    if profile_obj:
        print(f"  Profile loaded: {profile_obj.name}  Direction: {__import__('screens').get_direction(profile_dict)}")

    while True:
        # ── Event handling ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()
                elif event.key == pygame.K_RIGHT:
                    current_idx = (current_idx + 1) % len(screens)
                    needs_render = True
                elif event.key == pygame.K_LEFT:
                    current_idx = (current_idx - 1) % len(screens)
                    needs_render = True
                elif event.key == pygame.K_r:
                    needs_render = True
                elif event.key == pygame.K_n:
                    print("  Firing test nudge...")
                    nudge_result = fire_test_nudge(profile_obj)
                    if nudge_result:
                        if nudge_result.get("nudge"):
                            print(f"  Nudge: {nudge_result.get('message')}")
                        else:
                            print(f"  No nudge — {nudge_result.get('reason')}")
                    # Rebuild screens with nudge and jump to nudge screen
                    screens = build_screens(profile_dict, profile_obj, nudge_result)
                    nudge_idx = next(
                        (i for i, (lbl, _) in enumerate(screens) if "Nudge" in lbl),
                        current_idx
                    )
                    current_idx  = nudge_idx
                    needs_render = True
                elif event.key == pygame.K_o:
                    print("  To re-run onboarding: quit this window and run: python3 run.py")
                    print("  Then relaunch the simulator — it will auto-load the new profile.")

            # Mouse click: left half = previous, right half = next
            if event.type == pygame.MOUSEBUTTONUP and not dragging:
                if event.button == 1:  # left click
                    mx, _ = event.pos
                    if mx < DISPLAY_SIZE // 2:
                        current_idx = (current_idx - 1) % len(screens)
                    else:
                        current_idx = (current_idx + 1) % len(screens)
                    needs_render = True

            # Drag/swipe
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                drag_start_x = event.pos[0]
                dragging     = False
            if event.type == pygame.MOUSEMOTION:
                if drag_start_x is not None:
                    if abs(event.pos[0] - drag_start_x) > DRAG_THRESHOLD:
                        dragging = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                dx = event.pos[0] - drag_start_x
                if dx < -DRAG_THRESHOLD:
                    current_idx = (current_idx + 1) % len(screens)
                    needs_render = True
                elif dx > DRAG_THRESHOLD:
                    current_idx = (current_idx - 1) % len(screens)
                    needs_render = True
                drag_start_x = None
                dragging     = False
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag_start_x = None

        # ── File watcher: hot-reload profiles ─────────────────────────────────
        mtime = get_profiles_mtime()
        if mtime > last_mtime:
            print("  Profile changed — reloading...")
            last_mtime    = mtime
            profile_dict  = load_profile_dict()
            profile_obj   = load_profile_obj(profile_dict)
            nudge_result  = None
            screens       = build_screens(profile_dict, profile_obj)
            current_idx   = min(current_idx, len(screens) - 1)
            needs_render  = True

        # ── Auto-refresh A1 clock every minute ────────────────────────────────
        now = time.strftime("%H:%M")
        name_0 = screens[0][0] if screens else ""
        if current_idx == 0 and "Ambient" in name_0 and now != last_time:
            last_time    = now
            needs_render = True

        # ── Render ────────────────────────────────────────────────────────────
        if needs_render and screens:
            label, fn    = screens[current_idx]
            surface      = render_screen(fn, profile_dict)
            needs_render = False
            print(f"  Screen: {label}")

        win.fill(BG_COLOUR)

        if surface:
            clipped = apply_circular_clip(surface)
            win.blit(clipped, (DISC_OFFSET, DISC_OFFSET))

        hud = hud_font.render(
            f"{current_idx+1}/{len(screens)}  {screens[current_idx][0] if screens else ''}",
            True, (60, 60, 66)
        )
        win.blit(hud, (10, DISPLAY_SIZE - 20))

        # Show nudge dot indicator
        if nudge_result and nudge_result.get("nudge"):
            pygame.draw.circle(win, (180, 60, 60), (DISPLAY_SIZE - 16, DISPLAY_SIZE - 14), 4)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
