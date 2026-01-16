"""Google/Serper research CLI commands."""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Any

from cyclopts import App, Parameter

from .common import output_result
from ..db import CacheRepository, get_session, init_db
from ..sources import SerperResearch
from ..output import render_keywords, render_serp, render_paa, render_related

app = App(help="Google/Serper research commands")


# Reusable parameter types
QueryOpt = Annotated[str, Parameter(name=["-q", "--query"], help="Search query")]
GlOpt = Annotated[str, Parameter(name="--gl", help="Country code (us, uk, etc.)")]
JsonOpt = Annotated[bool, Parameter(name=["-j", "--json"], help="Output as JSON")]
OutputOpt = Annotated[Path | None, Parameter(name=["-o", "--output"], help="Output file path")]
NoCacheOpt = Annotated[bool, Parameter(name="--no-cache", help="Skip cache, force fresh fetch")]

# Cache TTL (48 hours - research data is less time-sensitive)
CACHE_TTL = 48


def _get_cached(cache_key: str) -> Any | None:
    """Get cached data if exists."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        return repo.get(cache_key)


def _set_cache(cache_key: str, data: Any) -> None:
    """Cache data with TTL."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        repo.set(cache_key, data, ttl_hours=CACHE_TTL)


def _get_serper_source() -> SerperResearch:
    """Get Serper research source."""
    from ..config import load_env_config
    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        print("Error: SERPER_API_KEY not configured", file=sys.stderr)
        sys.exit(1)
    return SerperResearch(api_key=api_key)


@app.command
def keywords(
    query: QueryOpt,
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Get autocomplete keyword suggestions."""
    cache_key = f"serper:keywords:{query}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            from ..sources import KeywordSuggestions
            data = KeywordSuggestions(**cached)
            output_result(
                {"command": "keywords", "query": data.query, "suggestions": data.suggestions, "cached": True},
                json_output,
                output,
                render_keywords,
                data,
            )
            return

    src = _get_serper_source()

    async def _run() -> None:
        data = await src.get_keywords(query)
        # Cache result
        _set_cache(cache_key, {"query": data.query, "suggestions": data.suggestions})
        output_result(
            {"command": "keywords", "query": data.query, "suggestions": data.suggestions},
            json_output,
            output,
            render_keywords,
            data,
        )

    asyncio.run(_run())


@app.command
def serp(
    query: QueryOpt,
    num: Annotated[int, Parameter(name=["-n", "--num"], help="Number of results")] = 10,
    gl: GlOpt = "us",
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Analyze SERP results (who ranks for query)."""
    cache_key = f"serper:serp:{query}:{num}:{gl}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            from ..sources import SerpAnalysis
            from ..serper.client import OrganicResult, PeopleAlsoAsk
            data = SerpAnalysis(
                query=cached["query"],
                results=[OrganicResult(**r) for r in cached["results"]],
                people_also_ask=[PeopleAlsoAsk(**p) for p in cached.get("people_also_ask", [])],
                related_searches=cached.get("related_searches", []),
            )
            output_result(
                {
                    "command": "serp",
                    "query": data.query,
                    "results": [
                        {"position": r.position, "title": r.title, "link": r.link, "snippet": r.snippet}
                        for r in data.results
                    ],
                    "cached": True,
                },
                json_output,
                output,
                render_serp,
                data,
            )
            return

    src = _get_serper_source()

    async def _run() -> None:
        data = await src.get_serp(query, num=num, gl=gl)
        # Cache result
        _set_cache(cache_key, {
            "query": data.query,
            "results": [
                {"position": r.position, "title": r.title, "link": r.link, "snippet": r.snippet}
                for r in data.results
            ],
            "people_also_ask": [
                {"question": p.question, "snippet": p.snippet, "link": p.link}
                for p in data.people_also_ask
            ],
            "related_searches": data.related_searches,
        })
        output_result(
            {
                "command": "serp",
                "query": data.query,
                "results": [
                    {"position": r.position, "title": r.title, "link": r.link, "snippet": r.snippet}
                    for r in data.results
                ],
            },
            json_output,
            output,
            render_serp,
            data,
        )

    asyncio.run(_run())


@app.command
def paa(
    query: QueryOpt,
    gl: GlOpt = "us",
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Get People Also Ask questions."""
    cache_key = f"serper:paa:{query}:{gl}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            from ..serper.client import PeopleAlsoAsk
            items = [PeopleAlsoAsk(**p) for p in cached["questions"]]
            output_result(
                {
                    "command": "paa",
                    "query": query,
                    "questions": [{"question": i.question, "snippet": i.snippet, "link": i.link} for i in items],
                    "cached": True,
                },
                json_output,
                output,
                render_paa,
                query,
                items,
            )
            return

    src = _get_serper_source()

    async def _run() -> None:
        items = await src.get_paa(query, gl=gl)
        # Cache result
        _set_cache(cache_key, {
            "questions": [{"question": i.question, "snippet": i.snippet, "link": i.link} for i in items],
        })
        output_result(
            {
                "command": "paa",
                "query": query,
                "questions": [{"question": i.question, "snippet": i.snippet, "link": i.link} for i in items],
            },
            json_output,
            output,
            render_paa,
            query,
            items,
        )

    asyncio.run(_run())


@app.command
def related(
    query: QueryOpt,
    gl: GlOpt = "us",
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Get related searches."""
    cache_key = f"serper:related:{query}:{gl}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            items = cached["related_searches"]
            output_result(
                {"command": "related", "query": query, "related_searches": items, "cached": True},
                json_output,
                output,
                render_related,
                query,
                items,
            )
            return

    src = _get_serper_source()

    async def _run() -> None:
        items = await src.get_related(query, gl=gl)
        # Cache result
        _set_cache(cache_key, {"related_searches": items})
        output_result(
            {"command": "related", "query": query, "related_searches": items},
            json_output,
            output,
            render_related,
            query,
            items,
        )

    asyncio.run(_run())
