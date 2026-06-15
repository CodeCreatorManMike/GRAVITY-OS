"""
Files router — PDF upload/processing and PDF report generation.

POST /files/upload        upload a PDF, extract text into memory
GET  /files               list uploaded files for this user
DELETE /files/{id}        delete a file record (memories remain — they belong to the user)
POST /files/report/cycle  generate and return a cycle-review PDF
POST /files/report/habits generate and return a 30-day habits report PDF
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func as sqlfunc

from backend.database import get_db
from backend.models.file import UserFile
from backend.models.user import Habit, HabitLog, User
from backend.models.integration import CycleReview
from backend.routers.auth import get_current_user
from backend.services import document_service, pdf_generator
from backend.services.context_service import build_user_context

router = APIRouter(prefix="/files", tags=["files"])

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Schemas ───────────────────────────────────────────────────────────────────

class FileResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    size_bytes: int
    pages: int
    chunks: int
    uploaded_at: str

    class Config:
        from_attributes = True


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF. Text is extracted and stored as memory chunks."""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB limit.",
        )

    # Process: extract + chunk + store memories
    result = await document_service.process_uploaded_pdf(
        user_id=current_user.id,
        filename=file.filename,
        file_bytes=file_bytes,
        db=db,
    )

    # Persist file metadata
    user_file = UserFile(
        user_id=current_user.id,
        filename=file.filename,
        file_type="pdf",
        size_bytes=len(file_bytes),
        pages=result["pages"],
        chunks=result["chunks"],
    )
    db.add(user_file)
    await db.commit()
    await db.refresh(user_file)

    return FileResponse(
        id=user_file.id,
        filename=user_file.filename,
        file_type=user_file.file_type,
        size_bytes=user_file.size_bytes,
        pages=user_file.pages,
        chunks=user_file.chunks,
        uploaded_at=user_file.uploaded_at.isoformat(),
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[FileResponse])
async def list_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all uploaded files for the current user, newest first."""
    result = await db.execute(
        select(UserFile)
        .where(UserFile.user_id == current_user.id)
        .order_by(UserFile.uploaded_at.desc())
    )
    files = result.scalars().all()
    return [
        FileResponse(
            id=f.id,
            filename=f.filename,
            file_type=f.file_type,
            size_bytes=f.size_bytes,
            pages=f.pages,
            chunks=f.chunks,
            uploaded_at=f.uploaded_at.isoformat(),
        )
        for f in files
    ]


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file record. Associated memories are retained (they belong to the user)."""
    result = await db.execute(
        select(UserFile).where(
            UserFile.id == file_id,
            UserFile.user_id == current_user.id,
        )
    )
    user_file = result.scalar_one_or_none()
    if user_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    await db.delete(user_file)
    await db.commit()


# ── Report helpers ────────────────────────────────────────────────────────────

