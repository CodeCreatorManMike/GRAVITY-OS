"""
Layout service — generates the ranked face list for a user's device.

AI path (default): Claude picks and ranks up to 5 faces from the typed schema,
returning a JSON array. Rule-based fallback fires if Claude is unavailable.

Each face payload conforms to backend/schemas/face.py — firmware renderers
are statically typed and will reject unknown fields.
"""
from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from backend.config import get_settings
from backend.services.context_service import build_user_context
from backend.schemas.face import (
    GoalArcFace, TaskListFace, HabitHeatmapFace, TimerFace, StudyProgressFace,
    FaceCard, FACE_TYPES,
)

settings = get_settings()

# ── Public entry point ────────────────────────────────────────────────────────

async def generate_layout(
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> dict:
    """Return the layout JSON for the user's device (max 5 faces, AI-ranked)."""
    ctx = await build_user_context(user_id, db, redis)

    # Respect user-pinned face type order if set
    prefs_raw = await redis.get(f"face_prefs:{user_id}")
    pinned: list[str] | None = json.loads(prefs_raw) if prefs_raw else None

    try:
        faces = await _ai_ranked_faces(ctx, pinned_types=pinned)
    except Exception as e:
        print(f"[layout] AI ranking failed, using rule-based fallback: {e}")
        faces = _rule_based_faces(ctx)

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "faces": [f.model_dump() for f in faces],
    }


# ── AI ranking ────────────────────────────────────────────────────────────────

_FACE_SCHEMA_HINT = """
Available face types and their required fields:
- goal_arc:       label(str), pct(0-100), days_left(int), on_track(bool), sub_label(str)
- task_list:      tasks([{title,done,active}] max 6), done_count, total_count, next_label
- habit_heatmap:  habits([{name, days:[7 bools]}] max 5), streak(int), week_label
- timer:          label, duration_seconds, remaining_seconds, running(bool)
- study_progress: subject, pct(0-100), current_lesson, total_lessons, target_grade, streak_days

Return a JSON array of up to 5 face objects, most important first. Each object must have a "type" field.
Return ONLY the JSON array, no other text.
"""


async def _ai_ranked_faces(ctx: dict, pinned_types: list[str] | None = None) -> list[FaceCard]:
    import anthropic

    profile = ctx.get("profile", {})
    cycle = ctx.get("current_cycle", {})
    today = ctx.get("today", {})
    behaviour = ctx.get("recent_behaviour", {})

    # Summarise context tightly for the prompt
    context_summary = {
        "name": profile.get("name", "User"),
        "goal": cycle.get("goal", ""),
        "goal_pct": cycle.get("likelihood_score", 0),
        "days_left": cycle.get("days_remaining", 0),
        "pending_tasks": today.get("non_negotiables_pending", []),
        "completed_tasks": today.get("non_negotiables_completed", []),
        "streak": behaviour.get("streak_days", 0),
        "habits": [
            {"name": h, "completions_this_week": sum(v[-7:]) if isinstance(v, list) else 0}
            for h, v in behaviour.get("last_7_days_habit_completion", {}).items()
        ][:5],
        "hour": datetime.now().hour,
    }

    if pinned_types:
        type_constraint = (
            f"The user has pinned these face types in this exact order: {pinned_types}. "
            "You MUST produce faces for exactly these types in exactly this order. "
            "Fill in the content fields based on context."
        )
    else:
        type_constraint = (
            "Pick the faces that will be most useful RIGHT NOW based on context. Max 5, min 1. "
            "Always include goal_arc if there is an active goal. Include task_list if there are pending tasks."
        )

    system = f"""You are selecting and building the device faces for {profile.get('name', 'a user')}'s Gravity device.
{_FACE_SCHEMA_HINT}
{type_constraint}"""

    user_msg = f"User context:\n{json.dumps(context_summary, indent=2)}\n\nReturn the face array."

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = await asyncio.to_thread(
        lambda: client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    face_dicts: list[dict] = json.loads(raw)
    return _validate_faces(face_dicts, ctx)[:5]


def _validate_faces(face_dicts: list[dict], ctx: dict) -> list[FaceCard]:
    """Parse and validate AI-returned face dicts. Drop malformed ones silently."""
    faces: list[FaceCard] = []
    for d in face_dicts:
        ftype = d.get("type")
        try:
            if ftype == "goal_arc":
                faces.append(GoalArcFace(**d))
            elif ftype == "task_list":
                faces.append(TaskListFace(**d))
            elif ftype == "habit_heatmap":
                faces.append(HabitHeatmapFace(**d))
            elif ftype == "timer":
                faces.append(TimerFace(**d))
            elif ftype == "study_progress":
                faces.append(StudyProgressFace(**d))
        except Exception as e:
            print(f"[layout] invalid face {ftype}: {e}")
    return faces if faces else _rule_based_faces(ctx)


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _compute_streak(ctx: dict) -> int:
    completion = ctx["recent_behaviour"].get("last_7_days_habit_completion", {})
    if not completion:
        return 0
    today_ctx = ctx.get("today", {})
    nn_names = today_ctx.get("non_negotiables_completed", []) + today_ctx.get("non_negotiables_pending", [])
    streak = 0
    for day_index in range(5, -1, -1):
        day_done = any(
            completion.get(name, [False] * 7)[day_index]
            for name in nn_names if name in completion
        )
        if day_done:
            streak += 1
        else:
            break
    if today_ctx.get("non_negotiables_completed"):
        streak += 1
    return streak


def _rule_based_faces(ctx: dict) -> list[FaceCard]:
    faces: list[FaceCard] = []
    cycle = ctx.get("current_cycle", {})
    today = ctx.get("today", {})
    behaviour = ctx.get("recent_behaviour", {})
    streak = _compute_streak(ctx)

    # Goal arc — always first if active goal
    if cycle.get("goal"):
        faces.append(GoalArcFace(
            label=cycle["goal"][:24].upper(),
            pct=float(cycle.get("likelihood_score", 0)),
            days_left=int(cycle.get("days_remaining", 0)),
            on_track=cycle.get("likelihood_score", 0) >= 50,
        ))

    # Task list — if pending tasks exist
    pending = today.get("non_negotiables_pending", [])
    completed = today.get("non_negotiables_completed", [])
    if pending or completed:
        tasks = [
            {"title": t[:40], "done": False, "active": i == 0}
            for i, t in enumerate(pending[:4])
        ] + [
            {"title": t[:40], "done": True, "active": False}
            for t in completed[:2]
        ]
        faces.append(TaskListFace(
            tasks=tasks,
            done_count=len(completed),
            total_count=len(pending) + len(completed),
            next_label=f"NEXT: {pending[0][:28]}" if pending else "ALL CLEAR",
        ))

    # Habit heatmap — always include
    habit_rows = []
    for name, days in list(behaviour.get("last_7_days_habit_completion", {}).items())[:5]:
        bools = days[-7:] if isinstance(days, list) else [False] * 7
        habit_rows.append({"name": name[:20], "days": bools})
    if habit_rows:
        faces.append(HabitHeatmapFace(habits=habit_rows, streak=streak))

    return faces[:5] if faces else [
        GoalArcFace(label="SET A GOAL", pct=0, days_left=0, on_track=False)
    ]
