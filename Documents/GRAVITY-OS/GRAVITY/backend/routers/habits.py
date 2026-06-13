from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.database import get_db
from backend.models.user import Habit, HabitLog, User
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/habits", tags=["habits"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class HabitResponse(BaseModel):
    id: int
    name: str
    is_non_negotiable: bool
    completed_today: bool


class HabitCreateRequest(BaseModel):
    name: str
    is_non_negotiable: bool = False


class HabitLogResponse(BaseModel):
    habit_id: int
    date: str
    completed: bool


class HeatmapEntry(BaseModel):
    date: str
    completed: bool


class HeatmapHabit(BaseModel):
    habit_id: int
    habit_name: str
    days: list[HeatmapEntry]


# ── Routes ────────────────────────────────────────────────────────────────────

# NOTE: /heatmap must be registered before /{habit_id} routes so the literal
# string "heatmap" is never mistaken for an integer path parameter.

@router.get("/heatmap", response_model=list[HeatmapHabit])
async def get_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return last 90 days of completion data per active habit.
    Every day in the window appears explicitly with completed=true/false.
    """
    today = date.today()
    start = today - timedelta(days=89)  # 90 days inclusive of today
    start_str = str(start)
    date_range = [str(start + timedelta(days=i)) for i in range(90)]

    habits_result = await db.execute(
        select(Habit)
        .where(Habit.user_id == current_user.id, Habit.is_active == True)
        .order_by(Habit.created_at.asc())
    )
    habits = habits_result.scalars().all()
    if not habits:
        return []

    habit_ids = [h.id for h in habits]

    logs_result = await db.execute(
        select(HabitLog.habit_id, HabitLog.date).where(
            and_(
                HabitLog.user_id == current_user.id,
                HabitLog.date >= start_str,
                HabitLog.completed == True,
                HabitLog.habit_id.in_(habit_ids),
            )
        )
    )
    completed_set: set[tuple[int, str]] = {(row[0], row[1]) for row in logs_result.all()}

    return [
        HeatmapHabit(
            habit_id=h.id,
            habit_name=h.name,
            days=[
                HeatmapEntry(date=d, completed=(h.id, d) in completed_set)
                for d in date_range
            ],
        )
        for h in habits
    ]


@router.get("", response_model=list[HabitResponse])
async def list_habits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all active habits with today's completion status."""
    today_str = str(date.today())

    habits_result = await db.execute(
        select(Habit)
        .where(Habit.user_id == current_user.id, Habit.is_active == True)
        .order_by(Habit.created_at.asc())
    )
    habits = habits_result.scalars().all()

    habit_ids = [h.id for h in habits]
    completed_today: set[int] = set()
    if habit_ids:
        logs_result = await db.execute(
            select(HabitLog.habit_id).where(
                and_(
                    HabitLog.user_id == current_user.id,
                    HabitLog.date == today_str,
                    HabitLog.completed == True,
                    HabitLog.habit_id.in_(habit_ids),
                )
            )
        )
        completed_today = {row[0] for row in logs_result.all()}

    return [
        HabitResponse(
            id=h.id,
            name=h.name,
            is_non_negotiable=h.is_non_negotiable,
            completed_today=h.id in completed_today,
        )
        for h in habits
    ]


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    req: HabitCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new habit."""
    if not req.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Habit name cannot be empty",
        )
    habit = Habit(
        user_id=current_user.id,
        name=req.name.strip(),
        is_non_negotiable=req.is_non_negotiable,
        is_active=True,
    )
    db.add(habit)
    await db.flush()
    return HabitResponse(
        id=habit.id,
        name=habit.name,
        is_non_negotiable=habit.is_non_negotiable,
        completed_today=False,
    )


@router.post("/{habit_id}/complete", response_model=HabitLogResponse)
async def complete_habit(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Log today's completion for a habit.
    Idempotent — if already logged today, returns the existing record.
    """
    result = await db.execute(select(Habit).where(Habit.id == habit_id))
    habit = result.scalar_one_or_none()
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your habit")
    if not habit.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Habit is inactive")

    today_str = str(date.today())

    existing = await db.execute(
        select(HabitLog).where(
            and_(
                HabitLog.habit_id == habit_id,
                HabitLog.user_id == current_user.id,
                HabitLog.date == today_str,
            )
        )
    )
    log = existing.scalar_one_or_none()

    if log is None:
        log = HabitLog(
            habit_id=habit_id,
            user_id=current_user.id,
            date=today_str,
            completed=True,
        )
        db.add(log)
        await db.flush()

    return HabitLogResponse(habit_id=habit_id, date=today_str, completed=log.completed)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a habit (is_active=False). History is preserved."""
    result = await db.execute(select(Habit).where(Habit.id == habit_id))
    habit = result.scalar_one_or_none()
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your habit")
    habit.is_active = False
