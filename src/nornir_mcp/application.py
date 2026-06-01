"""Nornir MCP Application Context - Shared application components."""

import os
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir
from nornir.core import Nornir
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Initialize FastMCP with metadata
mcp = FastMCP(
    "Nornir Network Automation",
    on_duplicate_tools="error",
)


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

    nr = InitNornir(config_file=str(config_file))

    username = os.getenv("NORNIR_USERNAME")
    password = os.getenv("NORNIR_PASSWORD")

    if username or password:
        for host in nr.inventory.hosts.values():
            if username and not host.username:
                host.username = username

            if password and not host.password:
                host.password = password

    return nr
