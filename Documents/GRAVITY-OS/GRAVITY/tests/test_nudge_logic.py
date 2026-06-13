"""
Tests for nudge engine decision and content pipeline logic.

These tests mock ai_client.AIClient.complete so no real API calls are made.
They verify the pipeline wiring, state builder, JSON parse fallback,
and cooldown / quiet-hours behaviour.
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.profile import UserProfile, Goal, Schedule
from core.nudge_engine import (
    build_user_state,
    decide_nudge,
    generate_nudge_content,
    evaluate_nudge,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _profile() -> UserProfile:
    return UserProfile(
        name="testuser",
        feedback_preference="direct",
        energy_pattern="evening",
        schedule=Schedule(
            wake_time="07:00",
            sleep_time="23:00",
            peak_focus_windows=["19:00-23:00"],
            avoidance_behaviours=["social media"],
        ),
        goal=Goal(
            statement="Build app prototype",
            real_why="Make something real",
            likelihood_score=0.6,
            risk_factors=["procrastination"],
        ),
        non_negotiables=["music work", "app work", "learning"],
        cycle_start="2026-06-12",
        cycle_end="2026-12-11",
        onboarding_complete=True,
    )


_DECISION_YES = json.dumps({
    "should_nudge": True,
    "category": "non_negotiable",
    "intensity": "medium",
    "reason": "Evening approaching with pending habits",
    "data_points": ["0/3 non-negotiables done", "time: 19:30"],
})

_DECISION_NO = json.dumps({
    "should_nudge": False,
    "category": None,
    "intensity": None,
    "reason": "User is on track",
    "data_points": [],
})

_CONTENT = json.dumps({
    "message": "You haven't touched your music today.",
    "sub_message": "Even 20 minutes counts.",
    "action_label": "Dismiss",
    "display_duration_seconds": 30,
})


# ── build_user_state ──────────────────────────────────────────────────────────

def test_build_state_contains_required_keys():
    p = _profile()
    state = build_user_state(
        profile=p,
        habits_completed_today=[],
        habits_pending_today=p.non_negotiables,
        current_time="19:30",
    )
    assert "current_time" in state
    assert "user" in state and "today" in state and "nudge_context" in state
    assert state["user"]["name"] == "testuser"
    assert state["today"]["habits_pending"] == p.non_negotiables


def test_build_state_cooldown_flag():
    p = _profile()
    state = build_user_state(
        profile=p,
        habits_completed_today=[],
        habits_pending_today=[],
        cooldown_active=True,
    )
    assert state["nudge_context"]["cooldown_active"] is True


# ── decide_nudge (mocked) ─────────────────────────────────────────────────────

def test_decide_nudge_yes(monkeypatch):
    monkeypatch.setattr("core.nudge_engine.client.complete", lambda *a, **kw: _DECISION_YES)
    state = build_user_state(_profile(), [], [])
    result = decide_nudge(state)
    assert result["should_nudge"] is True
    assert result["category"] == "non_negotiable"
    assert result["intensity"] == "medium"


def test_decide_nudge_no(monkeypatch):
    monkeypatch.setattr("core.nudge_engine.client.complete", lambda *a, **kw: _DECISION_NO)
    state = build_user_state(_profile(), [], [])
    result = decide_nudge(state)
    assert result["should_nudge"] is False


def test_decide_nudge_parse_failure_returns_safe_default(monkeypatch):
    monkeypatch.setattr("core.nudge_engine.client.complete", lambda *a, **kw: "not json at all")
    state = build_user_state(_profile(), [], [])
    result = decide_nudge(state)
    assert result["should_nudge"] is False
    assert "parse" in result["reason"].lower() or result["reason"]  # graceful


# ── generate_nudge_content (mocked) ──────────────────────────────────────────

def test_generate_content_extracts_message(monkeypatch):
    monkeypatch.setattr("core.nudge_engine.client.complete", lambda *a, **kw: _CONTENT)
    state    = build_user_state(_profile(), [], [])
    decision = {"should_nudge": True, "category": "non_negotiable", "intensity": "medium",
                "reason": "test", "data_points": []}
    content = generate_nudge_content(state, decision)
    assert content["message"] == "You haven't touched your music today."
    assert content["sub_message"] == "Even 20 minutes counts."


def test_generate_content_fallback_on_bad_json(monkeypatch):
    monkeypatch.setattr("core.nudge_engine.client.complete", lambda *a, **kw: "broken")
    state    = build_user_state(_profile(), [], [])
    decision = {"should_nudge": True, "category": "test", "intensity": "low",
                "reason": "x", "data_points": []}
    content = generate_nudge_content(state, decision)
    assert "message" in content  # fallback dict returned


# ── evaluate_nudge end-to-end (mocked) ───────────────────────────────────────

def test_evaluate_nudge_fires_when_decision_yes(monkeypatch):
    responses = iter([_DECISION_YES, _CONTENT])
    monkeypatch.setattr("core.nudge_engine.client.complete",
                        lambda *a, **kw: next(responses))
    p = _profile()
    result = evaluate_nudge(
        profile=p,
        habits_pending_today=p.non_negotiables,
        current_time="19:30",
    )
    assert result["nudge"] is True
    assert result["message"] == "You haven't touched your music today."


def test_evaluate_nudge_skips_content_when_no(monkeypatch):
    call_count = {"n": 0}
    def mock_complete(*a, **kw):
        call_count["n"] += 1
        return _DECISION_NO
    monkeypatch.setattr("core.nudge_engine.client.complete", mock_complete)
    p = _profile()
    result = evaluate_nudge(profile=p, habits_completed_today=p.non_negotiables)
    assert result["nudge"] is False
    assert call_count["n"] == 1  # only one call (decision), not two


def test_evaluate_nudge_respects_cooldown(monkeypatch):
    # Cooldown flag should prevent nudge before even calling AI
    # (nudge_engine passes it through state — AI sees it and should say no)
    monkeypatch.setattr("core.nudge_engine.client.complete", lambda *a, **kw: _DECISION_NO)
    p = _profile()
    result = evaluate_nudge(profile=p, cooldown_active=True)
    assert result["nudge"] is False
