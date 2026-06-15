"""
Weather service — Open-Meteo API.
No API key required. Results cached in Redis (1-hour TTL).
"""

import json
from typing import Optional

import httpx
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user_location import UserLocation

WEATHER_TTL = 3600  # 1 hour
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ── WMO weather code → ASCII glyph ───────────────────────────────────────────

def get_weather_glyph(weather_code: int) -> str:
    """Map WMO weather interpretation codes to ASCII display glyphs."""
    if weather_code == 0:
        return "SUN"
    if weather_code in (1, 2):
        return "PART"
    if weather_code == 3:
        return "CLD"
    if weather_code in (45, 48):
        return "FOG"
    if 51 <= weather_code <= 67:
        return "RAIN"
    if 71 <= weather_code <= 77:
        return "SNOW"
    if 80 <= weather_code <= 82:
        return "SHWRS"
    if 95 <= weather_code <= 99:
        return "STRM"
    return "UNK"


# ── Fetch + cache ─────────────────────────────────────────────────────────────

async def get_weather(lat: float, lon: float, redis: aioredis.Redis) -> dict:
    """
    Fetch current weather and 3-day forecast from Open-Meteo.
    Results cached in Redis for 1 hour keyed by rounded lat/lon.
    """
    cache_key = f"weather:{lat:.2f}:{lon:.2f}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,precipitation,wind_speed_10m",
        "daily": "sunrise,sunset,precipitation_probability_max,temperature_2m_max,temperature_2m_min",
        "forecast_days": 3,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    await redis.setex(cache_key, WEATHER_TTL, json.dumps(data))
    return data


# ── User-scoped helper ────────────────────────────────────────────────────────

async def get_weather_for_user(
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> Optional[dict]:
    """
    Look up the user's saved location and return weather data, or None if no
    location is stored.
    """
    result = await db.execute(
        select(UserLocation).where(UserLocation.user_id == user_id)
    )
    loc = result.scalar_one_or_none()
    if loc is None:
        return None

    return await get_weather(loc.latitude, loc.longitude, redis)
