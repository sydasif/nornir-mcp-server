"""Nornir MCP Server - Network Automation Server."""

from .application import mcp
from .tools import inventory, napalm, netmiko


def main():
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()