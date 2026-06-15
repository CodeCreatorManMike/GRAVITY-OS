"""
Fitness service — Wger open exercise database.
Public API, no auth required. https://wger.de/api/v2/
Results cached in-process for the session lifetime.
"""
import httpx

WGER_BASE = "https://wger.de/api/v2"

_exercise_cache: dict[str, list] = {}
_muscle_cache: list | None = None

_COMMON_WORDS = {
    "i", "want", "to", "a", "the", "and", "or", "my", "build", "get",
    "be", "in", "for", "with", "of", "at", "on", "improve", "increase",
    "have", "more", "better", "good", "great",
}


async def search_exercises(query: str, language: str = "english") -> list[dict]:
    """Search Wger exercise database. Returns [] on error."""
    if query in _exercise_cache:
        return _exercise_cache[query]
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"{WGER_BASE}/exercise/search/",
                params={"term": query, "language": language, "format": "json"},
            )
            r.raise_for_status()
            suggestions = r.json().get("suggestions", [])
            results = [
                {
                    "id": s.get("data", {}).get("id"),
                    "name": s.get("value", ""),
                    "category": s.get("data", {}).get("category", ""),
                    "description": "",
                }
                for s in suggestions
            ]
            _exercise_cache[query] = results
            return results
    except Exception as e:
        print(f"[fitness] search failed for '{query}': {e}")
        return []


async def get_muscle_groups() -> list[dict]:
    """Return all muscle groups from Wger."""
    global _muscle_cache
    if _muscle_cache is not None:
        return _muscle_cache
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{WGER_BASE}/muscle/", params={"format": "json"})
            r.raise_for_status()
            muscles = [
                {"id": m["id"], "name": m["name_en"]}
                for m in r.json().get("results", [])
            ]
            _muscle_cache = muscles
            return muscles
    except Exception as e:
        print(f"[fitness] muscle groups failed: {e}")
        return []


async def suggest_exercises_for_goal(goal_text: str) -> list[dict]:
    """Extract fitness keywords from goal text and return relevant exercises."""
    words = [
        w.lower().strip(".,!?")
        for w in goal_text.split()
        if len(w) > 3 and w.lower() not in _COMMON_WORDS
    ]
    keywords = list(dict.fromkeys(words))[:3]

    all_results: list[dict] = []
    seen_ids: set = set()

    for kw in keywords:
        results = await search_exercises(kw)
        for r in results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                all_results.append(r)
        if len(all_results) >= 10:
            break

    return all_results[:10]
