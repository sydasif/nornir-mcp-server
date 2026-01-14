"""Nornir MCP Server - Network Automation Server."""

from .application import mcp

# Import the new intent-based modules
from .tools import management, inventory, monitoring  # noqa: F401


def main():
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
