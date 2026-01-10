import logging
import os
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir

# Import all tool modules (they register via @mcp.tool())
from .tools import config_mgmt, inventory, napalm, netmiko  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("nornir-mcp.log"), logging.StreamHandler()],
)

logger = logging.getLogger("nornir-mcp")

# Initialize FastMCP with metadata
mcp = FastMCP("Nornir Network Automation", dependencies=["nornir", "napalm", "netmiko"])


# Initialize Nornir from config
def get_nornir():
    config_file = os.getenv("NORNIR_CONFIG_FILE")
    if not config_file:
        # Try local config.yaml
        config_file = Path.cwd() / "config.yaml"
        if not config_file.exists():
            raise ValueError(
                "No Nornir config found. Set NORNIR_CONFIG_FILE or "
                "create config.yaml in current directory"
            )

    return InitNornir(config_file=str(config_file))


# Global Nornir instance
nr = get_nornir()


def main():
    """Entry point for FastMCP"""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
