"""
Integrations router — Phase 1: Apple Health data ingest.

The iOS app reads HealthKit data and POSTs it here.
This endpoint is the ONLY way health data enters the system —
the backend never calls Apple APIs directly (the app holds the HealthKit permission).

Endpoints:
  POST /integrations/health/sync    ← app pushes daily health snapshot
  GET  /integrations/health/today   ← latest health data for context
  GET  /integrations/status         ← which integrations are connected
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User
from backend.models.integration import HealthData
from backend.routers.auth import get_current_user
from backend.config import get_settings
from backend.services.context_service import invalidate_user_context

router = APIRouter(prefix="/integrations", tags=["integrations"])
settings = get_settings()

_redis_client = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# ── Schemas ───────────────────────────────────────────────────────────────────

class HealthSyncRequest(BaseModel):
    date: str = Field(default_factory=lambda: str(date.today()))
    steps: int = Field(default=0, ge=0)
    sleep_hours: float = Field(default=0.0, ge=0.0, le=24.0)
    sleep_quality: str = Field(default="unknown")
    workout_minutes: int = Field(default=0, ge=0)
    workout_type: str = Field(default="")
    heart_rate_avg: int = Field(default=0, ge=0)
    calories_active: int = Field(default=0, ge=0)


class HealthSyncResponse(BaseModel):
    date: str
    steps: int
    sleep_hours: float
    sleep_quality: str
    workout_minutes: int
    workout_type: str
    heart_rate_avg: int
    calories_active: int
    synced: bool = True


class IntegrationStatus(BaseModel):
    name: str
    connected: bool
    last_sync: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/health/sync", response_model=HealthSyncResponse)
async def sync_health_data(
    req: HealthSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upsert a daily health snapshot from Apple Health.
    Called by the iOS app after reading HealthKit data.
    Idempotent — re-posting the same date updates the existing row.
    """
    # Validate date format
    try:
        date.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date must be YYYY-MM-DD",
        )

    # Upsert: check for existing row
    existing = await db.execute(
        select(HealthData).where(
            and_(
                HealthData.user_id == current_user.id,
                HealthData.date == req.date,
            )
        )
    )
    row = existing.scalar_one_or_none()

    if row is None:
        row = HealthData(
            user_id=current_user.id,
            date=req.date,
        )
        db.add(row)

    row.steps = req.steps
    row.sleep_hours = req.sleep_hours
    row.sleep_quality = req.sleep_quality or "unknown"
    row.workout_minutes = req.workout_minutes
    row.workout_type = req.workout_type or ""
    row.heart_rate_avg = req.heart_rate_avg
    row.calories_active = req.calories_active

    await db.flush()

    # Invalidate context so the next AI call picks up fresh health data
    await invalidate_user_context(current_user.id, get_redis())

    return HealthSyncResponse(
        date=row.date,
        steps=row.steps,
        sleep_hours=row.sleep_hours,
        sleep_quality=row.sleep_quality,
        workout_minutes=row.workout_minutes,
        workout_type=row.workout_type,
        heart_rate_avg=row.heart_rate_avg,
        calories_active=row.calories_active,
    )


@router.get("/health/today", response_model=Optional[HealthSyncResponse])
async def get_today_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return today's health snapshot, or null if not yet synced."""
    today_str = str(date.today())
    result = await db.execute(
        select(HealthData).where(
            and_(
                HealthData.user_id == current_user.id,
                HealthData.date == today_str,
            )
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return HealthSyncResponse(
        date=row.date,
        steps=row.steps,
        sleep_hours=row.sleep_hours,
        sleep_quality=row.sleep_quality,
        workout_minutes=row.workout_minutes,
        workout_type=row.workout_type,
        heart_rate_avg=row.heart_rate_avg,
        calories_active=row.calories_active,
    )


@router.get("/status", response_model=list[IntegrationStatus])
async def get_integration_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return which integrations have synced data for this user."""
    # Check Apple Health: any health_data row exists?
    health_result = await db.execute(
        select(HealthData.synced_at, HealthData.date)
        .where(HealthData.user_id == current_user.id)
        .order_by(HealthData.synced_at.desc())
        .limit(1)
    )
    health_row = health_result.first()

    integrations = [
        IntegrationStatus(
            name="apple_health",
            connected=health_row is not None,
            last_sync=health_row[0].isoformat() if health_row else None,
        ),
        # Phase 2 — not yet connected
        IntegrationStatus(name="apple_calendar", connected=False),
        IntegrationStatus(name="google_calendar", connected=False),
    ]
    return integrations
