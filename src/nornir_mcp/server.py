"""Nornir MCP Server - Network Automation Server.

This module provides a FastMCP server for network automation tasks using Nornir.
"""

import logging
import os
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("nornir-mcp.log"), logging.StreamHandler()],
)

logger = logging.getLogger("nornir-mcp")

# Initialize FastMCP with metadata
mcp = FastMCP("Nornir Network Automation")


# Initialize Nornir from config
def get_nornir():
    """Initialize and return a Nornir instance from configuration file.

    Returns:
        Nornir: A configured Nornir instance.

    Raises:
        ValueError: If no configuration file is found.

    """
    config_file = os.getenv("NORNIR_CONFIG_FILE")
    if not config_file:
        # Try local config.yaml
        config_file = Path.cwd() / "config.yaml"
        if not config_file.exists():
            raise ValueError(
                "No Nornir config found. Set NORNIR_CONFIG_FILE or create config.yaml in current directory",
            )

    return InitNornir(config_file=str(config_file))


# Global Nornir instance (deferred initialization)
def get_nr():
    """Get a fresh Nornir instance.

    Returns:
        Nornir: A new Nornir instance for the current request.
    """
    # We must return a new instance every time because Nornir is stateful.
    # If a host fails a task in a singleton instance, it is marked as 'failed'
    # and skipped in subsequent runs (0 hosts selected), which breaks the server.
    return get_nornir()


# Import all tool modules (they register via @mcp.tool()) after mcp is defined
# This happens after mcp is created to avoid circular imports
from .tools import inventory, napalm, netmiko  # noqa: F401,E402


def main():
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
