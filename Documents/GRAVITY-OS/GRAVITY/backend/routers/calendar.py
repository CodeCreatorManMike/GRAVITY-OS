"""
Calendar router.

Endpoints:
  POST /calendar/sync       ← trigger CalDAV sync (credentials used immediately, never stored)
  GET  /calendar/today      ← today's events
  GET  /calendar/upcoming   ← next 3 days of events
  POST /calendar/location   ← set user's lat/lon + timezone
  GET  /calendar/weather    ← current weather for user's saved location
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User
from backend.models.user_location import UserLocation
from backend.routers.auth import get_current_user
from backend.config import get_settings
from backend.services.calendar_service import sync_caldav, get_today_events, get_upcoming_events
from backend.services.weather_service import get_weather_for_user, get_weather_glyph

router = APIRouter(prefix="/calendar", tags=["calendar"])
settings = get_settings()

_redis_client = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# ── Schemas ───────────────────────────────────────────────────────────────────

class CalDAVSyncRequest(BaseModel):
    caldav_url: str
    username: str
    password: str  # used immediately, never stored


class CalDAVSyncResponse(BaseModel):
    synced: int
    message: str


class CalendarEventOut(BaseModel):
    title: str
    start_time: str
    end_time: str
    all_day: bool = False


class TodayEventsResponse(BaseModel):
    date: str
    events: list[CalendarEventOut]


class DayEvents(BaseModel):
    date: str
    events: list[CalendarEventOut]


class UpcomingEventsResponse(BaseModel):
    days: list[DayEvents]


class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    city: str = Field(default="")
    timezone: str = Field(default="Europe/London")


class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    city: str
    timezone: str


class WeatherResponse(BaseModel):
    temperature_c: float
    glyph: str
    description: str
    precipitation_chance: int
    sunrise: str
    sunset: str


# ── WMO code → human description ─────────────────────────────────────────────

_WMO_DESCRIPTION: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def _wmo_description(code: int) -> str:
    return _WMO_DESCRIPTION.get(code, "Unknown")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/sync", response_model=CalDAVSyncResponse)
async def trigger_caldav_sync(
    req: CalDAVSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a CalDAV sync for the next 7 days.
    Credentials are used immediately and never persisted.
    """
    count = await sync_caldav(
        user_id=current_user.id,
        caldav_url=req.caldav_url,
        username=req.username,
        password=req.password,
        db=db,
    )

    if count == -1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CalDAV authentication failed — check URL, username, and password.",
        )

    return CalDAVSyncResponse(
        synced=count,
        message=f"Synced {count} event(s) for the next 7 days.",
    )


@router.get("/today", response_model=TodayEventsResponse)
async def today_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return today's calendar events ordered by start time."""
    from datetime import date
    events = await get_today_events(current_user.id, db)
    return TodayEventsResponse(
        date=str(date.today()),
        events=[CalendarEventOut(**e) for e in events],
    )


@router.get("/upcoming", response_model=UpcomingEventsResponse)
async def upcoming_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return events for the next 3 days, grouped by date."""
    grouped = await get_upcoming_events(current_user.id, db, days=3)
    return UpcomingEventsResponse(
        days=[
            DayEvents(date=g["date"], events=[CalendarEventOut(**e) for e in g["events"]])
            for g in grouped
        ]
    )


@router.post("/location", response_model=LocationResponse)
async def set_location(
    req: LocationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store or update the user's lat/lon and timezone for weather lookups."""
    result = await db.execute(
        select(UserLocation).where(UserLocation.user_id == current_user.id)
    )
    loc = result.scalar_one_or_none()

    if loc is None:
        loc = UserLocation(user_id=current_user.id)
        db.add(loc)

    loc.latitude = req.latitude
    loc.longitude = req.longitude
    loc.city = req.city
    loc.timezone = req.timezone

    await db.flush()

    return LocationResponse(
        latitude=loc.latitude,
        longitude=loc.longitude,
        city=loc.city,
        timezone=loc.timezone,
    )


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current weather for the user's saved location."""
    redis = get_redis()
    data = await get_weather_for_user(current_user.id, db, redis)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location saved. POST /calendar/location first.",
        )

    current = data.get("current", {})
    daily = data.get("daily", {})

    weather_code = int(current.get("weather_code", 0))
    temp_c = float(current.get("temperature_2m", 0.0))

    # Precipitation probability — first day in the daily forecast
    precip_list = daily.get("precipitation_probability_max", [0])
    precip_chance = int(precip_list[0]) if precip_list else 0

    sunrise_list = daily.get("sunrise", [""])
    sunset_list = daily.get("sunset", [""])
    sunrise_raw = sunrise_list[0] if sunrise_list else ""
    sunset_raw = sunset_list[0] if sunset_list else ""

    # Open-Meteo returns full ISO datetimes; surface only HH:MM
    def _hhmm(iso_str: str) -> str:
        if "T" in iso_str:
            return iso_str.split("T")[1][:5]
        return iso_str

    return WeatherResponse(
        temperature_c=round(temp_c, 1),
        glyph=get_weather_glyph(weather_code),
        description=_wmo_description(weather_code),
        precipitation_chance=precip_chance,
        sunrise=_hhmm(sunrise_raw),
        sunset=_hhmm(sunset_raw),
    )
