"""
AI log router — app and device report back whether a user acted on AI output.

POST /ai/outcome          record an outcome for an interaction
GET  /ai/interactions     list recent interactions (debug / analytics)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.services.ai_log_service import record_outcome, get_recent_interactions

router = APIRouter(prefix="/ai", tags=["ai-log"])


class OutcomeRequest(BaseModel):
    interaction_id: int
    acted: bool
    acted_within_hours: float | None = None
    user_rating: int | None = Field(default=None, ge=1, le=5)


class InteractionResponse(BaseModel):
    id: int
    mode: str
    provider: str
    model: str
    message: str
    tool_used: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/outcome", status_code=status.HTTP_204_NO_CONTENT)
async def post_outcome(
    body: OutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """App or device reports whether the user acted on an AI output."""
    await record_outcome(
        interaction_id=body.interaction_id,
        acted=body.acted,
        acted_within_hours=body.acted_within_hours,
        user_rating=body.user_rating,
        db=db,
    )


@router.get("/interactions", response_model=list[InteractionResponse])
async def list_interactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await get_recent_interactions(current_user.id, db)
    return [
        InteractionResponse(
            id=r.id,
            mode=r.mode,
            provider=r.provider,
            model=r.model,
            message=r.message,
            tool_used=r.tool_used,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]
