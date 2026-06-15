"""
Research service — SearXNG web search + Jina Reader content extraction.

SearXNG runs on the same Docker network (http://searxng:8080).
Jina Reader: no setup, just prepend https://r.jina.ai/ to any URL.
Both calls fail gracefully — never raise to callers.
"""
import asyncio
from datetime import datetime, timezone

import httpx

SEARXNG_URL = "http://searxng:8080/search"
JINA_PREFIX = "https://r.jina.ai/"


async def web_search(query: str, num_results: int = 5) -> list[dict]:
    """Search via SearXNG. Returns [] if SearXNG is unreachable."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                SEARXNG_URL,
                params={"q": query, "format": "json", "categories": "general"},
            )
            r.raise_for_status()
            data = r.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                }
                for item in data.get("results", [])[:num_results]
            ]
    except Exception as e:
        print(f"[research] search failed: {e}")
        return []


async def extract_page_content(url: str, max_chars: int = 3000) -> str:
    """Fetch clean markdown from a URL via Jina Reader. Returns '' on error."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{JINA_PREFIX}{url}",
                headers={"Accept": "text/plain"},
                follow_redirects=True,
            )
            r.raise_for_status()
            return r.text[:max_chars]
    except Exception as e:
        print(f"[research] extract failed for {url}: {e}")
        return ""


async def research_goal(query: str, num_sources: int = 3) -> dict:
    """
    Full research pipeline: search → extract top sources in parallel.
    Returns structured result ready for AI synthesis.
    """
    results = await web_search(query, num_results=num_sources * 2)
    top = results[:num_sources]

    contents = await asyncio.gather(
        *[extract_page_content(r["url"]) for r in top],
        return_exceptions=True,
    )

    sources = []
    for i, result in enumerate(top):
        content = contents[i] if not isinstance(contents[i], Exception) else ""
        sources.append({
            "title": result["title"],
            "url": result["url"],
            "snippet": result["snippet"],
            "content": content,
        })

    return {
        "query": query,
        "sources": sources,
        "searched_at": datetime.now(tz=timezone.utc).isoformat(),
    }
