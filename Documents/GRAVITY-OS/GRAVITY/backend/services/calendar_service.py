"""
Calendar service — CalDAV sync (iCloud, Nextcloud, any CalDAV server).
Credentials stored encrypted in user settings (not in this file).
This service runs on-demand when user triggers sync, or nightly via scheduler.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.models.calendar_event import CalendarEvent


# ── CalDAV sync ───────────────────────────────────────────────────────────────

def _sync_caldav_sync(caldav_url: str, username: str, password: str) -> list[dict]:
    """
    Synchronous CalDAV fetch — runs in a thread via asyncio.to_thread.
    Returns a list of raw event dicts ready for upsert.
    """
    import caldav  # noqa: PLC0415 — import inside thread to avoid blocking import

    client = caldav.DAVClient(url=caldav_url, username=username, password=password)
    principal = client.principal()

    today = date.today()
    window_end = today + timedelta(days=7)

    events: list[dict] = []
    for cal in principal.calendars():
        cal_name = ""
        try:
            cal_name = str(cal.name) if cal.name else ""
        except Exception:
            pass

        try:
            results = cal.date_search(
                start=datetime(today.year, today.month, today.day),
                end=datetime(window_end.year, window_end.month, window_end.day),
                expand=True,
            )
        except Exception:
            continue

        for event in results:
            try:
                vevent = event.vobject_instance.vevent
                uid = str(vevent.uid.value) if hasattr(vevent, "uid") else ""
                title = str(vevent.summary.value) if hasattr(vevent, "summary") else ""

                dtstart = vevent.dtstart.value
                dtend_obj = vevent.dtend.value if hasattr(vevent, "dtend") else None

                all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)

                # Normalise to timezone-aware datetimes
                if all_day:
                    start_at = datetime(dtstart.year, dtstart.month, dtstart.day,
                                        tzinfo=timezone.utc)
                    if dtend_obj is None:
                        end_at = start_at + timedelta(days=1)
                    elif isinstance(dtend_obj, datetime):
                        end_at = dtend_obj if dtend_obj.tzinfo else dtend_obj.replace(tzinfo=timezone.utc)
                    else:
                        end_at = datetime(dtend_obj.year, dtend_obj.month, dtend_obj.day,
                                          tzinfo=timezone.utc)
                else:
                    start_at = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
                    if dtend_obj is None:
                        end_at = start_at + timedelta(hours=1)
                    elif isinstance(dtend_obj, datetime):
                        end_at = dtend_obj if dtend_obj.tzinfo else dtend_obj.replace(tzinfo=timezone.utc)
                    else:
                        end_at = datetime(dtend_obj.year, dtend_obj.month, dtend_obj.day,
                                          tzinfo=timezone.utc)

                events.append({
                    "uid": uid,
                    "title": title,
                    "start_at": start_at,
                    "end_at": end_at,
                    "all_day": all_day,
                    "calendar_name": cal_name,
                })
            except Exception:
                continue

    return events


async def sync_caldav(
    user_id: int,
    caldav_url: str,
    username: str,
    password: str,
    db: AsyncSession,
) -> int:
    """
    Sync CalDAV events for the next 7 days into calendar_events table.
    Credentials are used immediately and never persisted.
    Returns count of events synced, or -1 on auth failure.
    """
    try:
        raw_events = await asyncio.to_thread(
            _sync_caldav_sync, caldav_url, username, password
        )
    except Exception as exc:
        err_str = str(exc).lower()
        if any(k in err_str for k in ("401", "403", "auth", "unauthorized", "forbidden")):
            return -1
        raise

    count = 0
    for ev in raw_events:
        uid = ev["uid"]
        # Skip events without a UID — can't safely dedup
        if not uid:
            continue

        existing = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.uid == uid,
                    CalendarEvent.source == "caldav",
                )
            )
        )
        row = existing.scalar_one_or_none()

        if row is None:
            row = CalendarEvent(
                user_id=user_id,
                uid=uid,
                source="caldav",
            )
            db.add(row)

        row.title = ev["title"]
        row.start_at = ev["start_at"]
        row.end_at = ev["end_at"]
        row.all_day = ev["all_day"]
        row.calendar_name = ev["calendar_name"]

        count += 1

    await db.flush()
    return count


# ── Query helpers ─────────────────────────────────────────────────────────────

async def get_today_events(user_id: int, db: AsyncSession) -> list[dict]:
    """Return today's calendar events ordered by start time."""
    today = date.today()
    day_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_at >= day_start,
                CalendarEvent.start_at < day_end,
            )
        )
        .order_by(CalendarEvent.start_at)
    )
    events = result.scalars().all()

    return [
        {
            "title": ev.title,
            "start_time": ev.start_at.strftime("%H:%M"),
            "end_time": ev.end_at.strftime("%H:%M"),
            "all_day": ev.all_day,
        }
        for ev in events
    ]


async def get_upcoming_events(
    user_id: int,
    db: AsyncSession,
    days: int = 3,
) -> list[dict]:
    """
    Return events for the next `days` days, grouped by date.
    Returns list of {"date": "YYYY-MM-DD", "events": [{"title", "start_time", "end_time"}]}.
    """
    today = date.today()
    window_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    window_end = window_start + timedelta(days=days)

    result = await db.execute(
        select(CalendarEvent)
        .where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_at >= window_start,
                CalendarEvent.start_at < window_end,
            )
        )
        .order_by(CalendarEvent.start_at)
    )
    events = result.scalars().all()

    # Group by date
    grouped: dict[str, list[dict]] = {}
    for ev in events:
        day_key = ev.start_at.strftime("%Y-%m-%d")
        grouped.setdefault(day_key, [])
        grouped[day_key].append({
            "title": ev.title,
            "start_time": ev.start_at.strftime("%H:%M"),
            "end_time": ev.end_at.strftime("%H:%M"),
        })

    return [{"date": d, "events": evs} for d, evs in sorted(grouped.items())]
