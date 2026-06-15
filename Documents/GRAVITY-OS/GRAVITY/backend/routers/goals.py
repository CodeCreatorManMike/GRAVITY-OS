from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.user import Goal, User
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class GoalResponse(BaseModel):
    id: int
    statement: str
    real_why: str
    likelihood_score: float
    milestone_structure: list
    risk_factors: list
    cycle_start: str
    cycle_end: str
    days_remaining: int
    is_active: bool


class GoalUpdateRequest(BaseModel):
    statement: Optional[str] = None
    real_why: Optional[str] = None
    likelihood_score: Optional[float] = None

class GoalCreateRequest(BaseModel):
    statement: str
    real_why: str = ""
    cycle_length_days: int = 180   # default 6 months


# ── Helpers ───────────────────────────────────────────────────────────────────

def _days_remaining(cycle_end: str) -> int:
    try:
        return max(0, (date.fromisoformat(cycle_end) - date.today()).days)
    except (ValueError, TypeError):
        return 0


def _to_response(goal: Goal) -> GoalResponse:
    return GoalResponse(
        id=goal.id,
        statement=goal.statement or "",
        real_why=goal.real_why or "",
        likelihood_score=goal.likelihood_score or 0.0,
        milestone_structure=goal.milestone_structure or [],
        risk_factors=goal.risk_factors or [],
        cycle_start=goal.cycle_start or "",
        cycle_end=goal.cycle_end or "",
        days_remaining=_days_remaining(goal.cycle_end),
        is_active=goal.is_active,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    req: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Directly create a goal (bypasses AI onboarding).
    Deactivates any existing active goal first.
    Used for post-cycle goal creation or manual override.
    """
    if not req.statement.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Statement cannot be empty")

    # Deactivate existing active goal
    existing = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id, Goal.is_active == True)
    )
    for g in existing.scalars().all():
        g.is_active = False

    today = date.today()
    cycle_end = today + timedelta(days=max(1, req.cycle_length_days))

    goal = Goal(
        user_id=current_user.id,
        statement=req.statement.strip(),
        real_why=req.real_why.strip(),
        cycle_start=str(today),
        cycle_end=str(cycle_end),
        likelihood_score=0.5,
        is_active=True,
    )
    db.add(goal)
    await db.flush()
    return _to_response(goal)


@router.get("", response_model=GoalResponse)
async def get_active_goal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's current active goal."""
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.is_active == True)
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active goal found — complete onboarding first",
        )
    return _to_response(goal)


@router.get("/history", response_model=list[GoalResponse])
async def get_goal_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all completed (inactive) goals, newest first."""
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.is_active == False)
        .order_by(Goal.created_at.desc())
    )
    return [_to_response(g) for g in result.scalars().all()]


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    req: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update statement, real_why, and/or likelihood_score on a goal."""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()

    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    if goal.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your goal")

    if req.statement is not None:
        goal.statement = req.statement
    if req.real_why is not None:
        goal.real_why = req.real_why
    if req.likelihood_score is not None:
        goal.likelihood_score = max(0.0, min(1.0, req.likelihood_score))

    return _to_response(goal)
