"""Nornir MCP Server - Network Automation Server."""

from fastmcp import FastMCP

# mcp must be defined before importing tools (tools import mcp back)
mcp = FastMCP(
    "Nornir Network Automation",
    on_duplicate_tools="error",
)

# Import the new intent-based modules
from .tools import (  # noqa: E402,F401 — tools imports mcp; must come after mcp definition
    inventory,
    management,
    monitoring,
)


def main() -> None:
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    main()
