import asyncio
import json
import os
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from backend.database import get_db
from backend.models.user import User, Goal, Habit
from backend.routers.auth import get_current_user
from backend.config import get_settings

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
settings = get_settings()

# ── Lazy singletons ──────────────────────────────────────────────────────────

_ai_client = None
_redis_client = None


def get_ai_client():
    global _ai_client
    if _ai_client is None:
        from core.ai_client import AIClient
        _ai_client = AIClient()
    return _ai_client


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


# ── Constants ────────────────────────────────────────────────────────────────

PHASES = [
    (1, "phase1_identity.txt"),
    (2, "phase2_routine.txt"),
    (3, "phase3_goal.txt"),
    (4, "phase4_nonneg.txt"),
    (5, "phase5_feedback.txt"),
]

PHASE_NAMES = {
    1: "Who Are You",
    2: "Your Routine",
    3: "Your Goal",
    4: "Non-Negotiables",
    5: "Feedback Style",
}

SESSION_TTL = 60 * 60 * 24  # 24 hours


# ── Schemas ───────────────────────────────────────────────────────────────────

class StartResponse(BaseModel):
    message: str
    phase: int
    phase_name: str


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    message: str
    phase: int
    phase_name: str
    onboarding_complete: bool


# ── Internal helpers ──────────────────────────────────────────────────────────

def _prompt_path(filename: str) -> str:
    base = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(base, "..", "..", "core", "prompts", filename))


def load_prompt(filename: str) -> str:
    with open(_prompt_path(filename), "r") as f:
        return f.read()


async def ai_complete(system_prompt: str, messages: list, max_tokens: int = 200) -> str:
    """Run the blocking AIClient.complete() in a thread pool with a 30 s hard timeout."""
    client = get_ai_client()
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(client.complete, system_prompt, messages, max_tokens),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI response timed out — please try again",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI call failed: {exc}",
        )


def session_key(user_id: int) -> str:
    return f"onboarding:{user_id}"


async def load_session(user_id: int) -> dict | None:
    raw = await get_redis().get(session_key(user_id))
    return json.loads(raw) if raw else None


async def save_session(user_id: int, session: dict) -> None:
    await get_redis().setex(session_key(user_id), SESSION_TTL, json.dumps(session))


async def delete_session(user_id: int) -> None:
    await get_redis().delete(session_key(user_id))


def build_system_prompt(phase_file: str, profile_data: dict, name: str) -> str:
    """Load the phase prompt and append what we already know about the user."""
    prompt = load_prompt(phase_file)
    context = [f"User name: {name}"]

    if profile_data.get("personality_summary"):
        context.append(f"Personality: {profile_data['personality_summary']}")
    if profile_data.get("energy_pattern"):
        context.append(f"Energy pattern: {profile_data['energy_pattern']}")
    if profile_data.get("motivation_style"):
        context.append(f"Motivation style: {profile_data['motivation_style']}")

    sched = profile_data.get("schedule") or {}
    if sched.get("realistic_daily_hours"):
        context.append(f"Realistic daily hours: {sched['realistic_daily_hours']}")
    if sched.get("avoidance_behaviours"):
        context.append(f"Avoidance behaviours: {', '.join(sched['avoidance_behaviours'])}")

    goal = profile_data.get("goal") or {}
    if goal.get("statement"):
        context.append(f"Goal: {goal['statement']}")
    if goal.get("real_why"):
        context.append(f"Real why: {goal['real_why']}")

    if len(context) > 1:
        prompt += "\n\nWhat you already know about this user:\n" + "\n".join(context)
    return prompt


async def extract_profile_data(full_transcript: list, name: str, profile_data: dict) -> dict:
    """
    Silent extraction: send the full transcript to the AI with the extraction
    prompt and merge the returned JSON into profile_data. Never visible to user.
    On any failure (timeout, bad JSON, etc.) returns existing profile_data unchanged.
    """
    system_prompt = load_prompt("extract_profile.txt")

    transcript_text = ""
    for turn in full_transcript:
        role = "Gravity" if turn["role"] == "assistant" else name
        transcript_text += f"{role}: {turn['content']}\n\n"

    messages = [{
        "role": "user",
        "content": f"Extract structured profile data from this onboarding conversation:\n\n{transcript_text}",
    }]

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(get_ai_client().complete, system_prompt, messages, 1000),
            timeout=30.0,
        )
        clean = response.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1]
            if clean.startswith("json"):
                clean = clean[4:]
        extracted = json.loads(clean.strip())
        for key, value in extracted.items():
            if value is not None:
                profile_data[key] = value
    except Exception:
        pass  # silent — keep whatever profile_data we already have

    return profile_data


