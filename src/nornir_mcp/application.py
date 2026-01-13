"""Nornir MCP Application Context - Shared application components."""

import logging
import os
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(".mcp.log"), logging.StreamHandler()],
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


def get_nr():
    """Get a fresh Nornir instance for each request.

    Returns:
        Nornir: A fresh Nornir instance for each call.

    This function creates a new Nornir instance for each request,
    ensuring complete state isolation between tool calls.
    """
    return get_nornir()