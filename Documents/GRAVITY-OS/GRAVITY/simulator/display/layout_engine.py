"""
layout_engine.py — Builds an ordered list of screen configs from a UserProfile.

Never hardcode layouts here. All data comes from the profile; this module
translates it into callable screen configs the simulator can render.

Screen order:
  A1 (ambient/clock) → A2 (morning brief) →
  one A4 per milestone → A5 (heatmap) → A7 (wind-down, after 22:00)
"""

import sys
import os
import time as _time
from datetime import date, datetime

# Ensure both project root and this directory are on the path so imports work
# whether this file is called directly or imported as a package module.
_HERE    = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.abspath(os.path.join(_HERE, "../.."))
# Insert project root first, then this directory — so local imports
# (screens) shadow any root-level stale copies while core/ remains findable.
for _p in (_PROJECT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.profile import UserProfile
from screens import (          # local import — matches gravity_sim.py style
    A1, A2, A3, A4, A5, A6, A7,
    B1, B2, B4, B5, B7,
    C1, C2, C4, C5, C7,
    get_direction,
)


def _days_remaining(profile: UserProfile) -> int:
    if not profile.cycle_end:
        return 180
    try:
        end = date.fromisoformat(profile.cycle_end)
        return max(0, (end - date.today()).days)
    except ValueError:
        return 180


def _nonneg_display(profile: UserProfile) -> list[str]:
    """Format non-negotiables as checklist items, capped at 5."""
    return [f"[ ] {n[:20].upper()}" for n in profile.non_negotiables[:5]]


def _focus_line(profile: UserProfile) -> str:
    """Short motivational focus line from profile data."""
    why = profile.goal.real_why
    if why:
        # Truncate to fit in curved label
        return f"> {why[:36].lower()}"
    return "> focus on what matters today."


def build_layout(profile: UserProfile, nudge_result: dict | None = None) -> list[dict]:
    """
    Build an ordered list of screen configs for a given profile.

    Each config:
        {
            "screen":  str,       # canonical ID e.g. "A1", "A4_1"
            "label":   str,       # human-readable label for HUD
            "fn":      callable,  # fn(profile_dict) → PIL.Image
        }

    profile_dict is passed through so screen lambdas can stay pure;
    in practice most data is already bound via closure.
    """
    direction   = get_direction(profile.model_dump())
    days_left   = _days_remaining(profile)
    pct         = profile.goal.likelihood_score
    nonneg      = _nonneg_display(profile)
    focus       = _focus_line(profile)
    task        = (profile.goal.statement[:28] or "Work on your goal").title()
    hour        = datetime.now().hour
    show_wind   = hour >= 22

    screens: list[dict] = []

    # ── A1 / B1 / C1 — Ambient ────────────────────────────────────────────────
    if direction == "A":
        screens.append({
            "screen": "A1",
            "label":  "A1  Ambient",
            "fn": lambda _p: A1(
                time=_time.strftime("%H:%M"),
                date=_time.strftime("%a %d %b %Y").upper(),
                streak=47,
            ),
        })
    elif direction == "B":
        screens.append({
            "screen": "B1",
            "label":  "B1  Ambient",
            "fn": lambda _p: B1(
                time=_time.strftime("%-H:%M"),
                date=datetime.now().strftime("%A %-d %B"),
                streak=47,
            ),
        })
    else:  # C
        screens.append({
            "screen": "C1",
            "label":  "C1  Ambient",
            "fn": lambda _p: C1(
                time=_time.strftime("%-H:%M"),
                date=datetime.now().strftime("%a %-d %b").lower(),
                streak=47,
            ),
        })

    # ── A2 / B2 / C2 — Morning brief ──────────────────────────────────────────
    if direction == "A":
        screens.append({
            "screen": "A2",
            "label":  "A2  Morning Brief",
            "fn": lambda _p: A2(
                task=task,
                nonneg=nonneg,
                focus=focus,
            ),
        })
    elif direction == "B":
        screens.append({
            "screen": "B2",
            "label":  "B2  Morning Brief",
            "fn": lambda _p: B2(
                task=task,
                nonneg=[n.replace("[ ] ", "").title() for n in nonneg],
                focus=focus.replace("> ", ""),
            ),
        })
    else:
        screens.append({
            "screen": "C2",
            "label":  "C2  Morning Brief",
            "fn": lambda _p: C2(
                task=task + ".",
                nonneg=" · ".join(n.replace("[ ] ", "").lower() for n in nonneg),
                focus=focus.replace("> ", "").capitalize(),
            ),
        })

    # ── A4 / B4 / C4 — One screen per milestone ───────────────────────────────
    milestones = profile.goal.milestone_structure or [profile.goal.statement]
    for i, milestone in enumerate(milestones[:3]):
        ms_label = milestone[:16].upper()
        if direction == "A":
            screens.append({
                "screen": f"A4_{i+1}",
                "label":  f"A4  {milestone[:24]}",
                "fn": (lambda _p, ml=ms_label, p2=pct, dl=days_left:
                       A4(pct=p2, label=ml, days_left=dl)),
            })
        elif direction == "B":
            screens.append({
                "screen": f"B4_{i+1}",
                "label":  f"B4  {milestone[:24]}",
                "fn": (lambda _p, ml=ms_label, p2=pct, dl=days_left:
                       B4(pct=p2, label=ml, days_left=dl)),
            })
        else:
            screens.append({
                "screen": f"C4_{i+1}",
                "label":  f"C4  {milestone[:24]}",
                "fn": (lambda _p, ml=ms_label, p2=pct, dl=days_left:
                       C4(pct=p2, label=ml, days_left=dl)),
            })

    # ── A5 / B5 / C5 — Heatmap ────────────────────────────────────────────────
    if direction == "A":
        screens.append({"screen": "A5", "label": "A5  Heatmap", "fn": lambda _p: A5()})
    elif direction == "B":
        screens.append({"screen": "B5", "label": "B5  Heatmap", "fn": lambda _p: B5()})
    else:
        screens.append({"screen": "C5", "label": "C5  Heatmap", "fn": lambda _p: C5()})

    # ── Nudge overlay (A3) — inserted only when nudge_result is live ──────────
    if nudge_result and nudge_result.get("nudge"):
        msg = nudge_result.get("message", "STAY ON TRACK")
        sub = nudge_result.get("sub_message") or ""
        # Fit message into A3's two big-text lines
        words = msg.upper().split()
        mid   = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:]) or sub.upper()
        screens.append({
            "screen": "A3_nudge",
            "label":  "A3  Nudge",
            "fn": lambda _p, l1=line1, l2=line2: A3(
                message=l1,
                sub=l2,
                alert="! GRAVITY NUDGE !",
                dismiss="TAP DISMISS",
            ),
        })

    # ── A7 / B7 / C7 — Wind-down (after 22:00) ────────────────────────────────
    if show_wind:
        sleep_h, sleep_m_str = profile.schedule.sleep_time.split(":")
        wake_h, wake_m_str   = profile.schedule.wake_time.split(":")
        # Simple sleep window estimate
        total_min = (int(sleep_h) - int(wake_h)) % 24 * 60 + (int(sleep_m_str) - int(wake_m_str))
        s_h = total_min // 60
        s_m = total_min % 60
        if direction == "A":
            screens.append({
                "screen": "A7",
                "label":  "A7  Wind-down",
                "fn": lambda _p: A7(
                    lights_out=profile.schedule.sleep_time,
                    in_min=max(0, (int(profile.schedule.sleep_time.split(":")[0])*60 +
                                   int(profile.schedule.sleep_time.split(":")[1])) -
                                  (hour*60 + datetime.now().minute)),
                    alarm=profile.schedule.wake_time,
                    sleep_h=s_h,
                    sleep_m=s_m,
                ),
            })
        elif direction == "B":
            screens.append({
                "screen": "B7",
                "label":  "B7  Wind-down",
                "fn": lambda _p: B7(alarm=profile.schedule.wake_time, sleep_h=s_h, sleep_m=s_m),
            })
        else:
            screens.append({
                "screen": "C7",
                "label":  "C7  Wind-down",
                "fn": lambda _p: C7(lights_out=profile.schedule.sleep_time),
            })

    return screens
