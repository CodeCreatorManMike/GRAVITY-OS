"""
Pattern service — nightly behavioural pattern detection.

Reads the last 30 days of habit + health data for a user and produces
plain-English pattern descriptions that are stored in behaviour_patterns
and surfaced in the AI context as patterns_identified.

Called by the nightly scheduler. Not called during nudge evaluation
(patterns are pre-computed and read from DB, never inline).
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as aioredis

from backend.models.user import User, Habit, HabitLog
from backend.models.integration import HealthData, BehaviourPattern
from backend.services.context_service import invalidate_user_context


async def run_pattern_detection(
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> list[str]:
    """
    Detect behavioural patterns for one user and upsert BehaviourPattern rows.
    Returns list of active pattern strings (for context injection).
    """
    today = date.today()
    window_start = today - timedelta(days=29)  # 30-day window
    window_start_str = str(window_start)
    today_str = str(today)
    date_window = [str(window_start + timedelta(days=i)) for i in range(30)]

    # Load active habits
    habits_result = await db.execute(
        select(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
    )
    habits = habits_result.scalars().all()
    if not habits:
        return []

    habit_ids = [h.id for h in habits]
    habit_map = {h.id: h for h in habits}

    # Load 30-day completion logs
    logs_result = await db.execute(
        select(HabitLog.habit_id, HabitLog.date).where(
            and_(
                HabitLog.user_id == user_id,
                HabitLog.date >= window_start_str,
                HabitLog.date <= today_str,
                HabitLog.completed == True,
                HabitLog.habit_id.in_(habit_ids),
            )
        )
    )
    completed_set: set[tuple] = {(row[0], row[1]) for row in logs_result.all()}

    # Build per-habit completion matrix: {habit_name: [bool×30]}
    completion_matrix: dict[str, list[bool]] = {}
    for h in habits:
        completion_matrix[h.name] = [(h.id, d) in completed_set for d in date_window]

    # Load 30-day health data
    health_result = await db.execute(
        select(HealthData).where(
            and_(
                HealthData.user_id == user_id,
                HealthData.date >= window_start_str,
                HealthData.date <= today_str,
            )
        )
    )
    health_rows = {row.date: row for row in health_result.scalars().all()}

    # Compute patterns via AI
    patterns = await _detect_patterns_ai(
        user_id, completion_matrix, health_rows, date_window, db
    )

    # Upsert — deactivate all old patterns, insert new ones
    old_patterns = await db.execute(
        select(BehaviourPattern).where(
            BehaviourPattern.user_id == user_id,
            BehaviourPattern.is_active == True,
        )
    )
    for p in old_patterns.scalars().all():
        p.is_active = False

    today_str_iso = str(today)
    for pattern_text, category, confidence in patterns:
        new_p = BehaviourPattern(
            user_id=user_id,
            pattern=pattern_text,
            category=category,
            confidence=confidence,
            first_seen=today_str_iso,
            last_seen=today_str_iso,
            is_active=True,
        )
        db.add(new_p)

    await db.flush()
    await invalidate_user_context(user_id, redis)
    return [p[0] for p in patterns]


async def get_active_patterns(user_id: int, db: AsyncSession) -> list[str]:
    """Return current active pattern strings for a user — used by context_service."""
    result = await db.execute(
        select(BehaviourPattern.pattern).where(
            BehaviourPattern.user_id == user_id,
            BehaviourPattern.is_active == True,
        ).order_by(BehaviourPattern.confidence.desc())
    )
    return [row[0] for row in result.all()]


async def _detect_patterns_ai(
    user_id: int,
    completion_matrix: dict[str, list[bool]],
    health_rows: dict,
    date_window: list[str],
    db: AsyncSession,
) -> list[tuple[str, str, float]]:
    """
    Call AI to identify patterns. Returns list of (pattern_text, category, confidence).
    Falls back to rule-based patterns if AI fails.
    """
    # Try rule-based detection first (fast, always runs)
    rule_patterns = _rule_based_patterns(completion_matrix, health_rows, date_window)

    # AI-based enrichment (adds nuance the rules miss)
    try:
        ai_patterns = await asyncio.wait_for(
            asyncio.to_thread(_ai_pattern_call, completion_matrix, health_rows, date_window),
            timeout=30.0,
        )
        # Merge: AI patterns take precedence, rules fill gaps
        all_patterns = ai_patterns + [p for p in rule_patterns if p[0] not in [a[0] for a in ai_patterns]]
        return all_patterns[:8]  # cap at 8 patterns
    except Exception:
        return rule_patterns[:8]


def _rule_based_patterns(
    completion_matrix: dict[str, list[bool]],
    health_rows: dict,
    date_window: list[str],
) -> list[tuple[str, str, float]]:
    """Fast rule-based pattern detection. No API call."""
    patterns = []

    for habit_name, days in completion_matrix.items():
        total = sum(days)
        rate = total / len(days) if days else 0

        if rate < 0.3:
            patterns.append((
                f"Consistently missing {habit_name} — completed only {int(rate*100)}% of days",
                "habit",
                0.9,
            ))
        elif rate > 0.85:
            patterns.append((
                f"Strong consistency on {habit_name} — {int(rate*100)}% completion rate",
                "habit",
                0.85,
            ))

        # Weekend drop detection
        weekend_days = [days[i] for i, d in enumerate(date_window) if _is_weekend(d)]
        weekday_days = [days[i] for i, d in enumerate(date_window) if not _is_weekend(d)]
        if weekend_days and weekday_days:
            weekend_rate = sum(weekend_days) / len(weekend_days)
            weekday_rate = sum(weekday_days) / len(weekday_days)
            if weekday_rate > 0.6 and weekend_rate < 0.35:
                patterns.append((
                    f"{habit_name} drops significantly on weekends — {int(weekend_rate*100)}% vs {int(weekday_rate*100)}% on weekdays",
                    "habit",
                    0.8,
                ))

    # Sleep pattern
    sleep_values = [health_rows[d].sleep_hours for d in date_window if d in health_rows and health_rows[d].sleep_hours > 0]
    if len(sleep_values) >= 7:
        avg_sleep = sum(sleep_values) / len(sleep_values)
        if avg_sleep < 6.0:
            patterns.append((
                f"Averaging {avg_sleep:.1f} hours sleep — consistently below the 7-hour threshold",
                "sleep",
                0.9,
            ))
        elif avg_sleep >= 7.5:
            patterns.append((
                f"Good sleep consistency — averaging {avg_sleep:.1f} hours",
                "sleep",
                0.7,
            ))

    # Step pattern
    step_values = [health_rows[d].steps for d in date_window if d in health_rows and health_rows[d].steps > 0]
    if len(step_values) >= 7:
        avg_steps = int(sum(step_values) / len(step_values))
        if avg_steps < 4000:
            patterns.append((
                f"Low daily movement — averaging {avg_steps:,} steps",
                "fitness",
                0.85,
            ))

    return patterns


def _ai_pattern_call(
    completion_matrix: dict,
    health_rows: dict,
    date_window: list[str],
) -> list[tuple[str, str, float]]:
    """Synchronous AI call — run in a thread."""
    from core.ai_client import get_ai_client
    import json

    # Build a compact data summary for the AI
    summary_lines = []
    for habit, days in completion_matrix.items():
        rate = int(sum(days) / len(days) * 100)
        # Day-of-week breakdown
        by_day = {}
        for i, d in enumerate(date_window):
            dow = _day_name(d)
            by_day.setdefault(dow, []).append(days[i])
        dow_rates = {k: int(sum(v) / len(v) * 100) for k, v in by_day.items() if v}
        summary_lines.append(f"- {habit}: {rate}% overall, by day: {dow_rates}")

    if health_rows:
        sleep_vals = [health_rows[d].sleep_hours for d in date_window if d in health_rows and health_rows[d].sleep_hours > 0]
        step_vals = [health_rows[d].steps for d in date_window if d in health_rows and health_rows[d].steps > 0]
        if sleep_vals:
            summary_lines.append(f"- Sleep avg: {sum(sleep_vals)/len(sleep_vals):.1f}h over {len(sleep_vals)} days")
        if step_vals:
            summary_lines.append(f"- Steps avg: {int(sum(step_vals)/len(step_vals))} over {len(step_vals)} days")

    data_text = "\n".join(summary_lines) if summary_lines else "No data available."

    client = get_ai_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""Analyse this 30-day behaviour data and identify the 3-5 most meaningful patterns.

Data:
{data_text}

Return ONLY a JSON array. Each item: {{"pattern": "plain English description", "category": "habit|fitness|sleep|focus|general", "confidence": 0.0-1.0}}
Patterns must be specific and reference real numbers. No generic observations.
Response must be valid JSON only — no other text."""
        }]
    )

    text = response.content[0].text.strip()
    # Strip any accidental markdown fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    parsed = json.loads(text)
    return [(p["pattern"], p.get("category", "general"), float(p.get("confidence", 0.7))) for p in parsed]


def _is_weekend(date_str: str) -> bool:
    try:
        d = date.fromisoformat(date_str)
        return d.weekday() >= 5
    except ValueError:
        return False


def _day_name(date_str: str) -> str:
    try:
        return date.fromisoformat(date_str).strftime("%A")[:3]
    except ValueError:
        return "?"
