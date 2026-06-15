"""
Analytics router — aggregated stats for the app dashboard.

Endpoints:
  GET /analytics/summary    ← weekly/monthly habit completion rollup
  GET /analytics/patterns   ← active AI-identified behaviour patterns
  GET /analytics/likelihood ← goal likelihood score + trend
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from backend.database import get_db
from backend.models.user import User, Goal, Habit, HabitLog, Nudge
from backend.models.integration import HealthData, BehaviourPattern
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class WeekSummary(BaseModel):
    week_start: str
    total_completions: int
    possible_completions: int
    completion_rate: float


class HabitStat(BaseModel):
    habit_name: str
    is_non_negotiable: bool
    last_7_days: int    # completions
    last_30_days: int
    all_time: int
    current_streak: int


class AnalyticsSummary(BaseModel):
    current_streak: int
    longest_streak: int
    last_7_days_rate: float
    last_30_days_rate: float
    total_completions: int
    nudges_sent_30d: int
    nudge_response_rate: float
    habit_stats: list[HabitStat]
    weekly_breakdown: list[WeekSummary]


class PatternResponse(BaseModel):
    patterns: list[str]
    categories: list[str]


class LikelihoodResponse(BaseModel):
    current: float
    goal: str
    days_remaining: int
    cycle_start: str
    cycle_end: str
    habit_completion_30d: float


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_current_streak(completion_matrix: dict[str, list[bool]], nn_names: set[str]) -> int:
    """Count consecutive days (backwards from yesterday) where at least one NN was completed."""
    if not nn_names or not completion_matrix:
        return 0
    # Index 0 = 29 days ago, index 29 = today (30-day window)
    streak = 0
    for day_idx in range(28, -1, -1):  # 28=yesterday, 0=29 days ago
        done = any(
            completion_matrix.get(name, [False] * 30)[day_idx]
            for name in nn_names
        )
        if done:
            streak += 1
        else:
            break
    # Today counts if any NN done today
    today_done = any(
        completion_matrix.get(name, [False] * 30)[29]
        for name in nn_names
    )
    if today_done:
        streak += 1
    return streak


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated habit stats for the analytics dashboard."""
    today = date.today()
    d30_start = str(today - timedelta(days=29))
    d7_start = str(today - timedelta(days=6))

    # Active habits
    habits_result = await db.execute(
        select(Habit).where(Habit.user_id == current_user.id, Habit.is_active == True)
    )
    habits = habits_result.scalars().all()
    if not habits:
        return AnalyticsSummary(
            current_streak=0, longest_streak=0,
            last_7_days_rate=0.0, last_30_days_rate=0.0,
            total_completions=0, nudges_sent_30d=0, nudge_response_rate=0.0,
            habit_stats=[], weekly_breakdown=[],
        )

    habit_ids = [h.id for h in habits]
    nn_names = {h.name for h in habits if h.is_non_negotiable}

    # All completions in 30-day window
    logs_result = await db.execute(
        select(HabitLog.habit_id, HabitLog.date).where(
            and_(
                HabitLog.user_id == current_user.id,
                HabitLog.date >= d30_start,
                HabitLog.completed == True,
                HabitLog.habit_id.in_(habit_ids),
            )
        )
    )
    logs_30d: set[tuple] = {(r[0], r[1]) for r in logs_result.all()}

    # All-time completion counts
    all_time_result = await db.execute(
        select(HabitLog.habit_id, func.count()).select_from(HabitLog).where(
            and_(
                HabitLog.user_id == current_user.id,
                HabitLog.completed == True,
                HabitLog.habit_id.in_(habit_ids),
            )
        ).group_by(HabitLog.habit_id)
    )
    all_time_map = {r[0]: r[1] for r in all_time_result.all()}

    # Build per-habit completion matrix for 30 days
    date_window_30 = [str(today - timedelta(days=i)) for i in range(29, -1, -1)]
    date_window_7 = [str(today - timedelta(days=i)) for i in range(6, -1, -1)]

    completion_matrix: dict[str, list[bool]] = {}
    habit_stats = []
    for h in habits:
        days_30 = [(h.id, d) in logs_30d for d in date_window_30]
        days_7 = [(h.id, d) in logs_30d for d in date_window_7]
        completion_matrix[h.name] = days_30

        # Current streak for this habit
        s = 0
        for i in range(28, -1, -1):
            if days_30[i]: s += 1
            else: break
        if days_30[29]: s += 1

        habit_stats.append(HabitStat(
            habit_name=h.name,
            is_non_negotiable=h.is_non_negotiable,
            last_7_days=sum(days_7),
            last_30_days=sum(days_30),
            all_time=all_time_map.get(h.id, 0),
            current_streak=s,
        ))

    # Overall rates
    possible_7 = len(habits) * 7
    possible_30 = len(habits) * 30
    done_7 = sum(1 for (hid, d) in logs_30d if d in set(date_window_7))
    done_30 = len(logs_30d)
    rate_7 = round(done_7 / possible_7, 3) if possible_7 else 0.0
    rate_30 = round(done_30 / possible_30, 3) if possible_30 else 0.0

    # Total all-time completions
    total_result = await db.execute(
        select(func.count()).select_from(HabitLog).where(
            and_(HabitLog.user_id == current_user.id, HabitLog.completed == True)
        )
    )
    total = total_result.scalar() or 0

    # Nudge stats
    from datetime import datetime, timezone
    thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)
    nudge_total = await db.execute(
        select(func.count()).select_from(Nudge).where(
            and_(Nudge.user_id == current_user.id, Nudge.sent_at >= thirty_days_ago)
        )
    )
    nudge_acked = await db.execute(
        select(func.count()).select_from(Nudge).where(
            and_(Nudge.user_id == current_user.id, Nudge.sent_at >= thirty_days_ago, Nudge.acknowledged == True)
        )
    )
    n_total = nudge_total.scalar() or 0
    n_acked = nudge_acked.scalar() or 0

    # Weekly breakdown (last 4 weeks)
    weekly = []
    for w in range(4):
        w_end = today - timedelta(days=w * 7)
        w_start = w_end - timedelta(days=6)
        w_days = {str(w_start + timedelta(days=i)) for i in range(7)}
        w_done = sum(1 for (_, d) in logs_30d if d in w_days)
        w_possible = len(habits) * 7
        weekly.append(WeekSummary(
            week_start=str(w_start),
            total_completions=w_done,
            possible_completions=w_possible,
            completion_rate=round(w_done / w_possible, 3) if w_possible else 0.0,
        ))
    weekly.reverse()

    # Streak
    streak = _compute_current_streak(completion_matrix, nn_names)

    return AnalyticsSummary(
        current_streak=streak,
        longest_streak=streak,  # full longest-streak calc needs full history — placeholder
        last_7_days_rate=rate_7,
        last_30_days_rate=rate_30,
        total_completions=total,
        nudges_sent_30d=n_total,
        nudge_response_rate=round(n_acked / n_total, 3) if n_total else 0.0,
        habit_stats=habit_stats,
        weekly_breakdown=weekly,
    )


