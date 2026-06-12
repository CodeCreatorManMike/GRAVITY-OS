import json
import os
from datetime import datetime
from core.ai_client import AIClient
from core.profile import UserProfile, load_profile

client = AIClient()


def load_prompt(filename: str) -> str:
    path = os.path.join("core", "prompts", filename)
    with open(path, "r") as f:
        return f.read()


def build_user_state(
    profile: UserProfile,
    habits_completed_today: list[str],
    habits_pending_today: list[str],
    steps_today: int = 0,
    sleep_last_night_hours: float = 0,
    current_time: str = None,
    last_nudge_category: str = None,
    cooldown_active: bool = False,
    quiet_hours: list[str] = None,
    days_since_goal_progress: int = 0,
    non_negotiables_completed: list[str] = None,
    non_negotiables_pending: list[str] = None
) -> dict:
    """
    Build the current state object that gets sent to the nudge engine.

    In production this will be assembled from live integration data:
    Apple Health for steps and sleep, calendar for schedule,
    habit logs from the app, screen time data etc.

    For Stage 0 testing we pass it in manually so we can simulate
    any scenario without needing real integrations yet.

    Every field here maps to a real data source that will feed it later.
    """
    return {
        "current_time": current_time or datetime.now().strftime("%H:%M"),
        "current_day": datetime.now().strftime("%A"),
        "user": {
            "name": profile.name,
            "goal": profile.goal.statement,
            "real_why": profile.goal.real_why,
            "feedback_preference": profile.feedback_preference,
            "energy_pattern": profile.energy_pattern,
            "non_negotiables": profile.non_negotiables,
            "wake_time": profile.schedule.wake_time,
            "sleep_time": profile.schedule.sleep_time,
            "peak_focus_windows": profile.schedule.peak_focus_windows,
            "avoidance_behaviours": profile.schedule.avoidance_behaviours,
            "likelihood_score": profile.goal.likelihood_score,
            "risk_factors": profile.goal.risk_factors,
        },
        "today": {
            "habits_completed": habits_completed_today,
            "habits_pending": habits_pending_today,
            "non_negotiables_completed": non_negotiables_completed or [],
            "non_negotiables_pending": non_negotiables_pending or profile.non_negotiables,
            "steps": steps_today,
            "sleep_last_night_hours": sleep_last_night_hours,
            "days_since_goal_progress": days_since_goal_progress,
        },
        "nudge_context": {
            "cooldown_active": cooldown_active,
            "last_nudge_category": last_nudge_category,
            "quiet_hours": quiet_hours or ["22:00-08:00"],
        }
    }


def decide_nudge(state: dict) -> dict:
    """
    Call 1 — Decision.
    Cheap, runs frequently. Answers yes or no: should a nudge be sent?
    Returns the decision dict with category, intensity, and reasoning.
    """
    system_prompt = load_prompt("nudge_decision.txt")

    messages = [{
        "role": "user",
        "content": f"Current user state:\n{json.dumps(state, indent=2)}"
    }]

    response = client.complete(system_prompt, messages, max_tokens=300)

    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        return {
            "should_nudge": False,
            "category": None,
            "intensity": None,
            "reason": "Decision parse failed",
            "data_points": []
        }


def generate_nudge_content(state: dict, decision: dict) -> dict:
    """
    Call 2 — Content.
    Only runs when decision says yes.
    Generates the actual message in the user's tone,
    personalised to their specific goal and current situation.
    """
    system_prompt = load_prompt("nudge_content.txt")

    messages = [{
        "role": "user",
        "content": (
            f"User state:\n{json.dumps(state, indent=2)}\n\n"
            f"Nudge decision:\n{json.dumps(decision, indent=2)}"
        )
    }]

    response = client.complete(system_prompt, messages, max_tokens=200)

    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        return {
            "message": "Time to make progress on your goal.",
            "sub_message": None,
            "action_label": "Dismiss",
            "display_duration_seconds": 30
        }


