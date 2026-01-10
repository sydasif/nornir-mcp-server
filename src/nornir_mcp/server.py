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
    """Get the global Nornir instance, creating it if it doesn't exist.

    Returns:
        Nornir: The global Nornir instance.

    """
    if not hasattr(get_nr, "_instance"):
        get_nr._instance = get_nornir()
    return get_nr._instance


# Import all tool modules (they register via @mcp.tool()) after mcp is defined
# This happens after mcp is created to avoid circular imports
from .tools import inventory, napalm, netmiko  # noqa: F401


def main():
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
