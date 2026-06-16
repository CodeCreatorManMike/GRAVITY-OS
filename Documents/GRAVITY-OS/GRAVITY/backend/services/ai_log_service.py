"""
AI interaction logging — every AI-generated output gets a row.
Call log_interaction() after each AI call. App/device report outcomes via record_outcome().
These rows are the future fine-tuning training signal.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.ai_log import AIInteraction, AIOutcome


async def log_interaction(
    user_id: int,
    mode: str,
    provider: str,
    model: str,
    message: str,
    db: AsyncSession,
    tool_used: str | None = None,
    prompt_tokens: int = 0,
    output_tokens: int = 0,
) -> int:
    """Persist an AI interaction. Returns the interaction id."""
    row = AIInteraction(
        user_id=user_id,
        mode=mode,
        provider=provider,
        model=model,
        message=message,
        tool_used=tool_used,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
    )
    db.add(row)
    await db.flush()
    return row.id


async def record_outcome(
    interaction_id: int,
    acted: bool,
    acted_within_hours: float | None,
    user_rating: int | None,
    db: AsyncSession,
) -> None:
    """Record whether the user acted on an AI output. Called from app/device."""
    row = AIOutcome(
        interaction_id=interaction_id,
        acted=acted,
        acted_within_hours=acted_within_hours,
        user_rating=user_rating,
    )
    db.add(row)
    await db.flush()


async def get_recent_interactions(
    user_id: int,
    db: AsyncSession,
    limit: int = 20,
) -> list[AIInteraction]:
    result = await db.execute(
        select(AIInteraction)
        .where(AIInteraction.user_id == user_id)
        .order_by(AIInteraction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
