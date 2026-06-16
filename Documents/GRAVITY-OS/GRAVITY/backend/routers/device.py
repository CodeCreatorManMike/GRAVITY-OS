import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.config import get_settings
from backend.services.layout_service import generate_layout
from backend.schemas.face import FACE_TYPES

router = APIRouter(prefix="/device", tags=["device"])

settings = get_settings()

# Firmware version — bump this when a new firmware build ships
FIRMWARE_VERSION = "0.1.0"

_redis_client = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# ── Schemas ───────────────────────────────────────────────────────────────────

class PairRequest(BaseModel):
    device_id: str          # unique ID burned into firmware (MAC-derived)
    firmware_version: str

class PairResponse(BaseModel):
    paired: bool
    user_id: int
    firmware_version: str
    latest_firmware: str
    update_available: bool

class FirmwareResponse(BaseModel):
    version: str
    # In future: download_url, changelog, size_bytes

class HeartbeatResponse(BaseModel):
    ok: bool
    latest_firmware: str
    update_available: bool

class FacePrefsRequest(BaseModel):
    face_types: list[str]

class FacePrefsResponse(BaseModel):
    face_types: list[str]


# ── Routes ────────────────────────────────────────────────────────────────────

_FACE_PREFS_KEY = "face_prefs:{}"


@router.put("/layout", response_model=FacePrefsResponse)
async def set_face_prefs(
    req: FacePrefsRequest,
    current_user: User = Depends(get_current_user),
):
    """Store user's preferred face types and order (max 5). AI fills content for these types."""
    valid = [t for t in req.face_types if t in FACE_TYPES][:5]
    await get_redis().set(_FACE_PREFS_KEY.format(current_user.id), json.dumps(valid))
    return FacePrefsResponse(face_types=valid)


@router.get("/layout/prefs", response_model=FacePrefsResponse)
async def get_face_prefs(
    current_user: User = Depends(get_current_user),
):
    """Return user's pinned face types. Empty list = fully AI-ranked."""
    raw = await get_redis().get(_FACE_PREFS_KEY.format(current_user.id))
    return FacePrefsResponse(face_types=json.loads(raw) if raw else [])


@router.get("/state")
async def get_device_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current layout JSON for the user's device."""
    layout = await generate_layout(current_user.id, db, get_redis())
    return layout


@router.post("/pair", response_model=PairResponse)
async def pair_device(
    req: PairRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Link a physical device to this account.
    The device calls this on first boot after WiFi setup.
    Returns the latest firmware version so the device knows if it needs to update.
    """
    update_available = req.firmware_version != FIRMWARE_VERSION
    return PairResponse(
        paired=True,
        user_id=current_user.id,
        firmware_version=req.firmware_version,
        latest_firmware=FIRMWARE_VERSION,
        update_available=update_available,
    )


@router.get("/firmware", response_model=FirmwareResponse)
async def get_firmware_info(
    current_user: User = Depends(get_current_user),
):
    """Return the current latest firmware version. Device polls this on heartbeat."""
    return FirmwareResponse(version=FIRMWARE_VERSION)


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def device_heartbeat(
    current_user: User = Depends(get_current_user),
):
    """
    Lightweight heartbeat for devices that can't maintain a persistent WebSocket
    (e.g. deep sleep cycles). Returns firmware update status.
    """
    return HeartbeatResponse(
        ok=True,
        latest_firmware=FIRMWARE_VERSION,
        update_available=False,
    )
