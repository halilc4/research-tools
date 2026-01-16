# Research Tools

CLI toolkit + MCP server za dev.to, Google/Serper, Reddit i YouTube research. Globalni alias `rt`.

## Quick Start

```bash
# Help
rt --help

# Dev.to research
rt devto trending -t typescript
rt devto tags -t typescript,javascript
rt devto authors -t typescript --limit 10

# Google/Serper research
rt google keywords -q "typescript tips"
rt google paa -q "how to learn typescript"
rt google serp -q "claude code tutorial"
rt google related -q "ai development"
rt google keywords -q "test" --no-cache

# Reddit research
rt reddit -s typescript
rt reddit -s typescript,webdev --sort top --period month

# YouTube research
rt youtube search -q "typescript tutorial"
rt yt channel -c "Fireship" --limit 10
rt yt trending --category music --region us

# Cache management
rt cache stats
rt cache clear
rt cache cleanup
```

## MCP Server

```bash
# Run MCP server
rt-mcp

# Or via uvx (install from PyPI)
uvx mcp-cli-research-tools
```

### MCP Tools
- `devto_trending` - Trending posts from dev.to
- `devto_tags` - Tag engagement analysis
- `devto_authors` - Top authors by engagement
- `google_keywords` - Autocomplete suggestions
- `google_serp` - SERP analysis
- `google_paa` - People Also Ask
- `google_related` - Related searches
- `reddit_posts` - Subreddit monitoring
- `youtube_search` - Video search
- `youtube_channel` - Channel videos
- `youtube_trending` - Trending videos

## Setup

```bash
cd C:\ai-projects\research-tools && uv sync
```

## Credentials (.env)

```
DEVTO_API_KEY=xxx    # https://dev.to/settings/extensions
SERPER_API_KEY=xxx   # https://serper.dev/api-key
```

## Cache

SQLite baza (`~/.research-tools/data.db`). TTL: Serper 48h, Reddit 12h, YouTube 24h.

## Struktura

```
src/research_tools/
├── cli/           # Cyclopts CLI
├── db/            # SQLite + CacheRepository
├── mcp/           # FastMCP server
├── serper/        # Serper API client
├── sources/       # DevTo, Serper, Reddit, YouTube
└── output.py      # Rich rendering
```
