"""YouTube research CLI commands."""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Any

from cyclopts import App, Parameter

from .common import output_result
from ..db import CacheRepository, get_session, init_db
from ..sources import YouTubeResearch
from ..output import render_youtube

app = App(help="YouTube video research commands")


# Reusable parameter types
QueryOpt = Annotated[str, Parameter(name=["-q", "--query"], help="Search query")]
ChannelOpt = Annotated[str, Parameter(name=["-c", "--channel"], help="Channel name")]
CategoryOpt = Annotated[str | None, Parameter(name="--category", help="Category (music, gaming, tech, etc.)")]
RegionOpt = Annotated[str, Parameter(name=["-r", "--region"], help="Region code (us, rs, gb, etc.)")]
LimitOpt = Annotated[int, Parameter(name=["-l", "--limit"], help="Max results")]
JsonOpt = Annotated[bool, Parameter(name=["-j", "--json"], help="Output as JSON")]
OutputOpt = Annotated[Path | None, Parameter(name=["-o", "--output"], help="Output file path")]
NoCacheOpt = Annotated[bool, Parameter(name="--no-cache", help="Skip cache, force fresh fetch")]

# Cache TTL (24 hours - video content changes moderately)
CACHE_TTL = 24


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


def _get_youtube_source() -> YouTubeResearch:
    """Get YouTube research source."""
    from ..config import load_env_config
    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        print("Error: SERPER_API_KEY not configured", file=sys.stderr)
        sys.exit(1)
    return YouTubeResearch(api_key=api_key)


def _videos_to_dict(videos: list) -> list[dict]:
    """Convert VideoResult list to JSON-serializable dict list."""
    return [
        {
            "position": v.position,
            "title": v.title,
            "link": v.link,
            "snippet": v.snippet,
            "channel": v.channel,
            "duration": v.duration,
            "views": v.views,
            "date": v.date,
        }
        for v in videos
    ]


@app.command
def search(
    query: QueryOpt,
    limit: LimitOpt = 20,
    region: RegionOpt = "us",
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Search YouTube videos."""
    cache_key = f"youtube:search:{query}:{limit}:{region}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            from ..serper.client import VideoResult
            videos = [VideoResult(**v) for v in cached["videos"]]
            output_result(
                {
                    "command": "youtube:search",
                    "query": cached["query"],
                    "videos": cached["videos"],
                    "cached": True,
                },
                json_output,
                output,
                render_youtube,
                cached["query"],
                videos,
            )
            return

    src = _get_youtube_source()

    async def _run() -> None:
        data = await src.search(query, limit=limit, region=region)
        videos_dict = _videos_to_dict(data.videos)
        # Cache result
        _set_cache(cache_key, {"query": data.query, "videos": videos_dict})
        output_result(
            {
                "command": "youtube:search",
                "query": data.query,
                "videos": videos_dict,
            },
            json_output,
            output,
            render_youtube,
            data.query,
            data.videos,
        )

    asyncio.run(_run())


@app.command
def channel(
    channel_name: ChannelOpt,
    limit: LimitOpt = 20,
    region: RegionOpt = "us",
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Get videos from a specific channel."""
    cache_key = f"youtube:channel:{channel_name}:{limit}:{region}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            from ..serper.client import VideoResult
            videos = [VideoResult(**v) for v in cached["videos"]]
            output_result(
                {
                    "command": "youtube:channel",
                    "channel": cached["query"],
                    "videos": cached["videos"],
                    "cached": True,
                },
                json_output,
                output,
                render_youtube,
                cached["query"],
                videos,
            )
            return

    src = _get_youtube_source()

    async def _run() -> None:
        data = await src.channel_videos(channel_name, limit=limit, region=region)
        videos_dict = _videos_to_dict(data.videos)
        # Cache result
        _set_cache(cache_key, {"query": data.query, "videos": videos_dict})
        output_result(
            {
                "command": "youtube:channel",
                "channel": data.query,
                "videos": videos_dict,
            },
            json_output,
            output,
            render_youtube,
            data.query,
            data.videos,
        )

    asyncio.run(_run())


@app.command
def trending(
    category: CategoryOpt = None,
    region: RegionOpt = "us",
    limit: LimitOpt = 20,
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """Get trending videos."""
    cache_key = f"youtube:trending:{category or 'all'}:{region}:{limit}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            from ..serper.client import VideoResult
            videos = [VideoResult(**v) for v in cached["videos"]]
            output_result(
                {
                    "command": "youtube:trending",
                    "category": category,
                    "region": region,
                    "videos": cached["videos"],
                    "cached": True,
                },
                json_output,
                output,
                render_youtube,
                cached.get("query", "trending"),
                videos,
            )
            return

    src = _get_youtube_source()

    async def _run() -> None:
        data = await src.trending(category=category, region=region, limit=limit)
        videos_dict = _videos_to_dict(data.videos)
        # Cache result
        _set_cache(cache_key, {"query": data.query, "videos": videos_dict})
        output_result(
            {
                "command": "youtube:trending",
                "category": category,
                "region": region,
                "videos": videos_dict,
            },
            json_output,
            output,
            render_youtube,
            data.query,
            data.videos,
        )

    asyncio.run(_run())
