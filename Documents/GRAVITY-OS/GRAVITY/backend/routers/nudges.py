import asyncio
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import Nudge, NudgeSettings, User
from backend.routers.auth import get_current_user
from backend.config import get_settings
from backend.services.context_service import (
    build_user_context,
    build_nudge_state,
    invalidate_user_context,
)

router = APIRouter(prefix="/nudges", tags=["nudges"])
settings = get_settings()

# ── Lazy singleton ────────────────────────────────────────────────────────────

_redis_client = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# ── Schemas ───────────────────────────────────────────────────────────────────

class NudgeFiredData(BaseModel):
    id: int
    category: str
    intensity: str
    tone: str
    message: str
    sub_message: Optional[str] = None
    action_label: str
    sent_at: str


class NudgeEvaluateResponse(BaseModel):
    nudge: bool
    reason: Optional[str] = None     # set when nudge=False
    data: Optional[NudgeFiredData] = None  # set when nudge=True


class NudgeResponse(BaseModel):
    id: int
    category: str
    intensity: str
    tone: str
    message: str
    sub_message: str
    action_label: str
    reason: str
    acknowledged: bool
    sent_at: str


class NudgeSettingsResponse(BaseModel):
    quiet_hours_start: str
    quiet_hours_end: str
    rest_days: list
    sensitivity_habit: float
    sensitivity_focus: float
    sensitivity_fitness: float
    sensitivity_sleep: float
    sensitivity_spending: float


class NudgeSettingsUpdateRequest(BaseModel):
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    rest_days: Optional[list] = None
    sensitivity_habit: Optional[float] = None
    sensitivity_focus: Optional[float] = None
    sensitivity_fitness: Optional[float] = None
    sensitivity_sleep: Optional[float] = None
    sensitivity_spending: Optional[float] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _in_quiet_hours(now_hhmm: str, start: str, end: str) -> bool:
    """
    Return True if now falls within [start, end) quiet hours.
    Handles overnight spans correctly (e.g. 22:00–08:00).
    TODO: per-user timezone — currently uses server local time (London, single user)
    """
    def to_min(t: str) -> int:
        h, m = t.split(":")
        return int(h) * 60 + int(m)

    now = to_min(now_hhmm)
    s = to_min(start)
    e = to_min(end)
    if s > e:  # overnight span
        return now >= s or now < e
    return s <= now < e


def _to_nudge_response(n: Nudge) -> NudgeResponse:
    return NudgeResponse(
        id=n.id,
        category=n.category or "",
        intensity=n.intensity or "ambient",
        tone=n.tone or "direct",
        message=n.message or "",
        sub_message=n.sub_message or "",
        action_label=n.action_label or "Dismiss",
        reason=n.reason or "",
        acknowledged=n.acknowledged,
        sent_at=n.sent_at.isoformat() if n.sent_at else "",
    )


def _to_settings_response(s: NudgeSettings) -> NudgeSettingsResponse:
    return NudgeSettingsResponse(
        quiet_hours_start=s.quiet_hours_start or "22:00",
        quiet_hours_end=s.quiet_hours_end or "08:00",
        rest_days=s.rest_days or [],
        sensitivity_habit=s.sensitivity_habit if s.sensitivity_habit is not None else 1.0,
        sensitivity_focus=s.sensitivity_focus if s.sensitivity_focus is not None else 1.0,
        sensitivity_fitness=s.sensitivity_fitness if s.sensitivity_fitness is not None else 1.0,
        sensitivity_sleep=s.sensitivity_sleep if s.sensitivity_sleep is not None else 1.0,
        sensitivity_spending=s.sensitivity_spending if s.sensitivity_spending is not None else 1.0,
    )


async def _get_or_create_settings(user_id: int, db: AsyncSession) -> NudgeSettings:
    result = await db.execute(
        select(NudgeSettings).where(NudgeSettings.user_id == user_id)
    )
    ns = result.scalar_one_or_none()
    if ns is None:
        ns = NudgeSettings(user_id=user_id)
        db.add(ns)
        await db.flush()
    return ns


