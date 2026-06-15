"""
Review router — 6-month cycle review endpoints.

When a cycle ends, the user is guided through a review conversation.
The AI analyses the cycle, generates a summary, then sets up the next cycle.

Endpoints:
  GET  /review/current     ← active cycle summary
  POST /review/start       ← trigger a new cycle review
  POST /review/message     ← conversational turn during review
  GET  /review/history     ← list of completed cycle reviews
"""
import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User, Goal
from backend.models.integration import CycleReview
from backend.routers.auth import get_current_user
from backend.config import get_settings
from backend.services.context_service import build_user_context

router = APIRouter(prefix="/review", tags=["review"])
settings = get_settings()

_redis_client = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# ── Schemas ───────────────────────────────────────────────────────────────────

class CycleSummaryResponse(BaseModel):
    goal: str
    cycle_start: str
    cycle_end: str
    days_remaining: int
    likelihood_score: float
    habits_avg_completion: float
    is_cycle_ending: bool    # true if within 14 days of cycle_end


class ReviewStartResponse(BaseModel):
    review_id: int
    message: str
    phase: str


class ReviewMessageRequest(BaseModel):
    message: str
    review_id: int


class ReviewMessageResponse(BaseModel):
    message: str
    review_id: int
    review_complete: bool = False


class CycleReviewHistory(BaseModel):
    id: int
    cycle_start: str
    cycle_end: str
    final_likelihood: float
    habits_avg_completion: float
    ai_summary: str
    status: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_active_goal(user_id: int, db: AsyncSession) -> Optional[Goal]:
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.is_active == True)
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _compute_avg_completion(ctx: dict) -> float:
    completion = ctx["recent_behaviour"]["last_7_days_habit_completion"]
    if not completion:
        return 0.0
    totals = []
    for habit_days in completion.values():
        totals.append(sum(habit_days) / len(habit_days))
    return round(sum(totals) / len(totals), 3) if totals else 0.0


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/current", response_model=CycleSummaryResponse)
async def get_current_cycle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a summary of the current active goal cycle."""
    goal = await _get_active_goal(current_user.id, db)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active goal cycle",
        )

    redis = get_redis()
    ctx = await build_user_context(current_user.id, db, redis)
    avg_completion = _compute_avg_completion(ctx)

    days_remaining = ctx["current_cycle"]["days_remaining"]
    is_ending = days_remaining <= 14

    return CycleSummaryResponse(
        goal=goal.statement,
        cycle_start=goal.cycle_start or "",
        cycle_end=goal.cycle_end or "",
        days_remaining=days_remaining,
        likelihood_score=float(goal.likelihood_score or 0.0),
        habits_avg_completion=avg_completion,
        is_cycle_ending=is_ending,
    )


@router.post("/start", response_model=ReviewStartResponse, status_code=status.HTTP_201_CREATED)
async def start_review(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a new cycle review.
    Creates a CycleReview row with status='in_progress' and returns
    the opening AI message.
    """
    goal = await _get_active_goal(current_user.id, db)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active goal to review",
        )

    # Check if a review is already in progress
    existing = await db.execute(
        select(CycleReview).where(
            CycleReview.user_id == current_user.id,
            CycleReview.status == "in_progress",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A review is already in progress",
        )

    redis = get_redis()
    ctx = await build_user_context(current_user.id, db, redis)
    avg_completion = _compute_avg_completion(ctx)
    days_remaining = ctx["current_cycle"]["days_remaining"]

    # Create review row
    review = CycleReview(
        user_id=current_user.id,
        goal_id=goal.id,
        cycle_start=goal.cycle_start or "",
        cycle_end=goal.cycle_end or "",
        final_likelihood=float(goal.likelihood_score or 0.0),
        habits_avg_completion=avg_completion,
        nudge_response_rate=ctx["recent_behaviour"]["nudge_response_rate"],
        status="in_progress",
        patterns_log=ctx["recent_behaviour"]["patterns_identified"],
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)

    # Generate opening AI message
    def _build_opening_message() -> str:
        from core.ai_client import get_ai_client
        client = get_ai_client()
        pct = int(float(goal.likelihood_score or 0) * 100)
        habit_pct = int(avg_completion * 100)
        goal_text = goal.statement or "your goal"
        name = ctx["profile"]["name"]

        prompt = f"""You are GRAVITY, a direct AI goal coach. The user {name} has just completed (or is ending)
a 6-month cycle. Their goal was: {goal_text}

Cycle data:
- Likelihood score reached: {pct}%
- Habit completion rate: {habit_pct}%
- Days remaining in cycle: {days_remaining}

Open the review with ONE honest, direct opening message. Reference their specific goal and at least
one real number. Ask one question to start the reflection. No fluff, no platitudes.
Voice-ready format — no symbols, no markdown."""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    try:
        opening_message = await asyncio.wait_for(
            asyncio.to_thread(_build_opening_message),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI response timed out",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI call failed: {exc}",
        )

    return ReviewStartResponse(
        review_id=review.id,
        message=opening_message,
        phase="reflection",
    )


@router.post("/message", response_model=ReviewMessageResponse)
async def review_message(
    req: ReviewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Conversational turn during an in-progress cycle review.
    The AI guides the user through reflection, then goal-setting for the next cycle.
    When complete: marks the review done and deactivates the old goal.
    """
    result = await db.execute(
        select(CycleReview).where(CycleReview.id == req.review_id)
    )
    review = result.scalar_one_or_none()
    if review is None or review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.status == "complete":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review already complete")

    redis = get_redis()
    ctx = await build_user_context(current_user.id, db, redis)

    # Pull previous review session from Redis
    session_key = f"review_session:{review.id}"
    raw_history = await redis.get(session_key)
    history = []
    if raw_history:
        import json
        history = json.loads(raw_history)

    history.append({"role": "user", "content": req.message})

    def _run_review_turn():
        from core.ai_client import get_ai_client
        import json as _json
        client = get_ai_client()
        name = ctx["profile"]["name"]
        goal_text = ctx["current_cycle"]["goal"]

        system = f"""You are GRAVITY, conducting a structured 6-month cycle review with {name}.

Their cycle goal was: {goal_text}
Cycle stats: likelihood {int(review.final_likelihood * 100)}%, habit completion {int(review.habits_avg_completion * 100)}%

Phase structure:
1. Reflection: what worked, what didn't (2-3 turns)
2. Honest assessment: where they fell short and why (1-2 turns)
3. Next cycle goal setting: what they want to achieve in the next 6 months (2-3 turns)
4. Confirmation: finalise the new goal — signal completion with [REVIEW_COMPLETE] on a new line at the END of your message

Rules:
- One question per message
- Reference real data when confronting avoidance
- Be direct, not cruel
- Voice-ready output — no symbols, no markdown
- Signal completion ONLY when the new goal is confirmed"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=system,
            messages=history,
        )
        text = response.content[0].text.strip()
        return text

    try:
        import json
        ai_response = await asyncio.wait_for(
            asyncio.to_thread(_run_review_turn),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI response timed out",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI call failed: {exc}",
        )

    review_complete = "[REVIEW_COMPLETE]" in ai_response
    clean_response = ai_response.replace("[REVIEW_COMPLETE]", "").strip()

    history.append({"role": "assistant", "content": clean_response})
    await redis.setex(session_key, 86400, json.dumps(history))

    if review_complete:
        review.status = "complete"
        review.ai_summary = clean_response
        # Deactivate old goal — next onboarding will create a new one
        goal_result = await db.execute(
            select(Goal).where(Goal.id == review.goal_id)
        )
        old_goal = goal_result.scalar_one_or_none()
        if old_goal:
            old_goal.is_active = False
        await db.flush()
        await redis.delete(session_key)

    return ReviewMessageResponse(
        message=clean_response,
        review_id=review.id,
        review_complete=review_complete,
    )


@router.get("/history", response_model=list[CycleReviewHistory])
async def get_review_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all completed cycle reviews for this user."""
    result = await db.execute(
        select(CycleReview)
        .where(
            CycleReview.user_id == current_user.id,
            CycleReview.status == "complete",
        )
        .order_by(CycleReview.created_at.desc())
    )
    reviews = result.scalars().all()
    return [
        CycleReviewHistory(
            id=r.id,
            cycle_start=r.cycle_start,
            cycle_end=r.cycle_end,
            final_likelihood=r.final_likelihood,
            habits_avg_completion=r.habits_avg_completion,
            ai_summary=r.ai_summary,
            status=r.status,
        )
        for r in reviews
    ]
