"""
Context service — single source of truth for every AI call.

build_user_context(user_id, db, redis) returns the full context dict
defined in SOFTWARE_ARCH.md. It caches the result in Redis (1h TTL) and
is invalidated by habit completions and nudge fires so intra-day events
are always reflected.

build_nudge_state(ctx, now_hhmm, now_day) is a thin adapter that
transforms the context dict into the legacy format that core's
decide_nudge() and generate_nudge_content() were written to consume.
Core's build_user_state() is not called from the backend — it remains
as the Stage 0 / CLI entry point only.
"""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import redis.asyncio as aioredis

from backend.models.user import Goal, Habit, HabitLog, Nudge, NudgeSettings, User
from backend.models.integration import HealthData, BehaviourPattern

CONTEXT_TTL = 3600  # 1 hour


def _context_key(user_id: int) -> str:
    return f"context:{user_id}"


# ── Cache helpers ─────────────────────────────────────────────────────────────

async def get_cached_context(user_id: int, redis: aioredis.Redis) -> Optional[dict]:
    raw = await redis.get(_context_key(user_id))
    return json.loads(raw) if raw else None


async def set_cached_context(user_id: int, ctx: dict, redis: aioredis.Redis) -> None:
    await redis.setex(_context_key(user_id), CONTEXT_TTL, json.dumps(ctx))


async def invalidate_user_context(user_id: int, redis: aioredis.Redis) -> None:
    """Call after any intra-day event (habit complete, nudge sent) to force a rebuild."""
    await redis.delete(_context_key(user_id))


# ── Context builder ───────────────────────────────────────────────────────────

