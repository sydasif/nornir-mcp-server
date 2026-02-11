"""Nornir MCP Application Context - Shared application components."""

import logging
import logging.handlers
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir
from nornir.core import Nornir


class _NullSysLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        return None


def _disable_syslog_handler_if_unavailable() -> None:
    try:
        handler = logging.handlers.SysLogHandler()
        handler.close()
    except (OSError, RuntimeError):
        logging.handlers.SysLogHandler = _NullSysLogHandler  # type: ignore[assignment]


_disable_syslog_handler_if_unavailable()


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


def get_nr() -> Nornir:
    """Get a fresh Nornir instance for each request.

    Returns:
        Nornir: A fresh Nornir instance for each call.

    This function creates a new Nornir instance for each request,
    ensuring complete state isolation between tool calls.
    """
    return get_nornir()
