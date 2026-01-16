"""Main CLI entry point for research-tools."""

from cyclopts import App

from .cache import app as cache_app
from .devto import app as devto_app
from .google import app as google_app
from .reddit import app as reddit_app

app = App(
    name="rt",
    help="Research tools CLI - dev.to, Google/Serper, Reddit research",
)

# Register subcommands with aliases
app.command(devto_app, name="devto", alias="d")
app.command(google_app, name="google", alias="g")
app.command(reddit_app, name="reddit", alias="rd")
app.command(cache_app, name="cache")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
