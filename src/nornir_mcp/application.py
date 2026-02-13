"""Nornir MCP Application Context - Shared application components."""

import logging
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir
from nornir.core import Nornir


def _configure_logging() -> None:
    """Configure logging based on environment variables.

    Called at module import to set up logging. Respects LOG_LEVEL
    environment variable. Can be called again to reconfigure.
    """
    import os

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("nornir_mcp.log"), logging.StreamHandler()],
    )


# Initialize logging on first use
_configure_logging()

logger = logging.getLogger("nornir-mcp")

# Initialize FastMCP with metadata
mcp = FastMCP("Nornir Network Automation")


# Initialize Nornir from config
def get_nornir() -> Nornir:
    """Initialize and return a Nornir instance from configuration file.

    Returns:
        Nornir: A configured Nornir instance.

    Raises:
        ValueError: If no configuration file is found.
    """
    # Look for config file only in the current working directory
    config_file = Path.cwd() / "config.yaml"
    if not config_file.exists():
        raise ValueError(
            "No Nornir config found. Create config.yaml in current directory",
        )

    return InitNornir(config_file=str(config_file))
