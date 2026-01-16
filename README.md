# research-tools

CLI toolkit + MCP server za dev.to, Google/Serper, Reddit i YouTube research.

## Installation

### Claude Desktop

#### Windows

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "research-tools": {
      "command": "uvx",
      "args": ["--from", "mcp-cli-research-tools[mcp]", "rt-mcp"],
      "env": {
        "SERPER_API_KEY": "your-serper-key",
        "DEVTO_API_KEY": "your-devto-key"
      }
    }
  }
}
```

#### macOS

Claude Desktop on macOS doesn't include `~/.local/bin` in PATH. You must specify the full path to `uvx`.

1. Find your uvx path:
```bash
which uvx
# Usually: ~/.local/bin/uvx or /opt/homebrew/bin/uvx
```

2. Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "research-tools": {
      "command": "/Users/YOUR_USERNAME/.local/bin/uvx",
      "args": ["--from", "mcp-cli-research-tools[mcp]", "rt-mcp"],
      "env": {
        "SERPER_API_KEY": "your-serper-key",
        "DEVTO_API_KEY": "your-devto-key"
      }
    }
  }
}
```

Replace `/Users/YOUR_USERNAME/.local/bin/uvx` with the output from `which uvx`.

### Claude Code (.mcp.json)

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "research-tools": {
      "command": "uvx",
      "args": ["--from", "mcp-cli-research-tools[mcp]", "rt-mcp"]
    }
  }
}
```

### CLI (global)

```bash
uv tool install mcp-cli-research-tools
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `devto_trending` | Trending posts from dev.to |
| `devto_tags` | Tag engagement analysis |
| `devto_authors` | Top authors by engagement |
| `google_keywords` | Autocomplete suggestions |
| `google_serp` | SERP analysis |
| `google_paa` | People Also Ask |
| `google_related` | Related searches |
| `reddit_posts` | Subreddit monitoring |
| `youtube_search` | Video search |
| `youtube_channel` | Channel videos |
| `youtube_trending` | Trending videos |

## CLI Usage

```bash
# Dev.to
rt devto trending -t typescript
rt devto tags -t typescript,javascript
rt devto authors -t typescript --limit 10

# Google/Serper
rt google keywords -q "typescript tips"
rt google paa -q "how to learn typescript"
rt google serp -q "claude code tutorial"
rt google related -q "ai development"

# Reddit
rt reddit -s typescript,webdev --sort top --period month

# YouTube
rt youtube search -q "typescript tutorial"
rt yt channel -c "Fireship" --limit 10
rt yt trending --category music --region us

# Cache
rt cache stats
rt cache clear
```

## API Keys

| Service | Key | Get it at |
|---------|-----|-----------|
| Serper | `SERPER_API_KEY` | https://serper.dev/api-key |
| Dev.to | `DEVTO_API_KEY` | https://dev.to/settings/extensions |

Set via environment variables or `.env` file.

## Cache

SQLite database at `~/.research-tools/data.db`. TTL: Serper 48h, Reddit 12h, YouTube 24h.

## Troubleshooting

### macOS: "Failed to spawn process: No such file or directory"

Claude Desktop on macOS uses a limited PATH that doesn't include user-installed tools. The solution is to use the full path to `uvx` in your config:

```bash
# Find uvx location
which uvx

# Common locations:
# ~/.local/bin/uvx (uv installer)
# /opt/homebrew/bin/uvx (Homebrew on Apple Silicon)
# /usr/local/bin/uvx (Homebrew on Intel)
```

Then update `command` in `claude_desktop_config.json` to use the full path.
