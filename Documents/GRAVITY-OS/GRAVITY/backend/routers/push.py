"""
Push notification router.

  POST /push/register    ← app registers/updates its Expo push token
  DELETE /push/token     ← app unregisters (logout)
  POST /push/test        ← send a test push (dev only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.database import get_db
from backend.models.user import User
from backend.models.push import PushToken
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/push", tags=["push"])


class RegisterTokenRequest(BaseModel):
    token: str       # ExponentPushToken[xxxxxx]
    platform: str = "ios"


class RegisterTokenResponse(BaseModel):
    token: str
    registered: bool


@router.post("/register", response_model=RegisterTokenResponse)
async def register_token(
    req: RegisterTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or refresh an Expo push token for this user's device."""
    if not req.token.startswith("ExponentPushToken["):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Expo push token format",
        )

    # Upsert: if token already exists for another user, deactivate it
    existing = await db.execute(select(PushToken).where(PushToken.token == req.token))
    row = existing.scalar_one_or_none()

    if row is None:
        row = PushToken(
            user_id=current_user.id,
            token=req.token,
            platform=req.platform,
            is_active=True,
        )
        db.add(row)
    else:
        row.user_id = current_user.id
        row.platform = req.platform
        row.is_active = True

    await db.flush()
    return RegisterTokenResponse(token=req.token, registered=True)


@router.delete("/token", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_token(
    req: RegisterTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a push token on logout."""
    result = await db.execute(
        select(PushToken).where(
            and_(PushToken.token == req.token, PushToken.user_id == current_user.id)
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.is_active = False


@router.post("/test", status_code=status.HTTP_200_OK)
async def test_push(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a test push notification to all registered tokens for this user."""
    from backend.services.push_service import send_push_if_offline
    from backend.services.connection_manager import manager

    # Temporarily disconnect to force push (test only)
    was_connected = manager.is_connected(current_user.id)
    sent = await send_push_if_offline(
        current_user.id,
        title="GRAVITY",
        body="Push notifications are working.",
        data={"test": True},
        db=db,
    )
    return {"sent": sent, "was_online": was_connected}
