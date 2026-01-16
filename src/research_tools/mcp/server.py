"""MCP server implementation for research-tools."""

from collections import defaultdict
from typing import Any, Literal

from fastmcp import FastMCP

from ..config import load_env_config
from ..db import CacheRepository, get_session, init_db
from ..sources import (
    DevToResearch,
    SerperResearch,
    RedditResearch,
    YouTubeResearch,
    Article,
    TagStats,
    AuthorStats,
)

mcp = FastMCP("research-tools")

# Cache TTLs (hours)
SERPER_CACHE_TTL = 48
REDDIT_CACHE_TTL = 12
YOUTUBE_CACHE_TTL = 24


def _get_cached(cache_key: str) -> Any | None:
    """Get cached data if exists."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        return repo.get(cache_key)


def _set_cache(cache_key: str, data: Any, ttl_hours: int = 24) -> None:
    """Cache data with TTL."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        repo.set(cache_key, data, ttl_hours=ttl_hours)


# =============================================================================
# Dev.to Tools
# =============================================================================


@mcp.tool()
async def devto_trending(
    tags: str | None = None,
    period: int = 7,
    limit: int = 20,
) -> dict:
    """
    Get trending posts from dev.to.

    Args:
        tags: Comma-separated tags to filter (e.g. "typescript,javascript")
        period: Time period in days (default 7)
        limit: Max results (default 20)

    Returns:
        Trending articles with engagement metrics
    """
    env = load_env_config()
    src = DevToResearch(api_key=env.get("devto_api_key") or "")

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    articles = await src.fetch_articles(tags=tag_list, period=period, limit=limit)

    return {
        "source": "devto",
        "period": period,
        "tags": tag_list,
        "count": len(articles),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "author": a.author,
                "reactions": a.reactions,
                "comments": a.comments,
                "reading_time": a.reading_time,
                "tags": a.tags,
                "published_at": a.published_at.isoformat(),
            }
            for a in articles
        ],
    }