async def _build_habit_analytics(user: User, db: AsyncSession) -> dict:
    """Compute 30-day habit analytics for the report."""
    from datetime import datetime, timezone

    today = date.today()
    thirty_days_ago = today - timedelta(days=29)

    # Fetch active habits
    habits_result = await db.execute(
        select(Habit).where(Habit.user_id == user.id, Habit.is_active == True)
    )
    habits = habits_result.scalars().all()

    if not habits:
        return {
            "date_from": thirty_days_ago.isoformat(),
            "date_to": today.isoformat(),
            "completion_rate": 0.0,
            "streak": 0,
            "total_completions": 0,
            "habits": [],
            "patterns": [],
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

    habit_ids = [h.id for h in habits]
    logs_result = await db.execute(
        select(HabitLog).where(
            HabitLog.user_id == user.id,
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.date >= thirty_days_ago.isoformat(),
        )
    )
    logs = logs_result.scalars().all()

    # Per-habit completion rates
    from collections import defaultdict
    log_map: dict[int, set[str]] = defaultdict(set)
    for log in logs:
        if log.completed:
            log_map[log.habit_id].add(log.date)

    total_possible = len(habits) * 30
    total_completions = sum(len(dates) for dates in log_map.values())
    overall_rate = total_completions / total_possible if total_possible else 0.0

    # Best streak: consecutive days where at least one habit was completed
    completed_dates = set()
    for dates in log_map.values():
        completed_dates.update(dates)

    streak = 0
    current_streak = 0
    for i in range(30):
        d = (today - timedelta(days=i)).isoformat()
        if d in completed_dates:
            current_streak += 1
            streak = max(streak, current_streak)
        else:
            current_streak = 0

    habits_list = [
        {
            "name": h.name,
            "completion_rate": len(log_map[h.id]) / 30,
            "is_non_negotiable": h.is_non_negotiable,
        }
        for h in habits
    ]

    return {
        "date_from": thirty_days_ago.isoformat(),
        "date_to": today.isoformat(),
        "completion_rate": overall_rate,
        "streak": streak,
        "total_completions": total_completions,
        "habits": habits_list,
        "patterns": [],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


async def _build_cycle_review_data(user: User, db: AsyncSession) -> dict:
    """Build cycle review dict from the most recent CycleReview row."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(CycleReview)
        .where(CycleReview.user_id == user.id)
        .order_by(CycleReview.created_at.desc())
        .limit(1)
    )
    cycle_review = result.scalar_one_or_none()

    # Fetch habits for the report
    habits_result = await db.execute(
        select(Habit).where(Habit.user_id == user.id, Habit.is_active == True)
    )
    habits = habits_result.scalars().all()

    today = date.today()
    thirty_days_ago = today - timedelta(days=29)

    from collections import defaultdict
    if habits:
        habit_ids = [h.id for h in habits]
        logs_result = await db.execute(
            select(HabitLog).where(
                HabitLog.user_id == user.id,
                HabitLog.habit_id.in_(habit_ids),
                HabitLog.date >= thirty_days_ago.isoformat(),
            )
        )
        logs = logs_result.scalars().all()
        log_map: dict[int, set[str]] = defaultdict(set)
        for log in logs:
            if log.completed:
                log_map[log.habit_id].add(log.date)

        habits_data = [
            {
                "name": h.name,
                "completion_rate": len(log_map[h.id]) / 30,
                "streak": len(log_map[h.id]),
                "is_non_negotiable": h.is_non_negotiable,
            }
            for h in habits
        ]
    else:
        habits_data = []

    return {
        "goal": None,  # populated from ctx.goal in the template
        "habits": habits_data,
        "patterns": cycle_review.patterns if cycle_review and hasattr(cycle_review, "patterns") else [],
        "ai_summary": cycle_review.ai_summary if cycle_review and hasattr(cycle_review, "ai_summary") else "",
        "cycle_start": cycle_review.cycle_start if cycle_review and hasattr(cycle_review, "cycle_start") else "",
        "cycle_end": cycle_review.cycle_end if cycle_review and hasattr(cycle_review, "cycle_end") else "",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ── Report: cycle review ──────────────────────────────────────────────────────

@router.post("/report/cycle")
async def report_cycle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and return the 6-month cycle review as a PDF download."""
    ctx = await build_user_context(current_user.id, db)
    review = await _build_cycle_review_data(current_user, db)

    pdf_bytes = await pdf_generator.generate_cycle_review_pdf(ctx, review)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=gravity_cycle_review.pdf"},
    )


# ── Report: habits ────────────────────────────────────────────────────────────

@router.post("/report/habits")
async def report_habits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and return the 30-day habit analytics report as a PDF download."""
    ctx = await build_user_context(current_user.id, db)
    analytics = await _build_habit_analytics(current_user, db)

    pdf_bytes = await pdf_generator.generate_habit_report_pdf(ctx, analytics)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=gravity_habit_report.pdf"},
    )
