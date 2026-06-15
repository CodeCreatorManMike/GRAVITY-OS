"""
Push notification service — Expo Push API.

Sends push notifications to users whose device isn't connected via WebSocket.
Used as a fallback when the physical device / app is not live.

Expo Push API is free for up to 1,000 notifications/month, then pay-as-you-go.
No Expo account or SDK key needed for the basic API.
"""
import asyncio
from typing import Optional
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.push import PushToken
from backend.services.connection_manager import manager

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push_if_offline(
    user_id: int,
    title: str,
    body: str,
    data: Optional[dict] = None,
    db: AsyncSession = None,
) -> bool:
    """
    Send an Expo push notification if the user has no active WebSocket connection.
    Returns True if push was sent, False if user is online (WebSocket active) or no token.
    """
    # Only push if the user has no active WS connection (device not live)
    if manager.is_connected(user_id):
        return False

    if db is None:
        return False

    # Get all active push tokens for this user
    result = await db.execute(
        select(PushToken).where(
            PushToken.user_id == user_id,
            PushToken.is_active == True,
        )
    )
    tokens = result.scalars().all()
    if not tokens:
        return False

    messages = [
        {
            "to": t.token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
            "priority": "high",
        }
        for t in tokens
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[push] failed for user {user_id}: {e}")
        return False


async def deactivate_invalid_token(token: str, db: AsyncSession) -> None:
    """Mark a token inactive after Expo reports it as invalid/expired."""
    result = await db.execute(select(PushToken).where(PushToken.token == token))
    row = result.scalar_one_or_none()
    if row:
        row.is_active = False
        await db.flush()
