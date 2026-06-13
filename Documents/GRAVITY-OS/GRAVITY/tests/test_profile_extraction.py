"""Tests for profile save/load cycle and field constraints."""

import os
import json
import pytest
import tempfile
from datetime import date

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.profile import UserProfile, Schedule, Goal, save_profile, load_profile


def _full_profile() -> UserProfile:
    return UserProfile(
        name="Michael",
        personality_summary="Driven creative, procrastination risk.",
        motivation_style="intrinsic",
        energy_pattern="evening",
        self_awareness_level="moderate",
        failure_response="analyse",
        feedback_preference="direct",
        schedule=Schedule(
            wake_time="06:20",
            sleep_time="00:00",
            peak_focus_windows=["19:00-23:00"],
            known_dead_zones=["17:00-18:00"],
            realistic_daily_hours=4,
            avoidance_behaviours=["social media", "videos"],
        ),
        goal=Goal(
            statement="Build app prototype and release a single",
            real_why="Make a name for myself",
            likelihood_score=0.6,
            milestone_structure=["prototype", "single release"],
            risk_factors=["procrastination", "distraction"],
        ),
        non_negotiables=["music work", "app work", "learning"],
        cycle_start="2026-06-12",
        cycle_end="2026-12-11",
        onboarding_complete=True,
        onboarding_phase=5,
    )


def test_save_and_load_round_trip(tmp_path):
    profile = _full_profile()
    path = save_profile(profile, profiles_dir=str(tmp_path))
    assert os.path.exists(path)

    loaded = load_profile("michael", profiles_dir=str(tmp_path))
    assert loaded is not None
    assert loaded.name == "Michael"   # name field preserves original case
    assert loaded.goal.statement == profile.goal.statement
    assert loaded.goal.likelihood_score == profile.goal.likelihood_score
    assert loaded.non_negotiables == profile.non_negotiables
    assert loaded.schedule.wake_time == "06:20"
    assert loaded.onboarding_complete is True


def test_load_nonexistent_returns_none(tmp_path):
    result = load_profile("nobody", profiles_dir=str(tmp_path))
    assert result is None


def test_filename_normalises_spaces(tmp_path):
    profile = UserProfile(name="John Smith")
    save_profile(profile, profiles_dir=str(tmp_path))
    loaded = load_profile("john smith", profiles_dir=str(tmp_path))
    assert loaded is not None


def test_profile_json_is_valid(tmp_path):
    profile = _full_profile()
    path = save_profile(profile, profiles_dir=str(tmp_path))
    with open(path) as f:
        data = json.load(f)
    assert data["name"] == "Michael"   # name field preserves case
    assert "goal" in data and "schedule" in data and "non_negotiables" in data


def test_likelihood_score_range():
    goal = Goal(likelihood_score=0.6)
    assert 0.0 <= goal.likelihood_score <= 1.0


def test_defaults_are_safe():
    profile = UserProfile()
    assert profile.onboarding_complete is False
    assert profile.onboarding_phase == 0
    assert profile.non_negotiables == []
    assert profile.goal.likelihood_score == 0.0


def test_schedule_round_trip(tmp_path):
    profile = _full_profile()
    save_profile(profile, profiles_dir=str(tmp_path))
    loaded = load_profile("michael", profiles_dir=str(tmp_path))
    assert loaded.schedule.peak_focus_windows == ["19:00-23:00"]
    assert loaded.schedule.avoidance_behaviours == ["social media", "videos"]
