"""
PDF generator — produces downloadable reports for users.
Templates in backend/templates/pdf/.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

# ── Template directory ────────────────────────────────────────────────────────

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "pdf"


# ── Private sync renderer ─────────────────────────────────────────────────────

def _render_pdf(template_name: str, data: dict) -> bytes:
    """
    Sync. Load Jinja2 template from backend/templates/pdf/{template_name}.html,
    render with data, run WeasyPrint → return PDF bytes.
    """
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from weasyprint import HTML

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(f"{template_name}.html")
    html_string = template.render(**data)
    pdf_bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes


# ── Public async wrapper ──────────────────────────────────────────────────────

async def build_pdf(template_name: str, data: dict) -> bytes:
    """Generic async wrapper — offloads sync WeasyPrint to a thread."""
    return await asyncio.to_thread(_render_pdf, template_name, data)


# ── Report generators ─────────────────────────────────────────────────────────

async def generate_cycle_review_pdf(ctx: dict, review: dict) -> bytes:
    """
    6-month cycle review PDF.
    ctx  — user context dict from context_service.build_user_context()
    review — CycleReview data dict
    """
    data = {"ctx": ctx, "review": review}
    return await build_pdf("cycle_review", data)


async def generate_habit_report_pdf(ctx: dict, analytics: dict) -> bytes:
    """
    30-day habit analytics report PDF.
    ctx       — user context dict
    analytics — habit analytics dict (completion_rate, streak, habits list, etc.)
    """
    data = {"ctx": ctx, "analytics": analytics}
    return await build_pdf("habit_report", data)