def evaluate_nudge(
    profile: UserProfile,
    habits_completed_today: list[str] = None,
    habits_pending_today: list[str] = None,
    steps_today: int = 0,
    sleep_last_night_hours: float = 0,
    current_time: str = None,
    last_nudge_category: str = None,
    cooldown_active: bool = False,
    days_since_goal_progress: int = 0,
    non_negotiables_completed: list[str] = None,
    non_negotiables_pending: list[str] = None
) -> dict:
    """
    Main entry point for the nudge engine.

    Takes a profile and current state, runs the two-call pipeline,
    returns the final nudge result or a no-nudge result.

    This is what the backend worker will call every 15 minutes per user.
    """
    state = build_user_state(
        profile=profile,
        habits_completed_today=habits_completed_today or [],
        habits_pending_today=habits_pending_today or [],
        steps_today=steps_today,
        sleep_last_night_hours=sleep_last_night_hours,
        current_time=current_time,
        last_nudge_category=last_nudge_category,
        cooldown_active=cooldown_active,
        days_since_goal_progress=days_since_goal_progress,
        non_negotiables_completed=non_negotiables_completed,
        non_negotiables_pending=non_negotiables_pending
    )

    decision = decide_nudge(state)

    if not decision.get("should_nudge"):
        return {
            "nudge": False,
            "reason": decision.get("reason", "No nudge needed"),
            "state_snapshot": state
        }

    content = generate_nudge_content(state, decision)

    return {
        "nudge": True,
        "category": decision["category"],
        "intensity": decision["intensity"],
        "reason": decision["reason"],
        "data_points": decision["data_points"],
        "message": content["message"],
        "sub_message": content.get("sub_message"),
        "action_label": content.get("action_label", "Dismiss"),
        "display_duration_seconds": content.get("display_duration_seconds", 30),
        "state_snapshot": state
    }


# ─────────────────────────────────────────────
# TEST SCENARIOS
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from rich.console import Console
    from rich.panel import Panel
    from rich.json import JSON

    console = Console()

    # Load the most recent profile
    profiles_dir = "profiles"
    files = [f for f in os.listdir(profiles_dir) if f.endswith(".json")]
    if not files:
        console.print("[red]No profiles found. Run python3 run.py first.[/red]")
        sys.exit(1)

    # Load first profile found
    with open(os.path.join(profiles_dir, files[0])) as f:
        data = json.load(f)
    profile = UserProfile(**data)

    console.print(f"\n[dim]Testing nudge engine with profile: {profile.name}[/dim]\n")

    # Define test scenarios that simulate different real-world situations
    # Each one tests a different nudge trigger
    scenarios = [
        {
            "name": "Scenario 1 — On track, no nudge needed",
            "params": {
                "habits_completed_today": profile.non_negotiables,
                "habits_pending_today": [],
                "steps_today": 7500,
                "sleep_last_night_hours": 7.5,
                "current_time": "14:00",
                "days_since_goal_progress": 0,
                "non_negotiables_completed": profile.non_negotiables,
                "non_negotiables_pending": []
            }
        },
        {
            "name": "Scenario 2 — Non-negotiables not done, evening approaching",
            "params": {
                "habits_completed_today": [],
                "habits_pending_today": profile.non_negotiables,
                "steps_today": 800,
                "sleep_last_night_hours": 6.0,
                "current_time": "19:30",
                "days_since_goal_progress": 2,
                "non_negotiables_completed": [],
                "non_negotiables_pending": profile.non_negotiables
            }
        },
        {
            "name": "Scenario 3 — No goal progress for 4 days",
            "params": {
                "habits_completed_today": profile.non_negotiables[:1],
                "habits_pending_today": profile.non_negotiables[1:],
                "steps_today": 3200,
                "sleep_last_night_hours": 5.5,
                "current_time": "20:00",
                "days_since_goal_progress": 4,
                "non_negotiables_completed": profile.non_negotiables[:1],
                "non_negotiables_pending": profile.non_negotiables[1:]
            }
        },
        {
            "name": "Scenario 4 — Cooldown active, should not nudge",
            "params": {
                "habits_completed_today": [],
                "habits_pending_today": profile.non_negotiables,
                "steps_today": 200,
                "sleep_last_night_hours": 4.0,
                "current_time": "21:00",
                "cooldown_active": True,
                "days_since_goal_progress": 5,
                "non_negotiables_completed": [],
                "non_negotiables_pending": profile.non_negotiables
            }
        }
    ]

    for scenario in scenarios:
        console.print(Panel(scenario["name"], style="dim white", expand=False))

        result = evaluate_nudge(profile=profile, **scenario["params"])

        if result["nudge"]:
            console.print(f"[bold white]NUDGE FIRED[/bold white]")
            console.print(f"Category : {result['category']}")
            console.print(f"Intensity: {result['intensity']}")
            console.print(f"Message  : [bold]{result['message']}[/bold]")
            if result["sub_message"]:
                console.print(f"Sub      : {result['sub_message']}")
            console.print(f"Action   : {result['action_label']}")
            console.print(f"Reason   : [dim]{result['reason']}[/dim]")
        else:
            console.print(f"[dim]No nudge — {result['reason']}[/dim]")

        console.print()
