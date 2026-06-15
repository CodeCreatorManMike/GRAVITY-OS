"""
Research router — web search, content extraction, exercise database.

  POST /research/search      ← SearXNG web search
  POST /research/fetch       ← Jina Reader content extraction from URL
  POST /research/goal        ← full search + extract pipeline for a goal query
  GET  /research/exercises   ← Wger exercise database search
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/research", tags=["research"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    num_results: int = 5

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class FetchRequest(BaseModel):
    url: str

class ResearchRequest(BaseModel):
    query: str
    num_sources: int = 3

class ExerciseSearchRequest(BaseModel):
    query: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/search", response_model=list[SearchResult])
async def search_web(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search the web via SearXNG. Returns [] if SearXNG is not running."""
    from backend.services.research_service import web_search
    results = await web_search(req.query, num_results=min(req.num_results, 20))
    return [SearchResult(**r) for r in results]


@router.post("/fetch")
async def fetch_url(
    req: FetchRequest,
    current_user: User = Depends(get_current_user),
):
    """Extract clean text content from a URL via Jina Reader."""
    if not req.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid URL")
    from backend.services.research_service import extract_page_content
    content = await extract_page_content(req.url)
    return {"url": req.url, "content": content, "chars": len(content)}


@router.post("/goal")
async def research_for_goal(
    req: ResearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Full research pipeline: search → extract top sources in parallel.
    Use this when the user asks Gravity to research something related to their goal.
    """
    from backend.services.research_service import research_goal
    result = await research_goal(req.query, num_sources=min(req.num_sources, 5))
    return result


@router.get("/exercises")
async def search_exercises(
    query: str,
    current_user: User = Depends(get_current_user),
):
    """Search the Wger open exercise database."""
    from backend.services.fitness_service import search_exercises as _search
    results = await _search(query)
    return {"query": query, "exercises": results}


@router.get("/exercises/suggest")
async def suggest_exercises(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggest exercises based on the user's active goal."""
    from sqlalchemy import select
    from backend.models.user import Goal
    from backend.services.fitness_service import suggest_exercises_for_goal

    result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id, Goal.is_active == True).limit(1)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        return {"exercises": []}

    exercises = await suggest_exercises_for_goal(goal.statement or "")
    return {"goal": goal.statement, "exercises": exercises}
