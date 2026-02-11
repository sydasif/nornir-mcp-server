"""Nornir MCP Server - Network Automation Server."""

from .application import get_nr, mcp

# Import the new intent-based modules
from .tools import (  # noqa: F401
    inventory,
    management,
    monitoring,
)
from .utils.validation_helpers import register_validate_params

register_validate_params(mcp, get_nr)


def main() -> None:
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    main()
