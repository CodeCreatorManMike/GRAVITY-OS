from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.config import get_settings
from backend.services.layout_service import generate_layout

router = APIRouter(prefix="/device", tags=["device"])

settings = get_settings()

_redis_client = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


@router.get("/state")
async def get_device_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current layout JSON for the user's device."""
    layout = await generate_layout(current_user.id, db, get_redis())
    return layout
