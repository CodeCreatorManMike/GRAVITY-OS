"""
Document service — PDF ingestion pipeline.
Upload → extract text → chunk → ready for memory embedding.
PyMuPDF import name is 'fitz'.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ── Text extraction ───────────────────────────────────────────────────────────

def _extract_pdf_text_sync(file_bytes: bytes) -> tuple[str, int]:
    """Open PDF from bytes and extract all text. Returns (text, page_count)."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages), len(pages)


def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Sync. Open PDF from bytes, extract all page text, return joined string.
    Call via asyncio.to_thread() from async contexts.
    """
    text, _ = _extract_pdf_text_sync(file_bytes)
    return text


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 400) -> list[str]:
    """
    Split text into word-based chunks of ~chunk_size words with a 50-word overlap.
    Returns list of chunk strings.
    """
    words = text.split()
    if not words:
        return []

    overlap = 50
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap  # back up by overlap for next chunk

    return chunks


# ── Pipeline ──────────────────────────────────────────────────────────────────

async def process_uploaded_pdf(
    user_id: int,
    filename: str,
    file_bytes: bytes,
    db: "AsyncSession",
) -> dict:
    """
    Full ingestion pipeline:
    1. Extract text (in thread — PyMuPDF is sync)
    2. Chunk text
    3. Store each chunk as a memory
    Returns metadata dict with filename, pages, chunks, chars.
    """
    # Step 1: extract (sync → thread)
    text, page_count = await asyncio.to_thread(_extract_pdf_text_sync, file_bytes)

    # Step 2: chunk
    chunks = chunk_text(text)

    # Step 3: store memories (lazy import avoids circular)
    from backend.services import memory_service

    for chunk in chunks:
        if chunk.strip():
            await memory_service.store_memory(
                user_id=user_id,
                content=chunk,
                memory_type="document",
                source=filename,
                db=db,
            )

    return {
        "filename": filename,
        "pages": page_count,
        "chunks": len(chunks),
        "chars": len(text),
    }
