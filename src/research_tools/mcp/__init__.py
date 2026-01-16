"""MCP server entry point for research-tools."""

from .server import mcp


def main() -> None:
    """Run the MCP server."""
    mcp.run()
