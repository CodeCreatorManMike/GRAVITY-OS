"""
Memory router — CRUD for user long-term memories.

POST /memory/store     manually store a memory
GET  /memory/search    semantic search by query string
GET  /memory/recent    last 10 memories
DELETE /memory/{id}    delete a specific memory
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.models.memory import Memory
from backend.services.memory_service import store_memory, recall_similar, get_recent_memories

router = APIRouter(prefix="/memory", tags=["memory"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class StoreMemoryRequest(BaseModel):
    content: str
    memory_type: str = "insight"


class MemoryResponse(BaseModel):
    id: int
    content: str
    memory_type: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/store", response_model=MemoryResponse)
async def store_memory_endpoint(
    body: StoreMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually store a memory — text the user wants Gravity to remember."""
    memory = await store_memory(
        user_id=current_user.id,
        content=body.content,
        memory_type=body.memory_type,
        source="user",
        db=db,
    )
    return memory


@router.get("/search", response_model=list[MemoryResponse])
async def search_memories(
    query: str = Query(..., description="Natural language search query"),
    limit: int = Query(5, ge=1, le=50),
    memory_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search over the user's memories."""
    from backend.services.memory_service import get_embedder
    query_vec = get_embedder().encode(query).tolist()

    stmt = (
        select(Memory)
        .where(Memory.user_id == current_user.id)
        .order_by(Memory.embedding.cosine_distance(query_vec))
        .limit(limit)
    )
    if memory_type is not None:
        stmt = (
            select(Memory)
            .where(Memory.user_id == current_user.id, Memory.memory_type == memory_type)
            .order_by(Memory.embedding.cosine_distance(query_vec))
            .limit(limit)
        )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/recent", response_model=list[MemoryResponse])
async def recent_memories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the 10 most recently stored memories."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == current_user.id)
        .order_by(Memory.created_at.desc())
        .limit(10)
    )
    return result.scalars().all()


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific memory by ID."""
    result = await db.execute(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == current_user.id,
        )
    )
    memory = result.scalar_one_or_none()
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(memory)
