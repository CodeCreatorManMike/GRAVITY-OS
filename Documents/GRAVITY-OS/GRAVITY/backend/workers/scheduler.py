"""
Scheduled jobs:
  - Every 15 min: evaluate nudges for all users with active goals
  - 02:00 daily: rebuild context cache for all active users
Both jobs share the same gate logic as POST /nudges/evaluate.
The 15-min job skips users that are in cooldown, quiet hours, or rest days.
"""
import asyncio
from datetime import datetime, date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.database import AsyncSessionLocal
from backend.config import get_settings
from backend.models.user import User, Goal
import redis.asyncio as aioredis
from sqlalchemy import select

settings = get_settings()
scheduler = AsyncIOScheduler()


def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


@scheduler.scheduled_job('interval', minutes=15, id='nudge_evaluation')
async def scheduled_nudge_evaluation():
    """
    For each user with an active goal, run the nudge evaluation pipeline.
    Respects all gate rules — this is the same path as POST /nudges/evaluate.
    """
    redis = _get_redis()
    now = datetime.now()
    now_hhmm = now.strftime("%H:%M")
    today_str = str(date.today())
    weekday_name = now.strftime("%A")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User.id).join(Goal, Goal.user_id == User.id)
            .where(Goal.is_active == True, User.is_active == True)
            .distinct()
        )
        user_ids = [row[0] for row in result.all()]

    for user_id in user_ids:
        try:
            await _evaluate_for_user(user_id, now_hhmm, today_str, weekday_name, redis)
        except Exception as e:
            print(f"[scheduler] nudge eval failed for user {user_id}: {e}")
        # Small delay between users to avoid hammering Groq rate limits
        await asyncio.sleep(2)


async def _evaluate_for_user(
    user_id: int,
    now_hhmm: str,
    today_str: str,
    weekday_name: str,
    redis: aioredis.Redis,
):
    """Run the full nudge evaluation for one user. Same logic as the REST endpoint."""
    from backend.services.context_service import build_user_context, build_nudge_state, invalidate_user_context
    from backend.services.connection_manager import manager
    from core.nudge_engine import decide_nudge, generate_nudge_content
    from backend.models.user import Nudge, NudgeSettings
    from backend.routers.nudges import _in_quiet_hours

    # Gate checks
    cooldown_key = f"nudge_cooldown:{user_id}"
    daily_key = f"nudge_daily:{user_id}:{today_str}"

    if await redis.exists(cooldown_key):
        return

    daily_count = await redis.get(daily_key)
    if daily_count and int(daily_count) >= 3:
        return

    async with AsyncSessionLocal() as db:
        ctx = await build_user_context(user_id, db, redis)
        ns = ctx["nudge_settings"]

        if _in_quiet_hours(now_hhmm, ns["quiet_hours_start"], ns["quiet_hours_end"]):
            return

        if weekday_name in (ns["rest_days"] or []):
            return

        state = build_nudge_state(ctx, now_hhmm, weekday_name)

        def _run():
            decision = decide_nudge(state)
            if not decision.get("should_nudge"):
                return None
            content = generate_nudge_content(state, decision)
            return {"decision": decision, "content": content}

        result = await asyncio.wait_for(asyncio.to_thread(_run), timeout=30.0)
        if result is None:
            return

        decision = result["decision"]
        content = result["content"]

        nudge_row = Nudge(
            user_id=user_id,
            category=decision.get("category") or "",
            intensity=decision.get("intensity") or "ambient",
            tone=ctx["profile"]["feedback_preference"] or "direct",
            message=content.get("message") or "",
            sub_message=content.get("sub_message") or "",
            action_label=content.get("action_label") or "Dismiss",
            reason=decision.get("reason") or "",
            acknowledged=False,
        )
        db.add(nudge_row)
        await db.flush()
        await db.refresh(nudge_row)

        cooldown_minutes = max(90, decision.get("cooldown_after", 90))
        await redis.setex(cooldown_key, cooldown_minutes * 60, "1")

        count = await redis.incr(daily_key)
        if count == 1:
            await redis.expire(daily_key, 86400)

        await invalidate_user_context(user_id, redis)

        nudge_payload = {
            "id": nudge_row.id,
            "category": nudge_row.category,
            "intensity": nudge_row.intensity,
            "message": nudge_row.message,
            "sub_message": nudge_row.sub_message or None,
            "action_label": nudge_row.action_label,
            "sent_at": nudge_row.sent_at.isoformat(),
        }
        await manager.send_to_user(user_id, "NUDGE", nudge_payload)

        if not manager.is_connected(user_id):
            from backend.services.push_service import send_push_if_offline
            await send_push_if_offline(
                user_id,
                title="GRAVITY",
                body=nudge_row.message,
                data=nudge_payload,
                db=db,
            )


@scheduler.scheduled_job('cron', hour=2, minute=0, id='context_rebuild')
async def nightly_context_rebuild():
    """
    02:00 daily: rebuild context cache for all active users.
    Deletes the Redis key — it gets rebuilt on next access.
    """
    redis = _get_redis()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User.id).where(User.is_active == True)
        )
        user_ids = [row[0] for row in result.all()]

    from backend.services.context_service import invalidate_user_context
    for user_id in user_ids:
        await invalidate_user_context(user_id, redis)

    print(f"[scheduler] nightly rebuild: cleared context for {len(user_ids)} users")


@scheduler.scheduled_job('cron', hour=2, minute=30, id='pattern_detection')
async def nightly_pattern_detection():
    """
    02:30 daily: run behavioural pattern detection for all active users.
    Runs after context_rebuild so patterns are fresh when context is rebuilt.
    """
    from backend.services.pattern_service import run_pattern_detection
    redis = _get_redis()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User.id).where(User.is_active == True)
        )
        user_ids = [row[0] for row in result.all()]

    for user_id in user_ids:
        try:
            async with AsyncSessionLocal() as db:
                patterns = await run_pattern_detection(user_id, db, redis)
                await db.commit()
            print(f"[scheduler] patterns for user {user_id}: {len(patterns)} detected")
        except Exception as e:
            print(f"[scheduler] pattern detection failed for user {user_id}: {e}")
        await asyncio.sleep(1)


@scheduler.scheduled_job('cron', hour=9, minute=0, id='cycle_trigger')
async def daily_cycle_trigger():
    """
    09:00 daily: check if any active goal cycle has ended and notify user.
    Sends a CYCLE_REVIEW_READY WebSocket event if cycle_end <= today.
    """
    from backend.services.connection_manager import manager
    today_str = str(date.today())

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Goal.user_id, Goal.id, Goal.cycle_end)
            .where(Goal.is_active == True)
            .where(Goal.cycle_end != "")
            .where(Goal.cycle_end <= today_str)
        )
        ending_cycles = result.all()

    for user_id, goal_id, cycle_end in ending_cycles:
        print(f"[scheduler] cycle ended for user {user_id} (goal {goal_id}, end {cycle_end})")
        await manager.send_to_user(user_id, "CYCLE_REVIEW_READY", {
            "goal_id": goal_id,
            "cycle_end": cycle_end,
        })