# ── Routes ────────────────────────────────────────────────────────────────────
# NOTE: literal paths (/evaluate, /settings) registered before /{nudge_id}
# so FastAPI never mistakes them for integer path parameters.

@router.post("/evaluate", response_model=NudgeEvaluateResponse)
async def evaluate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger nudge evaluation for the current user.

    Gate order (all must pass before AI is called):
      1. cooldown   — Redis key nudge_cooldown:{id} exists
      2. daily_cap  — 3 nudges already sent today
      3. quiet_hours — current time in user's quiet window (from context)
      4. rest_day   — today in user's rest_days (from context)

    Context is served from Redis cache (1h TTL) or rebuilt from DB.
    Gate reads settings from context so quiet hours are always real
    values, never hardcoded defaults.
    """
    redis = get_redis()

    # ── 1. Load full context (cache or DB) ────────────────────────────────────
    ctx = await build_user_context(current_user.id, db, redis)
    ns = ctx["nudge_settings"]

    # ── 2. Gate checks ────────────────────────────────────────────────────────
    now = datetime.now()
    # TODO: per-user timezone — currently server local time (London, single user)
    now_hhmm = now.strftime("%H:%M")
    today_str = str(date.today())
    weekday_name = now.strftime("%A")

    cooldown_key = f"nudge_cooldown:{current_user.id}"
    daily_key    = f"nudge_daily:{current_user.id}:{today_str}"

    if await redis.exists(cooldown_key):
        return NudgeEvaluateResponse(nudge=False, reason="cooldown_active")

    daily_count = await redis.get(daily_key)
    if daily_count and int(daily_count) >= 3:
        return NudgeEvaluateResponse(nudge=False, reason="daily_cap")

    if _in_quiet_hours(now_hhmm, ns["quiet_hours_start"], ns["quiet_hours_end"]):
        return NudgeEvaluateResponse(nudge=False, reason="quiet_hours")

    if weekday_name in (ns["rest_days"] or []):
        return NudgeEvaluateResponse(nudge=False, reason="rest_day")

    # ── 3. Build decide_nudge-compatible state from context ───────────────────
    state = build_nudge_state(ctx, now_hhmm, weekday_name)

    # ── 4. Run two-call AI pipeline in thread ─────────────────────────────────
    from core.nudge_engine import decide_nudge, generate_nudge_content

    def _run_pipeline() -> dict:
        decision = decide_nudge(state)
        if not decision.get("should_nudge"):
            return {"nudge": False, "reason": decision.get("reason", "")}
        content = generate_nudge_content(state, decision)
        return {
            "nudge": True,
            "category": decision.get("category"),
            "intensity": decision.get("intensity"),
            "reason": decision.get("reason", ""),
            "data_points": decision.get("data_points", []),
            "message": content.get("message", ""),
            "sub_message": content.get("sub_message"),
            "action_label": content.get("action_label", "Dismiss"),
            "display_duration_seconds": content.get("display_duration_seconds", 30),
            "cooldown_after": decision.get("cooldown_after", 90),
        }

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_pipeline),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI response timed out — please try again",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI call failed: {exc}",
        )

    # ── 5. AI declined ────────────────────────────────────────────────────────
    if not result["nudge"]:
        return NudgeEvaluateResponse(nudge=False, reason="ai_declined")

    # ── 6. Store nudge row ────────────────────────────────────────────────────
    nudge_row = Nudge(
        user_id=current_user.id,
        category=result.get("category") or "",
        intensity=result.get("intensity") or "ambient",
        tone=ctx["profile"]["feedback_preference"] or "direct",
        message=result.get("message") or "",
        sub_message=result.get("sub_message") or "",
        action_label=result.get("action_label") or "Dismiss",
        reason=result.get("reason") or "",
        acknowledged=False,
    )
    db.add(nudge_row)
    await db.flush()
    await db.refresh(nudge_row)  # load server_default sent_at from DB

    # ── 7. Set Redis cooldown + increment daily counter ───────────────────────
    cooldown_minutes = max(90, result.get("cooldown_after", 90))
    await redis.setex(cooldown_key, cooldown_minutes * 60, "1")

    count = await redis.incr(daily_key)
    if count == 1:
        await redis.expire(daily_key, 86400)

    # ── 8. Invalidate context cache (nudge_history is now stale) ─────────────
    await invalidate_user_context(current_user.id, redis)

    # ── 9. Broadcast via WebSocket if user is connected ───────────────────────
    from backend.services.connection_manager import manager
    await manager.send_to_user(
        current_user.id,
        "NUDGE",
        {
            "id": nudge_row.id,
            "category": nudge_row.category,
            "intensity": nudge_row.intensity,
            "tone": nudge_row.tone,
            "message": nudge_row.message,
            "sub_message": nudge_row.sub_message or None,
            "action_label": nudge_row.action_label,
            "sent_at": nudge_row.sent_at.isoformat(),
        },
    )

    return NudgeEvaluateResponse(
        nudge=True,
        data=NudgeFiredData(
            id=nudge_row.id,
            category=nudge_row.category,
            intensity=nudge_row.intensity,
            tone=nudge_row.tone,
            message=nudge_row.message,
            sub_message=nudge_row.sub_message or None,
            action_label=nudge_row.action_label,
            sent_at=nudge_row.sent_at.isoformat(),
        ),
    )


@router.get("", response_model=list[NudgeResponse])
async def list_nudges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all nudges for this user, newest first."""
    result = await db.execute(
        select(Nudge)
        .where(Nudge.user_id == current_user.id)
        .order_by(Nudge.sent_at.desc())
    )
    return [_to_nudge_response(n) for n in result.scalars().all()]


