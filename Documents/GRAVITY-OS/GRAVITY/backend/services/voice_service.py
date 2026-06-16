"""
Voice service — full pipeline: audio → STT → Claude tool-calling → TTS → audio bytes.

STT:  faster-whisper (self-hosted, free, runs on CPU, ~300ms for short clips)
LLM:  Claude with structured tool-calling (tool routing lives here, not on device)
TTS:  edge-tts (free Microsoft neural TTS, no API key, high quality)

Tools available to Claude:
  add_task, complete_task, start_timer, stop_timer,
  answer_question, create_document, get_schedule
"""
from __future__ import annotations

import asyncio
import io
import json
import tempfile
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.services.context_service import build_user_context
from backend.services.memory_service import recall_similar
from backend.services.ai_log_service import log_interaction
import redis.asyncio as aioredis

settings = get_settings()

# ── STT ───────────────────────────────────────────────────────────────────────

_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        # base model: good accuracy, ~150MB, runs on CPU
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model


async def transcribe(audio_bytes: bytes) -> str:
    """Convert raw audio bytes (wav/webm/ogg) to text via faster-whisper."""
    def _run():
        model = _get_whisper()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            f.write(audio_bytes)
            f.flush()
            segments, _ = model.transcribe(f.name, beam_size=5, language="en")
            return " ".join(s.text for s in segments).strip()
    return await asyncio.to_thread(_run)


# ── TTS ───────────────────────────────────────────────────────────────────────

async def synthesise(text: str, voice: str = "en-GB-SoniaNeural") -> bytes:
    """Convert text to speech via edge-tts. Returns MP3 bytes."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "add_task",
        "description": "Add a new task or to-do item for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":    {"type": "string", "description": "Task title"},
                "due_date": {"type": "string", "description": "ISO date string, optional"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "complete_task",
        "description": "Mark an existing task as completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_title": {"type": "string", "description": "Title or partial title of the task to complete"},
            },
            "required": ["task_title"],
        },
    },
    {
        "name": "start_timer",
        "description": "Start a countdown timer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "duration_minutes": {"type": "integer", "description": "Timer duration in minutes"},
                "label":            {"type": "string", "description": "What the timer is for"},
            },
            "required": ["duration_minutes"],
        },
    },
    {
        "name": "stop_timer",
        "description": "Stop the currently running timer.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "answer_question",
        "description": "Answer a question about the user's goals, habits, schedule, or study material.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question":     {"type": "string"},
                "context_type": {"type": "string", "enum": ["goals", "habits", "schedule", "study", "general"]},
            },
            "required": ["question"],
        },
    },
    {
        "name": "create_document",
        "description": "Generate a document such as study notes, a summary, or a study plan. Delivered to the app.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":         {"type": "string"},
                "doc_type":      {"type": "string", "enum": ["study_notes", "summary", "study_plan", "revision_questions", "general"]},
                "content_query": {"type": "string", "description": "What the document should cover"},
            },
            "required": ["title", "doc_type", "content_query"],
        },
    },
    {
        "name": "get_schedule",
        "description": "Retrieve the user's schedule or calendar events for a given day.",
        "input_schema": {
            "type": "object",
            "properties": {
                "day": {"type": "string", "description": "ISO date or 'today'/'tomorrow'"},
            },
            "required": ["day"],
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

async def _execute_tool(
    tool_name: str,
    tool_input: dict,
    user_id: int,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> dict:
    """
    Execute the tool Claude selected. Returns a dict with:
      action_type: str — WebSocket event type to push to device + app
      payload:     dict — data for the event
      spoken:      str  — what to say back to the user
    """
    if tool_name == "add_task":
        from backend.models.user import Goal
        title = tool_input["title"]
        priority = tool_input.get("priority", "medium")
        due_date = tool_input.get("due_date")
        # Add as a habit/task — store as a simple goal milestone for now
        return {
            "action_type": "TASK_ADDED",
            "payload": {"title": title, "priority": priority, "due_date": due_date},
            "spoken": f"Added to your list: {title}.",
        }

    elif tool_name == "complete_task":
        title = tool_input["task_title"]
        return {
            "action_type": "TASK_COMPLETED",
            "payload": {"task_title": title},
            "spoken": f"Marked as done: {title}. Good work.",
        }

    elif tool_name == "start_timer":
        mins = tool_input["duration_minutes"]
        label = tool_input.get("label", "Focus")
        return {
            "action_type": "TIMER_START",
            "payload": {"duration_minutes": mins, "label": label},
            "spoken": f"{label} timer started. {mins} minutes on the clock.",
        }

    elif tool_name == "stop_timer":
        return {
            "action_type": "TIMER_STOP",
            "payload": {},
            "spoken": "Timer stopped.",
        }

    elif tool_name == "answer_question":
        question = tool_input["question"]
        ctx = await build_user_context(user_id, db, redis)
        memories = await recall_similar(user_id, question, db, limit=5)
        memory_text = "\n".join(f"- {m.content}" for m in memories) if memories else ""
        return {
            "action_type": "VOICE_ANSWER",
            "payload": {"question": question},
            "spoken": f"I'll check that for you. {question}",
            "_needs_llm_answer": True,
            "_question": question,
            "_context": ctx,
            "_memories": memory_text,
        }

    elif tool_name == "create_document":
        title = tool_input["title"]
        doc_type = tool_input["doc_type"]
        return {
            "action_type": "DOCUMENT_GENERATING",
            "payload": {"title": title, "doc_type": doc_type},
            "spoken": f"Generating your {doc_type.replace('_', ' ')} now. Check your app in a moment.",
            "_needs_doc_generation": True,
            "_doc_title": title,
            "_doc_type": doc_type,
            "_content_query": tool_input["content_query"],
        }

    elif tool_name == "get_schedule":
        day = tool_input["day"]
        return {
            "action_type": "VOICE_ANSWER",
            "payload": {"day": day},
            "spoken": f"Let me check your schedule for {day}.",
            "_needs_schedule": True,
            "_day": day,
        }

    return {
        "action_type": "VOICE_ANSWER",
        "payload": {},
        "spoken": "Done.",
    }


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def process_voice(
    user_id: int,
    audio_bytes: bytes,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> dict:
    """
    Full voice pipeline. Returns:
      transcript:   str
      spoken:       str   — what to say back
      audio:        bytes — TTS audio (MP3)
      action_type:  str   — WebSocket event to push
      payload:      dict  — event data
      interaction_id: int — for outcome logging
    """
    import anthropic

    # 1. STT
    transcript = await transcribe(audio_bytes)
    if not transcript:
        audio = await synthesise("I didn't catch that. Could you try again?")
        return {"transcript": "", "spoken": "I didn't catch that.", "audio": audio,
                "action_type": "VOICE_NO_INPUT", "payload": {}, "interaction_id": None}

    # 2. Build user context for system prompt
    ctx = await build_user_context(user_id, db, redis)
    memories = await recall_similar(user_id, transcript, db, limit=4)
    memory_text = "\n".join(f"- {m.content}" for m in memories) if memories else "None yet."

    goal = ctx.get("current_cycle", {}).get("goal", "No active goal")
    name = ctx.get("profile", {}).get("name", "User")

    system_prompt = f"""You are Gravity, an AI accountability companion for {name}.
