"""Cache CLI commands."""

from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console
from rich.prompt import Confirm

from ..db import CacheRepository, get_session, init_db

app = App(
    name="cache",
    help="Cache management",
)

console = Console()


@app.command
def stats() -> None:
    """Show cache statistics."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        cache_stats = repo.stats()

    console.print("[bold]Cache Statistics[/bold]")
    console.print(f"  Total entries: {cache_stats['total']}")
    console.print(f"  Valid: [green]{cache_stats['valid']}[/green]")
    console.print(f"  Expired: [yellow]{cache_stats['expired']}[/yellow]")


@app.command
def clear(
    force: Annotated[
        bool,
        Parameter(name=["--force", "-f"], help="Skip confirmation"),
    ] = False,
) -> None:
    """Clear all cache entries."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        cache_stats = repo.stats()

    if cache_stats["total"] == 0:
        console.print("[yellow]Cache is already empty.[/yellow]")
        return

    if not force:
        confirm = Confirm.ask(f"Clear {cache_stats['total']} cache entries?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            return

    with get_session() as session:
        repo = CacheRepository(session)
        deleted = repo.clear_all()

    console.print(f"[green]Cleared {deleted} cache entries.[/green]")


@app.command
def cleanup() -> None:
    """Remove expired cache entries."""
    init_db()
    with get_session() as session:
        repo = CacheRepository(session)
        deleted = repo.cleanup()

    if deleted == 0:
        console.print("[green]No expired entries found.[/green]")
    else:
        console.print(f"[green]Removed {deleted} expired entries.[/green]")
