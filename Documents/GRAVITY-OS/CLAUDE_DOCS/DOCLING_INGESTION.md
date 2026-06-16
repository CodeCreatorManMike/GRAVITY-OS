# GRAVITY — Docling Ingestion & User Knowledge Pipeline

**How Docling turns the documents a user uploads into structured, retrievable
knowledge that makes Gravity more accurate over time and lets the product evolve
with each user's specific goals.**

Last updated: June 2026

---

## What This Document Covers

The Knowledge Base feature promises that Gravity "builds continuously across every
conversation, upload, and interaction." Conversations are already handled by the
silent-extraction pattern. **Uploads are the missing half.** A user hands Gravity a
training programme, a CV, a business plan, a set of study notes — and the device is
supposed to read it, understand it, and use it to give better advice and tracking.

Docling is the component that turns those raw files into something the AI can
actually reason over. This doc explains what it is, why it was chosen, how it plugs
into the existing pgvector + sentence-transformers memory system, and the exact role
it plays in **accuracy** (better answers now) and **evolution** (the device knowing
the user better across 6-month cycles).

---

## 1 — What Docling Is

**Licence:** Apache 2.0
**Cost:** Free, runs fully local — no API, no per-document billing, no internet required
**Repo:** https://github.com/docling-project/docling
**Site:** https://www.docling.ai/
**Docs:** https://docling-project.github.io/docling/
**Install:** `pip install docling` (requires Python 3.10+ — you run 3.12.3)

Docling is an IBM Research project, now under the Linux Foundation, that converts
messy real-world documents into clean, structured, machine-readable form. It takes
PDF, DOCX, PPTX, HTML, Markdown, and images and produces a unified `DoclingDocument`
that preserves layout, reading order, headings, and tables — then exports to clean
Markdown or JSON.

The reason it matters for Gravity specifically: raw text extraction (e.g. plain
PyMuPDF `get_text()`) flattens a document into a soup of characters. A two-column
training plan, a CV with a sidebar, a table of weekly targets — all collapse into
unordered noise. Docling keeps the structure, which directly determines how well the
content chunks for retrieval. **Structure-aware ingestion is the difference between
"found something vaguely related" and "found the exact week of the plan the user
asked about."**

### Why Docling over the alternatives

| Tool | Verdict for Gravity |
|---|---|
| **Docling** | **Chosen.** Best structure preservation, local-first, OCR for scans, single clean Markdown output. Ideal for chunking. |
| PyMuPDF | Keep for fast raw-text / image / page extraction. Worse structure on complex layouts. Already in stack. |
| Unstructured | Broader format coverage (email, EPUB) but heavier deps and weaker PDF partitioning. Add only if a format Docling misses appears. |
| LangChain/LlamaIndex loaders | These wrap Docling anyway. No reason to take the framework just for the loader. |

Local-first is the deciding factor alongside quality: user-uploaded documents are
sensitive (CVs, business plans, personal goals). Docling processes them on your
backend with no third-party API in the loop, which keeps the data path clean for the
privacy posture the product depends on.

---

## 2 — Where It Sits in the System

Docling is a **pre-processing stage** that runs once per uploaded file, before
anything touches the AI. It does not replace the `AIClient` abstraction and does not
own any inference. It feeds the same `memories` table the conversation pipeline
already writes to.

```
User uploads a file (companion app)
        │
        ▼
Backend receives file  ──►  Docling parses to structured Markdown
        │                          (runs in asyncio.to_thread — CPU-heavy, blocking)
        ▼
Structure-aware chunking  (split on headings, sub-split long sections)
        │
        ▼
sentence-transformers embeds each chunk  (asyncio.to_thread, 384-dim vector)
        │
        ▼
Stored in PostgreSQL  →  memories table  (memory_type = 'document')
        │
        ▼
At query time: same retrieval path as conversation memories
        │
        ▼
Top-k chunks injected into system prompt  →  AIClient.complete()
        │
        ▼
Groq / Claude / Ollama answers with the user's own documents as context
```

