"""
Layout service — generates the UI layout JSON for a user's device screen.
For now: rule-based layout derived from context. The AI seam is a
`use_ai` parameter left as a placeholder — when AI layout generation
is ready, point generate_layout() at the AI call instead.

Direction selection:
  feedback_preference="direct" or failure_response="analyse" → Direction A (Terminal)
  creative/artist profile → Direction C (Minimal Type) [future]
  default → Direction A for now (B/C screens not yet built in backend)
"""
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from backend.services.context_service import build_user_context


async def generate_layout(
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
    use_ai: bool = False,  # seam for future AI-generated layouts
) -> dict:
    """
    Return the layout instruction JSON for this user's device.
    Consumed by the device firmware renderer and the app's circular preview.
    """
    ctx = await build_user_context(user_id, db, redis)
    return _build_rule_based_layout(ctx)


def _select_direction(ctx: dict) -> str:
    """Choose visual direction from user profile. A=Terminal, B=Orbital, C=Minimal."""
    fp = ctx["profile"].get("feedback_preference", "")
    fr = ctx["profile"].get("failure_response", "")
    if fp == "direct" or fr == "analyse":
        return "A"
    return "A"  # B and C not yet built in backend — default to A


def _compute_streak(ctx: dict) -> int:
    """
    Count consecutive days where at least one non-negotiable was completed.
    Uses last_7_days_habit_completion from recent_behaviour.
    Counts backwards from yesterday (today is in progress).
    """
    completion = ctx["recent_behaviour"]["last_7_days_habit_completion"]
    if not completion:
        return 0

    # Each habit has a list of 7 bools, index 0=6 days ago, index 6=today
    # A day is "complete" if at least one non-negotiable was done
    nn_names = (
        ctx["today"]["non_negotiables_completed"] +
        ctx["today"]["non_negotiables_pending"]
    )

    streak = 0
    # Check days 5 down to 0 (yesterday back to 6 days ago), stop at first miss
    for day_index in range(5, -1, -1):  # 5=yesterday, 0=6 days ago
        day_done = any(
            completion.get(name, [False] * 7)[day_index]
            for name in nn_names
            if name in completion
        )
        if day_done:
            streak += 1
        else:
            break

    # Today counts if any nn completed today
    if ctx["today"]["non_negotiables_completed"]:
        streak += 1

    return streak


def _build_rule_based_layout(ctx: dict) -> dict:
    direction = _select_direction(ctx)
    cycle = ctx["current_cycle"]
    today = ctx["today"]
    profile = ctx["profile"]
    streak = _compute_streak(ctx)
    now_hour = datetime.now().hour

    screens = []

    # A1 — Ambient/Idle: always first
    screens.append({
        "type": "A1",
        "data": {
            "streak": streak,
        }
    })

    # A2 — Morning Brief: show if non-negotiables are pending
    pending = today["non_negotiables_pending"]
    completed = today["non_negotiables_completed"]
    if pending or completed:
        top_task = pending[0] if pending else cycle["goal"][:40]
        screens.append({
            "type": "A2",
            "data": {
                "task": top_task,
                "nonneg": pending + completed,
                "nonneg_completed": completed,
            }
        })

    # A4 — Goal Progress: one screen per active goal
    if cycle["goal"]:
        screens.append({
            "type": "A4",
            "data": {
                "pct": cycle["likelihood_score"],
                "label": cycle["goal"][:20].upper(),
                "days_left": cycle["days_remaining"],
                "milestones": cycle["milestones"][:3],
            }
        })

    # A5 — Weekly Heatmap: always include
    screens.append({
        "type": "A5",
        "data": {}
    })

    # A7 — Wind-down: only after 21:00
    if now_hour >= 21:
        sleep_time = profile["schedule"].get("sleep_time", "23:00")
        screens.append({
            "type": "A7",
            "data": {
                "lights_out": sleep_time,
                "tomorrow_task": pending[0] if pending else "",
            }
        })

    return {
        "direction": direction,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "screens": screens,
    }
