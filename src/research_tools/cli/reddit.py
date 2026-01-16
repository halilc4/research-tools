"""Reddit research CLI commands."""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Any, Literal

from cyclopts import App, Parameter

from .common import output_result
from ..db import CacheRepository, get_session, init_db
from ..sources import RedditResearch, RedditPost
from ..output import render_reddit

app = App(help="Reddit research commands")

# Literal types for automatic validation
SortType = Literal["hot", "new", "rising", "top", "controversial"]
PeriodType = Literal["hour", "day", "week", "month", "year", "all"]

# Reusable parameter types
SubredditsOpt = Annotated[str, Parameter(name=["-s", "--subreddits"], help="Comma-separated subreddits")]
SortOpt = Annotated[SortType, Parameter(name="--sort", help="Sort: hot, new, rising, top, controversial")]
PeriodOpt = Annotated[PeriodType, Parameter(name=["-p", "--period"], help="Time period: hour, day, week, month, year, all")]
LimitOpt = Annotated[int, Parameter(name=["-l", "--limit"], help="Max results to show")]
JsonOpt = Annotated[bool, Parameter(name=["-j", "--json"], help="Output as JSON")]
OutputOpt = Annotated[Path | None, Parameter(name=["-o", "--output"], help="Output file path")]
NoCacheOpt = Annotated[bool, Parameter(name="--no-cache", help="Skip cache, force fresh fetch")]

# Cache TTL (12 hours for Reddit posts)
CACHE_TTL = 12


def _get_cached(cache_key: str) -> Any | None:
    """Get cached data if exists."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        return repo.get(cache_key)


def _parse_subreddits(subreddits: str) -> list[str]:
    """Parse comma-separated subreddits string."""
    return [s.strip().lower() for s in subreddits.split(",") if s.strip()]


@app.default
def reddit(
    subreddits: SubredditsOpt,
    sort: SortOpt = "hot",
    period: PeriodOpt = "week",
    limit: LimitOpt = 25,
    json_output: JsonOpt = False,
    output: OutputOpt = None,
    no_cache: NoCacheOpt = False,
) -> None:
    """
    Monitor subreddit posts for content ideas.

    Examples:
        rt reddit -s typescript
        rt reddit -s typescript,webdev --sort top --period month
        rt reddit -s programming --sort new --limit 50
    """
    sub_list = _parse_subreddits(subreddits)
    if not sub_list:
        print("Error: --subreddits is required", file=sys.stderr)
        sys.exit(1)

    # NO MANUAL VALIDATION NEEDED - Literal types handle it!

    cache_key = f"reddit:{','.join(sorted(sub_list))}:{sort}:{period}:{limit}"

    # Check cache
    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            posts = [RedditPost(**p) for p in cached["posts"]]
            output_result(
                {
                    "command": "reddit",
                    "subreddits": sub_list,
                    "sort": sort,
                    "period": period,
                    "count": len(posts),
                    "posts": cached["posts"],
                    "cached": True,
                },
                json_output,
                output,
                render_reddit,
                posts,
                sub_list,
                sort,
                period,
            )
            return

    src = RedditResearch()

    async def _run() -> None:
        posts = await src.fetch_posts(sub_list, sort=sort, period=period, limit=limit)

        posts_data = [
            {
                "id": p.id,
                "title": p.title,
                "url": p.url,
                "permalink": p.permalink,
                "author": p.author,
                "subreddit": p.subreddit,
                "score": p.score,
                "upvote_ratio": p.upvote_ratio,
                "comments": p.comments,
                "created_at": p.created_at.isoformat(),
                "flair": p.flair,
            }
            for p in posts
        ]

        # Cache result
        init_db()
        with get_session() as session:
            repo = CacheRepository(session)
            repo.set(cache_key, {"posts": posts_data}, ttl_hours=CACHE_TTL)

        output_result(
            {
                "command": "reddit",
                "subreddits": sub_list,
                "sort": sort,
                "period": period,
                "count": len(posts),
                "posts": posts_data,
            },
            json_output,
            output,
            render_reddit,
            posts,
            sub_list,
            sort,
            period,
        )

    asyncio.run(_run())