@router.get("/patterns", response_model=PatternResponse)
async def get_patterns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return currently active AI-identified behaviour patterns."""
    result = await db.execute(
        select(BehaviourPattern.pattern, BehaviourPattern.category).where(
            BehaviourPattern.user_id == current_user.id,
            BehaviourPattern.is_active == True,
        ).order_by(BehaviourPattern.confidence.desc())
    )
    rows = result.all()
    return PatternResponse(
        patterns=[r[0] for r in rows],
        categories=[r[1] for r in rows],
    )


@router.get("/likelihood", response_model=LikelihoodResponse)
async def get_likelihood(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current goal likelihood + supporting metrics."""
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.is_active == True)
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        return LikelihoodResponse(
            current=0.0, goal="", days_remaining=0,
            cycle_start="", cycle_end="", habit_completion_30d=0.0,
        )

    today = date.today()
    d30_start = str(today - timedelta(days=29))
    habits_result = await db.execute(
        select(func.count()).select_from(Habit).where(
            Habit.user_id == current_user.id, Habit.is_active == True
        )
    )
    habit_count = habits_result.scalar() or 0
    logs_count = await db.execute(
        select(func.count()).select_from(HabitLog).where(
            and_(
                HabitLog.user_id == current_user.id,
                HabitLog.date >= d30_start,
                HabitLog.completed == True,
            )
        )
    )
    done = logs_count.scalar() or 0
    possible = habit_count * 30
    completion_30d = round(done / possible, 3) if possible else 0.0

    try:
        days_remaining = max(0, (date.fromisoformat(goal.cycle_end) - today).days)
    except (ValueError, TypeError):
        days_remaining = 0

    return LikelihoodResponse(
        current=float(goal.likelihood_score or 0.0),
        goal=goal.statement or "",
        days_remaining=days_remaining,
        cycle_start=goal.cycle_start or "",
        cycle_end=goal.cycle_end or "",
        habit_completion_30d=completion_30d,
    )