The key architectural point: **once a document is chunked and embedded, it is just
more rows in `memories`.** Retrieval, re-ranking, and prompt injection do not care
whether a memory came from a conversation or an uploaded PDF. This keeps the system
provider-agnostic and avoids any new moving parts in the inference path.

---

## 3 — What You Need

```bash
pip install docling
```

First run downloads the layout/OCR models automatically (a few hundred MB, cached
after). On the Hetzner VPS this is a one-time cost. No API keys, no config required
for the default pipeline.

Add to the Stage 2 install block in `OPEN_SOURCE_STACK.md`:

```bash
# Stage 2 (knowledge base + memory) — add docling
pip install docling
```

---

## 4 — Code Pattern

This follows your non-negotiable async rule: Docling parsing and embedding are both
CPU-bound and blocking, so both are wrapped in `asyncio.to_thread()` with the same
discipline as every AI call in the backend.

### 4.1 Parsing

```python
# integrations/ingest.py
import asyncio
from docling.document_converter import DocumentConverter

_converter = DocumentConverter()  # load once at startup, reuse

def _parse_sync(path: str) -> str:
    result = _converter.convert(path)
    return result.document.export_to_markdown()

async def parse_to_markdown(path: str) -> str:
    # CPU-heavy + blocking — never run on the event loop directly
    return await asyncio.to_thread(_parse_sync, path)
```

### 4.2 Structure-aware chunking

Docling gives you Markdown with real headings, so chunk on structure rather than
blindly cutting every N characters. Split on headings first, then sub-split any
section longer than ~500 tokens with ~50 tokens of overlap so context isn't severed
mid-thought.

```python
import re

def chunk_markdown(md: str, target_tokens: int = 500, overlap: int = 50) -> list[str]:
    # Split on markdown headers (## / ###) to keep semantic sections together
    sections = re.split(r"\n(?=#{1,6}\s)", md)
    chunks: list[str] = []
    for section in sections:
        words = section.split()
        if len(words) <= target_tokens:
            chunks.append(section.strip())
        else:
            step = target_tokens - overlap
            for i in range(0, len(words), step):
                chunks.append(" ".join(words[i : i + target_tokens]))
    return [c for c in chunks if c.strip()]
```

> Token counting here is approximated by word count for simplicity. If you want exact
> token budgets, swap in `tiktoken` or the tokenizer of whichever model is active —
> but word-count is good enough for chunk sizing and adds no dependency.

### 4.3 Full ingestion into the existing memory system

This reuses the `embed` and `remember` helpers from `core/rag.py`:

```python
# integrations/ingest.py (continued)
from core.rag import embed  # the asyncio.to_thread-wrapped embedder
from sqlalchemy import text

async def ingest_document(session, user_id: int, path: str, source_name: str):
    md = await parse_to_markdown(path)
    chunks = chunk_markdown(md)

    for idx, chunk in enumerate(chunks):
        vec = await embed(chunk)
        await session.execute(
            text("""
                INSERT INTO memories
                    (user_id, content, embedding, memory_type, source, chunk_index)
                VALUES
                    (:uid, :c, CAST(:v AS vector), 'document', :src, :idx)
            """),
            {"uid": user_id, "c": chunk, "v": str(vec),
             "src": source_name, "idx": idx},
        )
    await session.commit()
    return {"chunks": len(chunks), "source": source_name}
```

This assumes two small additions to the `memories` table — `source` (filename, so
the AI can cite where context came from) and `chunk_index` (ordering, so adjacent
chunks can be re-stitched if needed):

```sql
ALTER TABLE memories ADD COLUMN IF NOT EXISTS source       VARCHAR(255);
ALTER TABLE memories ADD COLUMN IF NOT EXISTS chunk_index  INT;
```

---

## 5 — How This Improves Accuracy

Accuracy here means: the AI answers about *this user's actual situation*, not generic
advice. Docling-fed context does three things.

**It grounds answers in the user's real material.** When a user with an uploaded
marathon plan asks "what should I run today," retrieval pulls the relevant week of
*their* plan rather than the model inventing a generic schedule. The answer is
correct because it's sourced from the document, not hallucinated.

