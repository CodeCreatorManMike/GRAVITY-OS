"""
nudge_tester.py — CLI tool to fire nudge test scenarios against a profile.

Usage (from project root, venv active):
    python3 simulator/nudge_tester.py [profile_name]

Runs all 4 standard test scenarios (on-track, pending habits, no-progress,
cooldown) and prints the nudge result for each. Useful for validating prompts
without starting the full simulator.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.profile import UserProfile, load_profile
from core.nudge_engine import evaluate_nudge


def run_scenarios(profile: UserProfile) -> None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        _print = console.print
        _panel = lambda t: console.print(Panel(t, style="dim white", expand=False))
    except ImportError:
        _print = print
        _panel = lambda t: print(f"\n── {t} ──")

    scenarios = [
        {
            "name": "Scenario 1 — On track, no nudge expected",
            "params": {
                "habits_completed_today":    profile.non_negotiables,
                "habits_pending_today":      [],
                "steps_today":               7500,
                "sleep_last_night_hours":    7.5,
                "current_time":              "14:00",
                "days_since_goal_progress":  0,
                "non_negotiables_completed": profile.non_negotiables,
                "non_negotiables_pending":   [],
            },
        },
        {
            "name": "Scenario 2 — Pending habits, evening approaching",
            "params": {
                "habits_completed_today":    [],
                "habits_pending_today":      profile.non_negotiables,
                "steps_today":               800,
                "sleep_last_night_hours":    6.0,
                "current_time":              "19:30",
                "days_since_goal_progress":  2,
                "non_negotiables_completed": [],
                "non_negotiables_pending":   profile.non_negotiables,
            },
        },
        {
            "name": "Scenario 3 — No goal progress for 4 days",
            "params": {
                "habits_completed_today":    profile.non_negotiables[:1],
                "habits_pending_today":      profile.non_negotiables[1:],
                "steps_today":               3200,
                "sleep_last_night_hours":    5.5,
                "current_time":              "20:00",
                "days_since_goal_progress":  4,
                "non_negotiables_completed": profile.non_negotiables[:1],
                "non_negotiables_pending":   profile.non_negotiables[1:],
            },
        },
        {
            "name": "Scenario 4 — Cooldown active, should NOT nudge",
            "params": {
                "habits_completed_today":    [],
                "habits_pending_today":      profile.non_negotiables,
                "steps_today":               200,
                "sleep_last_night_hours":    4.0,
                "current_time":              "21:00",
                "cooldown_active":           True,
                "days_since_goal_progress":  5,
                "non_negotiables_completed": [],
                "non_negotiables_pending":   profile.non_negotiables,
            },
        },
    ]

    for s in scenarios:
        _panel(s["name"])
        result = evaluate_nudge(profile=profile, **s["params"])
        if result["nudge"]:
            _print(f"NUDGE FIRED")
            _print(f"  Category : {result['category']}")
            _print(f"  Intensity: {result['intensity']}")
            _print(f"  Message  : {result['message']}")
            if result.get("sub_message"):
                _print(f"  Sub      : {result['sub_message']}")
            _print(f"  Reason   : {result['reason']}")
        else:
            _print(f"  No nudge — {result['reason']}")
        _print("")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else None
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")

    if name:
        profile = load_profile(name, profiles_dir=profiles_dir)
    else:
        files = [f[:-5] for f in os.listdir(profiles_dir) if f.endswith(".json")]
        if not files:
            print("No profiles found. Run python3 run.py first.")
            sys.exit(1)
        profile = load_profile(files[0], profiles_dir=profiles_dir)

    if not profile:
        print(f"Profile '{name}' not found.")
        sys.exit(1)

    print(f"Testing nudge engine with profile: {profile.name}\n")
    run_scenarios(profile)