@router.get("/settings", response_model=NudgeSettingsResponse)
async def get_nudge_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return nudge settings for this user. Auto-creates defaults on first call."""
    ns = await _get_or_create_settings(current_user.id, db)
    return _to_settings_response(ns)


@router.put("/settings", response_model=NudgeSettingsResponse)
async def update_nudge_settings(
    req: NudgeSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Partially update nudge settings. Sensitivity values clamped to 0.0–1.0."""
    redis = get_redis()
    ns = await _get_or_create_settings(current_user.id, db)
    if req.quiet_hours_start is not None:
        ns.quiet_hours_start = req.quiet_hours_start
    if req.quiet_hours_end is not None:
        ns.quiet_hours_end = req.quiet_hours_end
    if req.rest_days is not None:
        ns.rest_days = req.rest_days
    if req.sensitivity_habit is not None:
        ns.sensitivity_habit = max(0.0, min(1.0, req.sensitivity_habit))
    if req.sensitivity_focus is not None:
        ns.sensitivity_focus = max(0.0, min(1.0, req.sensitivity_focus))
    if req.sensitivity_fitness is not None:
        ns.sensitivity_fitness = max(0.0, min(1.0, req.sensitivity_fitness))
    if req.sensitivity_sleep is not None:
        ns.sensitivity_sleep = max(0.0, min(1.0, req.sensitivity_sleep))
    if req.sensitivity_spending is not None:
        ns.sensitivity_spending = max(0.0, min(1.0, req.sensitivity_spending))
    # Settings changed — invalidate so next evaluate reads fresh values
    await invalidate_user_context(current_user.id, redis)
    return _to_settings_response(ns)


@router.put("/{nudge_id}/acknowledge", response_model=NudgeResponse)
async def acknowledge_nudge(
    nudge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a nudge as acknowledged. Returns 404 if not found or not owned by this user."""
    result = await db.execute(select(Nudge).where(Nudge.id == nudge_id))
    nudge = result.scalar_one_or_none()
    if nudge is None or nudge.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nudge not found")
    nudge.acknowledged = True
    return _to_nudge_response(nudge)