**It enables citation.** Because each chunk carries its `source` filename, the system
prompt can instruct the AI to say "according to your training programme…". This makes
Gravity's advice traceable and trustworthy, which matters for a device whose whole
value proposition is that it knows the user precisely.

**It feeds the silent-extraction pattern.** A newly uploaded document can be passed
through a one-off extraction call (the same invisible-second-call pattern used in
onboarding) to pull structured facts — "user's goal race is 2 Oct", "user benches
60kg" — and write them as high-value `memory_type = 'pattern'` rows. These then
surface in *every* future relevant query, not just ones that happen to match the raw
chunk text.

> **Quality upgrade when needed:** once a user has many documents, embedding
> similarity alone can return loosely-related chunks. Add the cross-encoder re-ranker
> already noted in the RAG plan (`cross-encoder/ms-marco-MiniLM-L6-v2`): retrieve top
> ~20 by vector, re-rank to the best 5. This is the single biggest precision bump and
> it's ~30 lines on top of what's here.

---

## 6 — How This Drives Evolution

Evolution is the 6-month-cycle promise: "by cycle 3, the device knows the user's
patterns better than most people in their life." Document ingestion is how the
knowledge base actually deepens rather than just accumulating chat logs.

**Documents become permanent context.** Conversation transcripts are summarised and
the raw deleted after 7 days (per the data-retention policy). Documents the user
chooses to share are durable knowledge — they stay in `memories` as `'document'`
rows and remain retrievable for the life of the goal. The knowledge base grows in
*depth* (richer per-goal context), not just volume.

**It supports the archive-don't-discard principle.** When a goal changes between
cycles, its documents aren't deleted — they're marked archived (add a
`archived_at` timestamp or a `cycle_id` to scope retrieval). The system can still
reason over "what the user was working toward last cycle and why it changed," which
is exactly the contextual, non-generic memory the product is built around.

**It makes the evolving UI smarter.** The UI layout is AI-generated from what the AI
knows about the user. The more grounded, document-backed context the AI has, the more
specific the layout JSON it can produce — a study-goal user who uploaded a syllabus
gets a UI that reflects the actual modules, not a generic progress ring.

**It powers agentic research with the user's own inputs.** The research feature
already searches the web and synthesises. Docling lets that synthesis include the
user's uploaded material — so a "build me a revision plan" request can be grounded in
the actual syllabus they gave Gravity, producing a downloadable plan that's genuinely
theirs.

---

## 7 — Build Order (Stage 2)

A pragmatic sequence so this lands cleanly inside the existing backend:

1. `pip install docling`; add to the Stage 2 install block.
2. Run the `ALTER TABLE` migration for `source` / `chunk_index` (Alembic).
3. Build `integrations/ingest.py` — `parse_to_markdown`, `chunk_markdown`,
   `ingest_document` (above).
4. Add an upload endpoint: accept file → save to temp → `ingest_document` →
   return chunk count. Wrap the whole thing with the same 30s-timeout discipline
   as the AI endpoints.
5. Confirm retrieval: upload a real document, ask a question that can only be
   answered from it, verify the relevant chunk is pulled and cited.
6. (When quality demands) add the cross-encoder re-ranker to the retrieval step.
7. (When goals start cycling) add archive scoping so old-cycle documents don't
   pollute current retrieval.

---

## 8 — Things to Watch

- **First-run model download.** Docling pulls models on first conversion. Trigger one
  conversion at deploy time so the first real user upload isn't slow.
- **CPU cost on the VPS.** Parsing is heavier than plain text extraction. The Hetzner
  CX22 will handle single-user uploads fine; if ingestion volume grows, push it to a
  Celery background task rather than blocking the request.
- **Async discipline.** Both Docling parsing and embedding are blocking. They go
  through `asyncio.to_thread()` — no exceptions, same rule as every AI call.
- **OCR is optional and slower.** Docling can OCR scanned PDFs, but the OCR path is
  heavier. It's on for image-based PDFs automatically; for clean digital PDFs it's
  not needed and the fast path runs.
- **Chunk size is a tuning knob.** 500/50 is a sensible default. If retrieval misses
  context, increase overlap; if it returns bloated irrelevant chunks, decrease target
  size.