async def build_user_context(
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> dict:
    """
    Return the user's full AI context dict. Serves from Redis cache if warm;
    otherwise builds from DB and caches the result.
    """
    cached = await get_cached_context(user_id, redis)
    if cached is not None:
        return cached

    ctx = await _build_from_db(user_id, db, redis)
    await set_cached_context(user_id, ctx, redis)
    return ctx


async def _build_from_db(
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> dict:
    """Build the full context dict from live DB data."""

    # ── User row ──────────────────────────────────────────────────────────────
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise ValueError(f"User {user_id} not found")

    # ── Active goal ───────────────────────────────────────────────────────────
    goal_result = await db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.is_active == True)
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    goal = goal_result.scalar_one_or_none()

    # ── Active habits ─────────────────────────────────────────────────────────
    habits_result = await db.execute(
        select(Habit)
        .where(Habit.user_id == user_id, Habit.is_active == True)
        .order_by(Habit.created_at.asc())
    )
    habits = habits_result.scalars().all()

    # ── Today's completions ───────────────────────────────────────────────────
    today_str = str(date.today())
    completed_today_ids: set[int] = set()
    if habits:
        logs_result = await db.execute(
            select(HabitLog.habit_id).where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.date == today_str,
                    HabitLog.completed == True,
                    HabitLog.habit_id.in_([h.id for h in habits]),
                )
            )
        )
        completed_today_ids = {row[0] for row in logs_result.all()}

    habits_completed = [h.name for h in habits if h.id in completed_today_ids]
    habits_pending   = [h.name for h in habits if h.id not in completed_today_ids]
    nn_completed     = [h.name for h in habits if h.is_non_negotiable and h.id in completed_today_ids]
    nn_pending       = [h.name for h in habits if h.is_non_negotiable and h.id not in completed_today_ids]

    # ── Last 7 days habit completion ──────────────────────────────────────────
    # {habit_name: [bool×7]}, index 0 = 6 days ago, index 6 = today
    last_7_days: dict[str, list[bool]] = {}
    if habits:
        window_start = str(date.today() - timedelta(days=6))
        logs_7d_result = await db.execute(
            select(HabitLog.habit_id, HabitLog.date).where(
                and_(
                    HabitLog.user_id == user_id,
                    HabitLog.date >= window_start,
                    HabitLog.completed == True,
                    HabitLog.habit_id.in_([h.id for h in habits]),
                )
            )
        )
        completed_7d: set[tuple] = {(row[0], row[1]) for row in logs_7d_result.all()}
        date_window = [str(date.today() - timedelta(days=i)) for i in range(6, -1, -1)]
        for h in habits:
            last_7_days[h.name] = [(h.id, d) in completed_7d for d in date_window]

    # ── Nudge response rate (last 30 days) ────────────────────────────────────
    # Use a datetime object — sent_at is timestamptz, not varchar
    thirty_days_ago_dt = datetime.now(tz=timezone.utc) - timedelta(days=30)
    total_result = await db.execute(
        select(func.count()).select_from(Nudge).where(
            and_(Nudge.user_id == user_id, Nudge.sent_at >= thirty_days_ago_dt)
        )
    )
    total_nudges = total_result.scalar() or 0

    acked_result = await db.execute(
        select(func.count()).select_from(Nudge).where(
            and_(
                Nudge.user_id == user_id,
                Nudge.sent_at >= thirty_days_ago_dt,
                Nudge.acknowledged == True,
            )
        )
    )
    acked_nudges = acked_result.scalar() or 0
    nudge_response_rate = round(acked_nudges / total_nudges, 3) if total_nudges > 0 else 0.0

    # ── Last nudge + cooldown ─────────────────────────────────────────────────
    last_nudge_result = await db.execute(
        select(Nudge)
        .where(Nudge.user_id == user_id)
        .order_by(Nudge.sent_at.desc())
        .limit(1)
    )
    last_nudge = last_nudge_result.scalar_one_or_none()

    cooldown_key = f"nudge_cooldown:{user_id}"
    cooldown_active = bool(await redis.exists(cooldown_key))

    # ── Yesterday's health data (Apple Health) ────────────────────────────
    yesterday_str = str(date.today() - timedelta(days=1))
    health_result = await db.execute(
        select(HealthData).where(
            and_(
                HealthData.user_id == user_id,
                HealthData.date == yesterday_str,
            )
        )
    )
    health_yesterday = health_result.scalar_one_or_none()

    steps_yesterday = health_yesterday.steps if health_yesterday else 0
    sleep_hours = health_yesterday.sleep_hours if health_yesterday else 0.0
    sleep_quality = health_yesterday.sleep_quality if health_yesterday else "unknown"
    sleep_label = "unknown"
    if sleep_hours > 0:
        sleep_label = f"{sleep_hours:.1f}h ({sleep_quality})"

    # ── Active behaviour patterns ─────────────────────────────────────────
    patterns_result = await db.execute(
        select(BehaviourPattern.pattern).where(
            BehaviourPattern.user_id == user_id,
            BehaviourPattern.is_active == True,
        ).order_by(BehaviourPattern.confidence.desc()).limit(5)
    )
    active_patterns = [row[0] for row in patterns_result.all()]

    # ── NudgeSettings — real values, never baked-in defaults ─────────────────
    # If no row exists yet, surface the defaults without writing to DB;
    # the router creates the row on first /nudges/settings access.
    ns_result = await db.execute(
        select(NudgeSettings).where(NudgeSettings.user_id == user_id)
    )
    ns = ns_result.scalar_one_or_none()
    nudge_settings_dict = {
        "quiet_hours_start":    ns.quiet_hours_start    if ns else "22:00",
        "quiet_hours_end":      ns.quiet_hours_end      if ns else "08:00",
        "rest_days":            ns.rest_days            if ns else [],
        "sensitivity_habit":    ns.sensitivity_habit    if ns else 1.0,
        "sensitivity_focus":    ns.sensitivity_focus    if ns else 1.0,
        "sensitivity_fitness":  ns.sensitivity_fitness  if ns else 1.0,
        "sensitivity_sleep":    ns.sensitivity_sleep    if ns else 1.0,
        "sensitivity_spending": ns.sensitivity_spending if ns else 1.0,
    }

    # ── Cycle dates ───────────────────────────────────────────────────────────
    days_remaining = 0
    weeks_remaining = 0
    if goal and goal.cycle_end:
        try:
            delta = (date.fromisoformat(goal.cycle_end) - date.today()).days
            days_remaining = max(0, delta)
            weeks_remaining = days_remaining // 7
        except ValueError:
            pass

    # ── Known blockers = avoidance behaviours + risk factors, deduped ─────────
    avoidance = user.avoidance_behaviours or []
    risk = (goal.risk_factors if goal else []) or []
    known_blockers = list(dict.fromkeys(avoidance + risk))

    # ── Assemble ──────────────────────────────────────────────────────────────
    return {
        "profile": {
            "name": user.name,
            "personality_summary": user.personality_summary or "",
            "motivation_style": user.motivation_style or "",
            "energy_pattern": user.energy_pattern or "",
            "self_awareness_level": user.self_awareness_level or "",
            "failure_response": user.failure_response or "",
            "feedback_preference": user.feedback_preference or "direct",
            "schedule": {
                "wake_time": user.wake_time or "07:00",
                "sleep_time": user.sleep_time or "23:00",
                "peak_focus_windows": user.peak_focus_windows or [],
                "known_dead_zones": user.known_dead_zones or [],
                "realistic_daily_hours": float(user.realistic_daily_hours or 1.0),
                "avoidance_behaviours": avoidance,
            },
            "known_blockers": known_blockers,
        },
        "current_cycle": {
            "goal": goal.statement if goal else "",
            "real_why": goal.real_why if goal else "",
            "likelihood_score": float(goal.likelihood_score or 0.0) if goal else 0.0,
            "milestones": (goal.milestone_structure if goal else []) or [],
            "risk_factors": risk,
            "cycle_start": goal.cycle_start if goal else None,
            "cycle_end": goal.cycle_end if goal else None,
            "days_remaining": days_remaining,
            "weeks_remaining": weeks_remaining,
        },
        "today": {
            "date": today_str,
            "day_of_week": date.today().strftime("%A"),
            "habits_completed": habits_completed,
            "habits_pending": habits_pending,
            "non_negotiables_completed": nn_completed,
            "non_negotiables_pending": nn_pending,
            "schedule": [],  # placeholder — calendar events in future integration
        },
        "recent_behaviour": {
            "last_7_days_habit_completion": last_7_days,
            "nudge_response_rate": nudge_response_rate,
            "patterns_identified": active_patterns,
            "steps_yesterday": steps_yesterday,
            "sleep_last_night_hours": sleep_hours,
            "sleep_last_night": sleep_label,
        },
        "nudge_history": {
            "last_nudge_sent": (
                last_nudge.sent_at.isoformat()
                if last_nudge and last_nudge.sent_at else None
            ),
            "last_nudge_category": last_nudge.category if last_nudge else None,
            "cooldown_active": cooldown_active,
        },
        "nudge_settings": nudge_settings_dict,
    }