@mcp.tool()
async def devto_tags(
    tags: str,
    period: int = 7,
    limit: int = 10,
) -> dict:
    """
    Analyze engagement by tag on dev.to.

    Args:
        tags: Comma-separated tags to analyze (required)
        period: Time period in days (default 7)
        limit: Max tags to return (default 10)

    Returns:
        Tag statistics with engagement metrics
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    if not tag_list:
        return {"error": "tags parameter is required"}

    env = load_env_config()
    src = DevToResearch(api_key=env.get("devto_api_key") or "")
    sample_size = max(100, limit * 10)

    articles = await src.fetch_articles(tags=tag_list, period=period, limit=sample_size)

    # Aggregate by tag
    tag_data: dict[str, list[Article]] = defaultdict(list)
    for article in articles:
        for tag in article.tags:
            if tag in tag_list:
                tag_data[tag].append(article)

    # Calculate stats
    tag_stats: list[TagStats] = []
    for tag_name in tag_list:
        tag_articles = tag_data.get(tag_name, [])
        if not tag_articles:
            continue

        count = len(tag_articles)
        total_reactions = sum(a.reactions for a in tag_articles)
        total_comments = sum(a.comments for a in tag_articles)
        total_reading = sum(a.reading_time for a in tag_articles)

        tag_stats.append(
            TagStats(
                name=tag_name,
                article_count=count,
                total_reactions=total_reactions,
                total_comments=total_comments,
                avg_reactions=total_reactions / count,
                avg_comments=total_comments / count,
                avg_reading_time=total_reading / count,
            )
        )

    tag_stats.sort(key=lambda t: t.avg_reactions, reverse=True)
    tag_stats = tag_stats[:limit]

    return {
        "source": "devto",
        "period": period,
        "sample_size": len(articles),
        "tags": [
            {
                "name": t.name,
                "article_count": t.article_count,
                "total_reactions": t.total_reactions,
                "total_comments": t.total_comments,
                "avg_reactions": round(t.avg_reactions, 1),
                "avg_comments": round(t.avg_comments, 1),
                "avg_reading_time": round(t.avg_reading_time, 1),
            }
            for t in tag_stats
        ],
    }


@mcp.tool()
async def devto_authors(
    tags: str | None = None,
    period: int = 7,
    limit: int = 10,
) -> dict:
    """
    Find top authors by engagement on dev.to.

    Args:
        tags: Comma-separated tags to filter (optional)
        period: Time period in days (default 7)
        limit: Max authors to return (default 10)

    Returns:
        Top authors with engagement metrics
    """
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    env = load_env_config()
    src = DevToResearch(api_key=env.get("devto_api_key") or "")
    sample_size = max(100, limit * 10)

    articles = await src.fetch_articles(tags=tag_list, period=period, limit=sample_size)

    # Aggregate by author
    author_data: dict[str, list[Article]] = defaultdict(list)
    for article in articles:
        author_data[article.author].append(article)

    # Calculate stats
    author_stats: list[AuthorStats] = []
    for username, user_articles in author_data.items():
        count = len(user_articles)
        total_reactions = sum(a.reactions for a in user_articles)
        total_comments = sum(a.comments for a in user_articles)

        author_stats.append(
            AuthorStats(
                username=username,
                article_count=count,
                total_reactions=total_reactions,
                total_comments=total_comments,
                avg_reactions=total_reactions / count,
                articles=user_articles,
            )
        )

    author_stats.sort(key=lambda a: a.total_reactions, reverse=True)
    author_stats = author_stats[:limit]

    return {
        "source": "devto",
        "period": period,
        "tags": tag_list,
        "sample_size": len(articles),
        "authors": [
            {
                "username": a.username,
                "article_count": a.article_count,
                "total_reactions": a.total_reactions,
                "total_comments": a.total_comments,
                "avg_reactions": round(a.avg_reactions, 1),
            }
            for a in author_stats
        ],
    }


# =============================================================================
# Google/Serper Tools
# =============================================================================


@mcp.tool()
async def google_keywords(
    query: str,
    no_cache: bool = False,
) -> dict:
    """
    Get Google autocomplete keyword suggestions.

    Args:
        query: Seed keyword
        no_cache: Skip cache, force fresh fetch

    Returns:
        List of keyword suggestions
    """
    cache_key = f"serper:keywords:{query}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {
                "query": cached["query"],
                "suggestions": cached["suggestions"],
                "cached": True,
            }

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = SerperResearch(api_key=api_key)
    data = await src.get_keywords(query)

    result = {"query": data.query, "suggestions": data.suggestions}
    _set_cache(cache_key, result, ttl_hours=SERPER_CACHE_TTL)

    return result


@mcp.tool()
async def google_serp(
    query: str,
    num: int = 10,
    gl: str = "us",
    no_cache: bool = False,
) -> dict:
    """
    Analyze Google SERP results (who ranks for a query).

    Args:
        query: Search query
        num: Number of results (default 10)
        gl: Country code (default "us")
        no_cache: Skip cache, force fresh fetch

    Returns:
        SERP analysis with organic results
    """
    cache_key = f"serper:serp:{query}:{num}:{gl}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "cached": True}

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = SerperResearch(api_key=api_key)
    data = await src.get_serp(query, num=num, gl=gl)

    result = {
        "query": data.query,
        "results": [
            {
                "position": r.position,
                "title": r.title,
                "link": r.link,
                "snippet": r.snippet,
            }
            for r in data.results
        ],
        "people_also_ask": [
            {"question": p.question, "snippet": p.snippet, "link": p.link}
            for p in data.people_also_ask
        ],
        "related_searches": data.related_searches,
    }
    _set_cache(cache_key, result, ttl_hours=SERPER_CACHE_TTL)

    return result


@mcp.tool()
async def google_paa(
    query: str,
    gl: str = "us",
    no_cache: bool = False,
) -> dict:
    """
    Get People Also Ask questions from Google.

    Args:
        query: Search query
        gl: Country code (default "us")
        no_cache: Skip cache, force fresh fetch

    Returns:
        List of PAA questions with snippets
    """
    cache_key = f"serper:paa:{query}:{gl}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "query": query, "cached": True}

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = SerperResearch(api_key=api_key)
    items = await src.get_paa(query, gl=gl)

    result = {
        "query": query,
        "questions": [
            {"question": i.question, "snippet": i.snippet, "link": i.link}
            for i in items
        ],
    }
    _set_cache(cache_key, result, ttl_hours=SERPER_CACHE_TTL)

    return result


@mcp.tool()
async def google_related(
    query: str,
    gl: str = "us",
    no_cache: bool = False,
) -> dict:
    """
    Get related searches from Google.

    Args:
        query: Search query
        gl: Country code (default "us")
        no_cache: Skip cache, force fresh fetch

    Returns:
        List of related search queries
    """
    cache_key = f"serper:related:{query}:{gl}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "query": query, "cached": True}

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = SerperResearch(api_key=api_key)
    items = await src.get_related(query, gl=gl)

    result = {"query": query, "related_searches": items}
    _set_cache(cache_key, result, ttl_hours=SERPER_CACHE_TTL)

    return result


# =============================================================================
# Reddit Tools
# =============================================================================

SortType = Literal["hot", "new", "rising", "top", "controversial"]
PeriodType = Literal["hour", "day", "week", "month", "year", "all"]


@mcp.tool()
async def reddit_posts(
    subreddits: str,
    sort: SortType = "hot",
    period: PeriodType = "week",
    limit: int = 25,
    no_cache: bool = False,
) -> dict:
    """
    Monitor subreddit posts for content ideas.

    Args:
        subreddits: Comma-separated subreddits (e.g. "typescript,webdev")
        sort: Sort order - hot, new, rising, top, controversial (default "hot")
        period: Time period for top/controversial - hour, day, week, month, year, all (default "week")
        limit: Max posts per subreddit (default 25)
        no_cache: Skip cache, force fresh fetch

    Returns:
        Reddit posts sorted by score
    """
    sub_list = [s.strip().lower() for s in subreddits.split(",") if s.strip()]
    if not sub_list:
        return {"error": "subreddits parameter is required"}

    cache_key = f"reddit:{','.join(sorted(sub_list))}:{sort}:{period}:{limit}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "cached": True}

    src = RedditResearch()
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

    result = {
        "subreddits": sub_list,
        "sort": sort,
        "period": period,
        "count": len(posts),
        "posts": posts_data,
    }
    _set_cache(cache_key, result, ttl_hours=REDDIT_CACHE_TTL)

    return result


# =============================================================================
# YouTube Tools
# =============================================================================


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


@mcp.tool()
async def youtube_search(
    query: str,
    limit: int = 20,
    region: str = "us",
    no_cache: bool = False,
) -> dict:
    """
    Search YouTube videos.

    Args:
        query: Search query
        limit: Max number of results (default 20)
        region: Country code (default "us")
        no_cache: Skip cache, force fresh fetch

    Returns:
        List of YouTube videos with metadata
    """
    cache_key = f"youtube:search:{query}:{limit}:{region}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "cached": True}

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = YouTubeResearch(api_key=api_key)
    data = await src.search(query, limit=limit, region=region)
    videos_dict = _videos_to_dict(data.videos)

    result = {"query": data.query, "count": len(videos_dict), "videos": videos_dict}
    _set_cache(cache_key, result, ttl_hours=YOUTUBE_CACHE_TTL)

    return result


@mcp.tool()
async def youtube_channel(
    channel: str,
    limit: int = 20,
    region: str = "us",
    no_cache: bool = False,
) -> dict:
    """
    Get videos from a specific YouTube channel.

    Args:
        channel: Channel name
        limit: Max number of results (default 20)
        region: Country code (default "us")
        no_cache: Skip cache, force fresh fetch

    Returns:
        List of videos from the channel
    """
    cache_key = f"youtube:channel:{channel}:{limit}:{region}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "cached": True}

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = YouTubeResearch(api_key=api_key)
    data = await src.channel_videos(channel, limit=limit, region=region)
    videos_dict = _videos_to_dict(data.videos)

    result = {"channel": channel, "count": len(videos_dict), "videos": videos_dict}
    _set_cache(cache_key, result, ttl_hours=YOUTUBE_CACHE_TTL)

    return result


@mcp.tool()
async def youtube_trending(
    category: str | None = None,
    region: str = "us",
    limit: int = 20,
    no_cache: bool = False,
) -> dict:
    """
    Get trending YouTube videos.

    Args:
        category: Optional category (music, gaming, tech, etc.)
        region: Country code (default "us")
        limit: Max number of results (default 20)
        no_cache: Skip cache, force fresh fetch

    Returns:
        List of trending videos
    """
    cache_key = f"youtube:trending:{category or 'all'}:{region}:{limit}"

    if not no_cache:
        cached = _get_cached(cache_key)
        if cached:
            return {**cached, "cached": True}

    env = load_env_config()
    api_key = env.get("serper_api_key")
    if not api_key:
        return {"error": "SERPER_API_KEY not configured"}

    src = YouTubeResearch(api_key=api_key)
    data = await src.trending(category=category, region=region, limit=limit)
    videos_dict = _videos_to_dict(data.videos)

    result = {
        "category": category,
        "region": region,
        "count": len(videos_dict),
        "videos": videos_dict,
    }
    _set_cache(cache_key, result, ttl_hours=YOUTUBE_CACHE_TTL)

    return result
