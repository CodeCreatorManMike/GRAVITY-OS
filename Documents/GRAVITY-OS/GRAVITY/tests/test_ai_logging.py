import json
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.ai_client import AICompletion
from backend.services.ai_log_service import log_completion
from backend.routers import onboarding, review
from backend.models.user import User
from backend.services import layout_service


@pytest.mark.asyncio
async def test_log_completion_persists_provider_model_and_token_counts():
    db = MagicMock()
    db.flush = AsyncMock()
    completion = AICompletion(
        "AI output",
        provider="groq",
        model="llama-test",
        prompt_tokens=17,
        output_tokens=9,
    )

    await log_completion(
        user_id=42,
        mode="nudge",
        completion=completion,
        db=db,
    )

    row = db.add.call_args.args[0]
    assert row.user_id == 42
    assert row.mode == "nudge"
    assert row.message == "AI output"
    assert row.provider == "groq"
    assert row.model == "llama-test"
    assert row.prompt_tokens == 17
    assert row.output_tokens == 9
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_log_completion_uses_explicit_metadata_for_plain_strings():
    db = MagicMock()
    db.flush = AsyncMock()

    await log_completion(
        user_id=7,
        mode="review",
        completion="Review output",
        db=db,
        provider="anthropic",
        model="claude-test",
        prompt_tokens=5,
        output_tokens=3,
    )

    row = db.add.call_args.args[0]
    assert row.provider == "anthropic"
    assert row.model == "claude-test"
    assert row.prompt_tokens == 5
    assert row.output_tokens == 3


@pytest.mark.asyncio
async def test_onboarding_ai_complete_logs_the_call(monkeypatch):
    completion = AICompletion(
        "Hello",
        provider="groq",
        model="llama-test",
        prompt_tokens=2,
        output_tokens=1,
    )
    client = SimpleNamespace(complete=lambda *args: completion)
    logger = AsyncMock()
    db = MagicMock()
    monkeypatch.setattr(onboarding, "get_ai_client", lambda: client)
    monkeypatch.setattr(onboarding, "log_completion", logger)

    result = await onboarding.ai_complete("system", [], 12, db)

    assert result == "Hello"
    logger.assert_awaited_once_with(
        user_id=12,
        mode="onboarding",
        completion=completion,
        db=db,
    )


@pytest.mark.asyncio
async def test_onboarding_extraction_logs_before_parsing(monkeypatch):
    completion = AICompletion(
        "not valid json",
        provider="groq",
        model="llama-test",
        prompt_tokens=8,
        output_tokens=4,
    )
    client = SimpleNamespace(complete=lambda *args: completion)
    logger = AsyncMock()
    db = MagicMock()
    profile_data = {"motivation_style": "direct"}
    monkeypatch.setattr(onboarding, "get_ai_client", lambda: client)
    monkeypatch.setattr(onboarding, "log_completion", logger)

    result = await onboarding.extract_profile_data(
        [{"role": "user", "content": "I work best in the morning."}],
        "Sam",
        profile_data,
        12,
        db,
    )

    assert result == profile_data
    logger.assert_awaited_once_with(
        user_id=12,
        mode="onboarding",
        completion=completion,
        db=db,
    )


@pytest.mark.asyncio
async def test_layout_ranking_logs_before_parsing(monkeypatch):
    raw = json.dumps([{
        "type": "goal_arc",
        "label": "SHIP",
        "pct": 50,
        "days_left": 10,
        "on_track": True,
        "sub_label": "",
    }])
    response = SimpleNamespace(
        content=[SimpleNamespace(text=raw)],
        usage=SimpleNamespace(input_tokens=11, output_tokens=7),
    )
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: response))
    logger = AsyncMock()
    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: client)
    monkeypatch.setattr(layout_service, "log_completion", logger)

    faces = await layout_service._ai_ranked_faces(
        {"profile": {}, "current_cycle": {}, "today": {}, "recent_behaviour": {}},
        user_id=9,
        db=MagicMock(),
    )

    assert faces[0].type == "goal_arc"
    assert logger.await_args is not None
    logged = logger.await_args.kwargs
    assert logged["user_id"] == 9
    assert logged["mode"] == "layout"
    assert logged["completion"] == raw
    assert logged["prompt_tokens"] == 11
    assert logged["output_tokens"] == 7


@pytest.mark.asyncio
async def test_cycle_review_opening_logs_the_call(monkeypatch):
    goal = SimpleNamespace(
        id=4,
        statement="Ship Gravity",
        cycle_start="2026-01-01",
        cycle_end="2026-07-01",
        likelihood_score=0.7,
    )
    ctx = {
        "profile": {"name": "Sam"},
        "current_cycle": {"days_remaining": 2},
        "recent_behaviour": {
            "last_7_days_habit_completion": {"Build": [True] * 7},
            "nudge_response_rate": 0.5,
            "patterns_identified": [],
        },
    }
    response = SimpleNamespace(
        content=[SimpleNamespace(text="You reached 70 percent. What worked?")],
        usage=SimpleNamespace(input_tokens=13, output_tokens=6),
    )
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: response))
    db = MagicMock()
    db.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None))
    db.flush = AsyncMock()

    async def refresh(row):
        row.id = 55

    db.refresh = AsyncMock(side_effect=refresh)
    logger = AsyncMock()
    monkeypatch.setattr(review, "_get_active_goal", AsyncMock(return_value=goal))
    monkeypatch.setattr(review, "build_user_context", AsyncMock(return_value=ctx))
    monkeypatch.setattr(review, "get_redis", lambda: MagicMock())
    monkeypatch.setattr(review, "log_completion", logger)
    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: client)

    result = await review.start_review(
        current_user=cast(User, SimpleNamespace(id=3)),
        db=db,
    )

    assert result.review_id == 55
    assert result.message == "You reached 70 percent. What worked?"
    logger.assert_awaited_once_with(
        user_id=3,
        mode="review",
        completion="You reached 70 percent. What worked?",
        db=db,
        provider="anthropic",
        model=review.REVIEW_MODEL,
        prompt_tokens=13,
        output_tokens=6,
    )
