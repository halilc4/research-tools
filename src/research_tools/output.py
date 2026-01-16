"""Rich output rendering for research commands."""

import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .sources import Article, TagStats, AuthorStats, KeywordSuggestions, SerpAnalysis, RedditPost
from .serper.client import PeopleAlsoAsk, OrganicResult, VideoResult


# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console(force_terminal=True)


def render_trending(
    articles: list[Article],
    period: int,
    tags: list[str] | None,
) -> None:
    """Render trending posts as Rich table."""
    title = f"Trending Posts ({period}d)"
    if tags:
        title += f" - {', '.join(tags)}"

    table = Table(title=title, show_lines=False)

    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold", max_width=50, overflow="ellipsis")
    table.add_column("Author", style="cyan")
    table.add_column("Reactions", justify="right", style="green")
    table.add_column("Comments", justify="right", style="yellow")
    table.add_column("Read", justify="right")
    table.add_column("Tags", style="dim", max_width=30, overflow="ellipsis")

    for i, article in enumerate(articles, 1):
        tags_str = ", ".join(article.tags[:3])
        if len(article.tags) > 3:
            tags_str += "..."

        table.add_row(
            str(i),
            article.title,
            f"@{article.author}",
            f"{article.reactions:,}",
            f"{article.comments:,}",
            f"{article.reading_time}min",
            tags_str,
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Showing {len(articles)} articles[/dim]")


def render_tags(
    tag_stats: list[TagStats],
    sample_size: int,
    period: int,
) -> None:
    """Render tag analysis as Rich table."""
    table = Table(
        title=f"Tag Analysis ({period}d, {sample_size} articles sampled)",
        show_lines=False,
    )

    table.add_column("Tag", style="bold cyan")
    table.add_column("Articles", justify="right")
    table.add_column("Avg Reactions", justify="right", style="green")
    table.add_column("Avg Comments", justify="right", style="yellow")
    table.add_column("Avg Read Time", justify="right")

    for stats in tag_stats:
        table.add_row(
            stats.name,
            f"{stats.article_count:,}",
            f"{stats.avg_reactions:.1f}",
            f"{stats.avg_comments:.1f}",
            f"{stats.avg_reading_time:.1f}min",
        )

    console.print()
    console.print(table)
    console.print()


def render_authors(
    author_stats: list[AuthorStats],
    sample_size: int,
    period: int,
    tags: list[str] | None,
) -> None:
    """Render top authors as Rich table."""
    title = f"Top Authors ({period}d, {sample_size} articles sampled)"
    if tags:
        title = f"Top Authors - {', '.join(tags)} ({period}d)"

    table = Table(title=title, show_lines=False)

    table.add_column("#", style="dim", width=3)
    table.add_column("Author", style="bold cyan")
    table.add_column("Articles", justify="right")
    table.add_column("Total Reactions", justify="right", style="green")
    table.add_column("Avg Reactions", justify="right", style="green")
    table.add_column("Total Comments", justify="right", style="yellow")

    for i, stats in enumerate(author_stats, 1):
        table.add_row(
            str(i),
            f"@{stats.username}",
            f"{stats.article_count:,}",
            f"{stats.total_reactions:,}",
            f"{stats.avg_reactions:.1f}",
            f"{stats.total_comments:,}",
        )

    console.print()
    console.print(table)
    console.print()


def render_keywords(data: KeywordSuggestions) -> None:
    """Render keyword suggestions."""
    console.print()
    console.print(f"[bold]Keyword Suggestions for[/bold] [cyan]\"{data.query}\"[/cyan]")
    console.print("-" * 40)

    if not data.suggestions:
        console.print("[dim]No suggestions found[/dim]")
        return

    for i, suggestion in enumerate(data.suggestions, 1):
        console.print(f"  {i:2}. {suggestion}")

    console.print()


def render_serp(data: SerpAnalysis) -> None:
    """Render SERP analysis (top results)."""
    console.print()
    console.print(f"[bold]Top Results:[/bold] [cyan]\"{data.query}\"[/cyan]")
    console.print("-" * 50)

    if not data.results:
        console.print("[dim]No results found[/dim]")
        return

    for result in data.results:
        pos_style = "green" if result.position <= 3 else "yellow" if result.position <= 10 else "dim"
        console.print(f"  [bold {pos_style}]#{result.position:2}[/bold {pos_style}]  {result.title}")
        console.print(f"       [dim]{result.link}[/dim]")

    console.print()


def render_paa(query: str, items: list[PeopleAlsoAsk]) -> None:
    """Render People Also Ask questions."""
    console.print()
    console.print(f"[bold]People Also Ask:[/bold] [cyan]\"{query}\"[/cyan]")
    console.print("-" * 50)

    if not items:
        console.print("[dim]No PAA data found[/dim]")
        return

    for item in items:
        console.print(f"\n  [bold cyan]Q:[/bold cyan] {item.question}")
        if item.snippet:
            # Truncate long snippets
            snippet = item.snippet[:200] + "..." if len(item.snippet) > 200 else item.snippet
            console.print(f"     [dim]> {snippet}[/dim]")

    console.print()


def render_related(query: str, items: list[str]) -> None:
    """Render related searches."""
    console.print()
    console.print(f"[bold]Related Searches:[/bold] [cyan]\"{query}\"[/cyan]")
    console.print("-" * 40)

    if not items:
        console.print("[dim]No related searches found[/dim]")
        return

    for i, item in enumerate(items, 1):
        console.print(f"  {i:2}. {item}")

    console.print()


def render_reddit(
    posts: list[RedditPost],
    subreddits: list[str],
    sort: str,
    period: str | None = None,
) -> None:
    """Render Reddit posts as Rich table."""
    title = f"Reddit r/{', r/'.join(subreddits)} - {sort}"
    if period and sort in ("top", "controversial"):
        title += f" ({period})"

    table = Table(title=title, show_lines=False)

    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold", max_width=50, overflow="ellipsis")
    table.add_column("Subreddit", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Ratio", justify="right", style="yellow")
    table.add_column("Comments", justify="right")
    table.add_column("Author", style="dim")

    for i, post in enumerate(posts, 1):
        table.add_row(
            str(i),
            post.title,
            f"r/{post.subreddit}",
            f"{post.score:,}",
            f"{post.upvote_ratio:.0%}",
            f"{post.comments:,}",
            f"u/{post.author}",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Showing {len(posts)} posts[/dim]")


def render_youtube(
    query: str,
    videos: list[VideoResult],
) -> None:
    """Render YouTube videos as Rich table."""
    table = Table(title=f"YouTube: {query}", show_lines=False)

    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold", max_width=45, overflow="ellipsis")
    table.add_column("Channel", style="cyan", max_width=18, overflow="ellipsis")
    table.add_column("Duration", justify="right")
    table.add_column("Views", justify="right", style="green")
    table.add_column("Date", style="dim")

    for video in videos:
        pos_style = "green" if video.position <= 3 else "yellow" if video.position <= 10 else "dim"
        table.add_row(
            f"[{pos_style}]{video.position}[/{pos_style}]",
            video.title,
            video.channel or "-",
            video.duration or "-",
            video.views or "-",
            video.date or "-",
        )

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Showing {len(videos)} videos[/dim]")