# ── Nudge state adapter ───────────────────────────────────────────────────────

def build_nudge_state(ctx: dict, now_hhmm: str, now_day: str) -> dict:
    """
    Transform the context dict into the exact format core's decide_nudge()
    and generate_nudge_content() consume.

    Mirrors the shape build_user_state() produced so those functions need
    no changes. core/nudge_engine.py's build_user_state() is kept for
    Stage 0 / CLI usage only and is never called from the backend.
    """
    profile = ctx["profile"]
    cycle = ctx["current_cycle"]
    today = ctx["today"]
    nudge_hist = ctx["nudge_history"]
    ns = ctx["nudge_settings"]

    all_nn = today["non_negotiables_completed"] + today["non_negotiables_pending"]

    return {
        "current_time": now_hhmm,
        "current_day": now_day,
        "user": {
            "name": profile["name"],
            "goal": cycle["goal"],
            "real_why": cycle["real_why"],
            "feedback_preference": profile["feedback_preference"],
            "energy_pattern": profile["energy_pattern"],
            "non_negotiables": all_nn,
            "wake_time": profile["schedule"]["wake_time"],
            "sleep_time": profile["schedule"]["sleep_time"],
            "peak_focus_windows": profile["schedule"]["peak_focus_windows"],
            "avoidance_behaviours": profile["schedule"]["avoidance_behaviours"],
            "likelihood_score": cycle["likelihood_score"],
            "risk_factors": cycle["risk_factors"],
        },
        "today": {
            "habits_completed": today["habits_completed"],
            "habits_pending": today["habits_pending"],
            "non_negotiables_completed": today["non_negotiables_completed"],
            "non_negotiables_pending": today["non_negotiables_pending"],
            "steps": ctx["recent_behaviour"]["steps_yesterday"],
            "sleep_last_night_hours": ctx["recent_behaviour"]["sleep_last_night_hours"],
            "days_since_goal_progress": 0,  # placeholder
        },
        "nudge_context": {
            "cooldown_active": nudge_hist["cooldown_active"],
            "last_nudge_category": nudge_hist["last_nudge_category"],
            # Real quiet hours from settings — never a hardcoded default.
            "quiet_hours": [f"{ns['quiet_hours_start']}-{ns['quiet_hours_end']}"],
        },
    }