async def save_profile_to_db(user_id: int, profile_data: dict, db: AsyncSession) -> None:
    """Write all extracted onboarding data to the database."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.personality_summary = profile_data.get("personality_summary") or ""
    user.motivation_style = profile_data.get("motivation_style") or ""
    user.energy_pattern = profile_data.get("energy_pattern") or ""
    user.self_awareness_level = profile_data.get("self_awareness_level") or ""
    user.failure_response = profile_data.get("failure_response") or ""
    user.feedback_preference = profile_data.get("feedback_preference") or "direct"
    user.onboarding_complete = True
    user.onboarding_phase = 5

    sched = profile_data.get("schedule") or {}
    user.wake_time = sched.get("wake_time") or "07:00"
    user.sleep_time = sched.get("sleep_time") or "23:00"
    user.peak_focus_windows = sched.get("peak_focus_windows") or []
    user.known_dead_zones = sched.get("known_dead_zones") or []
    user.realistic_daily_hours = float(sched.get("realistic_daily_hours") or 1.0)
    user.avoidance_behaviours = sched.get("avoidance_behaviours") or []

    goal_data = profile_data.get("goal") or {}
    today = date.today()
    db.add(Goal(
        user_id=user_id,
        statement=goal_data.get("statement") or "",
        real_why=goal_data.get("real_why") or "",
        likelihood_score=float(goal_data.get("likelihood_score") or 0.0),
        milestone_structure=goal_data.get("milestone_structure") or [],
        risk_factors=goal_data.get("risk_factors") or [],
        cycle_start=str(today),
        cycle_end=str(today + timedelta(days=182)),
        is_active=True,
    ))

    for nn in (profile_data.get("non_negotiables") or [])[:5]:
        db.add(Habit(
            user_id=user_id,
            name=nn,
            is_non_negotiable=True,
            is_active=True,
        ))


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartResponse)
async def start_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Begin the onboarding conversation. Returns Gravity's Phase 1 opening message."""
    if current_user.onboarding_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding already complete",
        )

    # Clear any stale session so the user always gets a fresh start
    await delete_session(current_user.id)

    _, phase_file = PHASES[0]
    system_prompt = build_system_prompt(phase_file, {}, current_user.name)

    opening = await ai_complete(
        system_prompt,
        [{"role": "user", "content": "[start]"}],
        max_tokens=150,
    )
    opening_clean = opening.replace("PHASE_COMPLETE", "").strip()

    await save_session(current_user.id, {
        "phase": 1,
        "phase_messages": [
            {"role": "user", "content": "[start]"},
            {"role": "assistant", "content": opening},
        ],
        "full_transcript": [
            {"role": "assistant", "content": opening_clean},
        ],
        "profile_data": {},
    })

    return StartResponse(
        message=opening_clean,
        phase=1,
        phase_name=PHASE_NAMES[1],
    )


@router.post("/message", response_model=MessageResponse)
async def send_message(
    req: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a user message in the onboarding conversation.
    Returns Gravity's response. When a phase completes, returns the opening
    message of the next phase (or marks onboarding_complete=true on phase 5).
    """
    if current_user.onboarding_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding already complete",
        )

    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty",
        )

    session = await load_session(current_user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active onboarding session — call POST /onboarding/start first",
        )

    phase: int = session["phase"]
    phase_messages: list = session["phase_messages"]
    full_transcript: list = session["full_transcript"]
    profile_data: dict = session["profile_data"]

    # Append user message to both histories
    phase_messages.append({"role": "user", "content": req.message})
    full_transcript.append({"role": "user", "content": req.message})

    # Call AI for current phase
    _, phase_file = PHASES[phase - 1]
    system_prompt = build_system_prompt(phase_file, profile_data, current_user.name)
    response = await ai_complete(system_prompt, phase_messages, max_tokens=200)

    phase_complete = "PHASE_COMPLETE" in response
    response_clean = response.replace("PHASE_COMPLETE", "").strip()

    # Record AI response
    phase_messages.append({"role": "assistant", "content": response})
    full_transcript.append({"role": "assistant", "content": response_clean or response})

    # ── Mid-phase: just save and return ──────────────────────────────────────
    if not phase_complete:
        session.update({"phase_messages": phase_messages, "full_transcript": full_transcript})
        await save_session(current_user.id, session)
        return MessageResponse(
            message=response_clean,
            phase=phase,
            phase_name=PHASE_NAMES[phase],
            onboarding_complete=False,
        )

    # ── Phase completed — silent extraction ──────────────────────────────────
    profile_data = await extract_profile_data(full_transcript, current_user.name, profile_data)

    if phase < 5:
        # Advance to next phase and get its opening message
        next_phase = phase + 1
        _, next_phase_file = PHASES[next_phase - 1]
        next_system_prompt = build_system_prompt(next_phase_file, profile_data, current_user.name)

        next_opening = await ai_complete(
            next_system_prompt,
            [{"role": "user", "content": "[start]"}],
            max_tokens=150,
        )
        next_opening_clean = next_opening.replace("PHASE_COMPLETE", "").strip()
        full_transcript.append({"role": "assistant", "content": next_opening_clean})

        await save_session(current_user.id, {
            "phase": next_phase,
            "phase_messages": [
                {"role": "user", "content": "[start]"},
                {"role": "assistant", "content": next_opening},
            ],
            "full_transcript": full_transcript,
            "profile_data": profile_data,
        })

        return MessageResponse(
            message=next_opening_clean,
            phase=next_phase,
            phase_name=PHASE_NAMES[next_phase],
            onboarding_complete=False,
        )

    # ── All 5 phases done — persist to DB and clean up ───────────────────────
    await save_profile_to_db(current_user.id, profile_data, db)
    await delete_session(current_user.id)

    return MessageResponse(
        message=response_clean or "Setup complete. Your profile has been saved.",
        phase=5,
        phase_name=PHASE_NAMES[5],
        onboarding_complete=True,
    )
