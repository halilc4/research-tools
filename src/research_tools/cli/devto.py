"""Dev.to research CLI commands."""

import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from .common import output_result
from ..sources import Article, TagStats, AuthorStats, DevToResearch
from ..output import render_trending, render_tags, render_authors

app = App(help="Dev.to research commands")


# Reusable parameter types
TagsOpt = Annotated[str | None, Parameter(name=["-t", "--tags"], help="Comma-separated tags")]
PeriodOpt = Annotated[int, Parameter(name="--period", help="Time period in days")]
LimitOpt = Annotated[int, Parameter(name=["-l", "--limit"], help="Max results to show")]
JsonOpt = Annotated[bool, Parameter(name=["-j", "--json"], help="Output as JSON")]
OutputOpt = Annotated[Path | None, Parameter(name=["-o", "--output"], help="Output file path")]


def _parse_tags(tags: str | None) -> list[str] | None:
    """Parse comma-separated tags string."""
    if not tags:
        return None
    return [t.strip() for t in tags.split(",") if t.strip()]


def _get_devto_source() -> DevToResearch:
    """Get dev.to research source."""
    from ..config import load_env_config
    env = load_env_config()
    return DevToResearch(api_key=env.get("devto_api_key"))


@app.command
def trending(
    tags: TagsOpt = None,
    period: PeriodOpt = 7,
    limit: LimitOpt = 20,
    json_output: JsonOpt = False,
    output: OutputOpt = None,
) -> None:
    """Get trending posts from dev.to."""
    tag_list = _parse_tags(tags)
    src = _get_devto_source()

    async def _run() -> None:
        articles = await src.fetch_articles(tags=tag_list, period=period, limit=limit)

        data = {
            "command": "trending",
            "source": src.name,
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
        output_result(data, json_output, output, render_trending, articles, period, tag_list)

    asyncio.run(_run())


@app.command
def tags(
    tags: TagsOpt = None,
    period: PeriodOpt = 7,
    limit: LimitOpt = 10,
    json_output: JsonOpt = False,
    output: OutputOpt = None,
) -> None:
    """Analyze engagement by tag."""
    tag_list = _parse_tags(tags)
    if not tag_list:
        print("Error: --tags is required for tag analysis", file=sys.stderr)
        sys.exit(1)

    src = _get_devto_source()
    sample_size = max(100, limit * 10)

    async def _run() -> None:
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

            tag_stats.append(TagStats(
                name=tag_name,
                article_count=count,
                total_reactions=total_reactions,
                total_comments=total_comments,
                avg_reactions=total_reactions / count,
                avg_comments=total_comments / count,
                avg_reading_time=total_reading / count,
            ))

        tag_stats.sort(key=lambda t: t.avg_reactions, reverse=True)
        tag_stats = tag_stats[:limit]

        data = {
            "command": "tags",
            "source": src.name,
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
        output_result(data, json_output, output, render_tags, tag_stats, len(articles), period)

    asyncio.run(_run())


@app.command
def authors(
    tags: TagsOpt = None,
    period: PeriodOpt = 7,
    limit: LimitOpt = 10,
    json_output: JsonOpt = False,
    output: OutputOpt = None,
) -> None:
    """Find top authors by engagement."""
    tag_list = _parse_tags(tags)
    src = _get_devto_source()
    sample_size = max(100, limit * 10)

    async def _run() -> None:
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

            author_stats.append(AuthorStats(
                username=username,
                article_count=count,
                total_reactions=total_reactions,
                total_comments=total_comments,
                avg_reactions=total_reactions / count,
                articles=user_articles,
            ))

        author_stats.sort(key=lambda a: a.total_reactions, reverse=True)
        author_stats = author_stats[:limit]

        data = {
            "command": "authors",
            "source": src.name,
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
        output_result(data, json_output, output, render_authors, author_stats, len(articles), period, tag_list)

    asyncio.run(_run())
