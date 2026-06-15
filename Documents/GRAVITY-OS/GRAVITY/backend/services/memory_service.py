"""
Long-term memory service — pgvector + sentence-transformers.

The embedder is a lazy singleton: imported only on first call so the server
starts immediately without downloading the 80MB model.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.memory import Memory

# ── Lazy embedder singleton ───────────────────────────────────────────────────

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


# ── Core operations ───────────────────────────────────────────────────────────

async def store_memory(
    user_id: int,
    content: str,
    memory_type: str,
    source: str,
    db: AsyncSession,
) -> Memory:
    """
    Embed content and persist a Memory row.
    Calls db.flush() but NOT db.commit() — the caller owns the transaction.
    """
    embedding = get_embedder().encode(content).tolist()
    memory = Memory(
        user_id=user_id,
        content=content,
        embedding=embedding,
        memory_type=memory_type,
        source=source,
    )
    db.add(memory)
    await db.flush()
    return memory


async def recall_similar(
    user_id: int,
    query: str,
    db: AsyncSession,
    limit: int = 5,
    memory_type: Optional[str] = None,
) -> list[str]:
    """
    Return content strings of the memories most semantically similar to query.
    Uses pgvector cosine distance (lower = more similar), ordered ASC.
    """
    query_vec = get_embedder().encode(query).tolist()

    stmt = (
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.embedding.cosine_distance(query_vec))
        .limit(limit)
    )
    if memory_type is not None:
        stmt = (
            select(Memory)
            .where(Memory.user_id == user_id, Memory.memory_type == memory_type)
            .order_by(Memory.embedding.cosine_distance(query_vec))
            .limit(limit)
        )

    result = await db.execute(stmt)
    memories = result.scalars().all()
    return [m.content for m in memories]


async def store_conversation_memory(
    user_id: int,
    role: str,
    content: str,
    db: AsyncSession,
) -> None:
    """
    Store a conversation turn as a memory.
    Only stores user/assistant messages with meaningful content (>20 chars).
    """
    if role not in ("user", "assistant"):
        return
    if len(content) <= 20:
        return
    await store_memory(
        user_id=user_id,
        content=content,
        memory_type="conversation",
        source=f"conversation:{role}",
        db=db,
    )


async def get_recent_memories(
    user_id: int,
    db: AsyncSession,
    limit: int = 10,
) -> list[str]:
    """Return the most recent memories for the user, newest first."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.created_at.desc())
        .limit(limit)
    )
    memories = result.scalars().all()
    return [m.content for m in memories]