Their current goal: {goal}
Relevant memory about this user:
{memory_text}

The user has spoken to you. Select the right tool to respond. If none fit, use answer_question.
Be direct. Never use markdown. Responses will be spoken aloud."""

    # 3. Claude tool-calling
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = await asyncio.to_thread(
        lambda: client.messages.create(
            model=settings.anthropic_model,
            max_tokens=512,
            system=system_prompt,
            tools=TOOLS,
            messages=[{"role": "user", "content": transcript}],
        )
    )

    # 4. Extract tool use or text
    tool_name = None
    tool_input: dict[str, Any] = {}
    spoken_direct = ""

    for block in response.content:
        if block.type == "tool_use":
            tool_name = block.name
            tool_input = block.input
            break
        elif block.type == "text":
            spoken_direct = block.text

    # 5. Execute tool
    if tool_name:
        result = await _execute_tool(tool_name, tool_input, user_id, db, redis)
        spoken = result["spoken"]
        action_type = result["action_type"]
        payload = result["payload"]

        # If the tool needs a follow-up LLM call (answer_question)
        if result.get("_needs_llm_answer"):
            answer_response = await asyncio.to_thread(
                lambda: client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=256,
                    system=f"Answer this question about the user concisely. Speak directly, no markdown.\nContext: {json.dumps(result['_context'], default=str)}\nMemory:\n{result['_memories']}",
                    messages=[{"role": "user", "content": result["_question"]}],
                )
            )
            spoken = answer_response.content[0].text if answer_response.content else spoken
            payload["answer"] = spoken
    else:
        spoken = spoken_direct or "I'm not sure how to help with that."
        action_type = "VOICE_ANSWER"
        payload = {"answer": spoken}

    # 6. Log interaction
    interaction_id = await log_interaction(
        user_id=user_id,
        mode="voice",
        provider="anthropic",
        model=settings.anthropic_model,
        message=spoken,
        db=db,
        tool_used=tool_name,
        prompt_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

    # 7. TTS
    audio = await synthesise(spoken)

    return {
        "transcript": transcript,
        "spoken": spoken,
        "audio": audio,
        "action_type": action_type,
        "payload": payload,
        "interaction_id": interaction_id,
    }
