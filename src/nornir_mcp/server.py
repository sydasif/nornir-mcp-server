"""Nornir MCP Server - Network Automation Server."""

from .application import mcp

# Import the new intent-based modules
from .tools import (  # noqa: F401
    inventory,
    management,
    monitoring,
    system,
)


def main() -> None:
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    main()
