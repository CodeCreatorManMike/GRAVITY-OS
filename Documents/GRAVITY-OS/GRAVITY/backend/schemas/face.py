"""
Face card schemas — canonical JSON shapes for all 5 device face types.

Device firmware has one MicroPython renderer per face type.
Backend always produces one of these typed payloads; firmware never guesses structure.

Face types:
  goal_arc        — perimeter arc showing goal progress %
  task_list       — ring-checkbox list of up to 6 tasks
  habit_heatmap   — 7-column heatmap grid of habit completions
  timer           — depleting arc countdown
  study_progress  — study goal arc + lesson/module counter
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


# ── goal_arc ─────────────────────────────────────────────────────────────────

class GoalArcFace(BaseModel):
    type: Literal["goal_arc"] = "goal_arc"
    label: str = Field(..., max_length=24, description="Goal name, truncated")
    pct: float = Field(..., ge=0, le=100, description="Completion percentage")
    days_left: int = Field(..., ge=0)
    on_track: bool = True
    sub_label: str = Field(default="", max_length=32, description="E.g. '£6,800 of £10,000'")


# ── task_list ─────────────────────────────────────────────────────────────────

class TaskItem(BaseModel):
    title: str = Field(..., max_length=40)
    done: bool = False
    active: bool = False   # currently in-progress item


class TaskListFace(BaseModel):
    type: Literal["task_list"] = "task_list"
    tasks: list[TaskItem] = Field(..., max_length=6)
    done_count: int = 0
    total_count: int = 0
    next_label: str = Field(default="", max_length=32, description="E.g. 'NEXT: Deep work 09:30'")


# ── habit_heatmap ─────────────────────────────────────────────────────────────

class HabitRow(BaseModel):
    name: str = Field(..., max_length=20)
    days: list[bool] = Field(..., min_length=7, max_length=7, description="Mon–Sun bools")


class HabitHeatmapFace(BaseModel):
    type: Literal["habit_heatmap"] = "habit_heatmap"
    habits: list[HabitRow] = Field(..., max_length=5)
    streak: int = Field(default=0, ge=0)
    week_label: str = Field(default="THIS WEEK", max_length=16)


# ── timer ────────────────────────────────────────────────────────────────────

class TimerFace(BaseModel):
    type: Literal["timer"] = "timer"
    label: str = Field(default="FOCUS", max_length=20)
    duration_seconds: int = Field(..., gt=0)
    remaining_seconds: int = Field(..., ge=0)
    running: bool = True


# ── study_progress ────────────────────────────────────────────────────────────

class StudyProgressFace(BaseModel):
    type: Literal["study_progress"] = "study_progress"
    subject: str = Field(..., max_length=24)
    pct: float = Field(..., ge=0, le=100, description="Overall module completion %")
    current_lesson: int = Field(default=1, ge=1)
    total_lessons: int = Field(default=1, ge=1)
    target_grade: str = Field(default="", max_length=8, description="E.g. '80%' or 'A*'")
    streak_days: int = Field(default=0, ge=0)


# ── Union type for layout service ─────────────────────────────────────────────

FaceCard = GoalArcFace | TaskListFace | HabitHeatmapFace | TimerFace | StudyProgressFace

FACE_TYPES = {"goal_arc", "task_list", "habit_heatmap", "timer", "study_progress"}
