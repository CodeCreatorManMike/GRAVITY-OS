"""
Voice router — audio in, action + TTS audio out.

POST /voice/process   multipart: audio file → transcript + tool action + TTS audio
GET  /voice/tts       ?text=... → TTS audio bytes (utility endpoint for app)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.services import voice_service
from backend.services.connection_manager import manager
from backend.config import get_settings

router = APIRouter(prefix="/voice", tags=["voice"])
settings = get_settings()

_redis_client = None


def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=False)
    return _redis_client


class VoiceResponse(BaseModel):
    transcript: str
    spoken: str
    action_type: str
    payload: dict
    interaction_id: int | None


@router.post("/process", response_model=VoiceResponse)
async def process_voice(
    audio: UploadFile = File(..., description="Raw audio file (wav/webm/ogg/mp4)"),
    return_audio: bool = Query(default=True, description="Include TTS audio in X-Audio header"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive audio from device or app.
    Returns JSON with transcript + action, plus TTS audio bytes in X-Audio-Base64 header.
    Simultaneously pushes WebSocket events to device and app.
    """
    audio_bytes = await audio.read()
    if len(audio_bytes) < 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio too short.")

    result = await voice_service.process_voice(
        user_id=current_user.id,
        audio_bytes=audio_bytes,
        db=db,
        redis=_get_redis(),
    )

    # Push action to device + app via WebSocket
    await manager.send_to_user(current_user.id, result["action_type"], result["payload"])

    # Return TTS audio as base64 in a header so JSON body stays clean
    import base64
    audio_b64 = base64.b64encode(result["audio"]).decode() if result.get("audio") else ""

    response = VoiceResponse(
        transcript=result["transcript"],
        spoken=result["spoken"],
        action_type=result["action_type"],
        payload=result["payload"],
        interaction_id=result.get("interaction_id"),
    )

    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=response.model_dump(),
        headers={"X-Audio-Base64": audio_b64} if audio_b64 else {},
    )


@router.get("/tts")
async def text_to_speech(
    text: str = Query(..., max_length=500),
    voice: str = Query(default="en-GB-SoniaNeural"),
    current_user: User = Depends(get_current_user),
):
    """Utility: convert any text to speech. Used by app for reading generated content."""
    if not text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text is empty.")
    audio_bytes = await voice_service.synthesise(text, voice=voice)
    return Response(content=audio_bytes, media_type="audio/mpeg")
