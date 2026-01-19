"""Nornir MCP Server - Network Automation Server."""

import logging

from .application import get_nr, mcp

# Import the new intent-based modules
from .tools import (  # noqa: F401
    inventory,
    management,
    monitoring,
)
from .utils.validation_helpers import make_validate_params

# Initialize logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nornir-mcp")


# Create a mock NornirManager-like object for the validation system
class MockNornirManager:
    def list_hosts(self):
        """Get list of available hosts from inventory."""
        nr = get_nr()
        hosts_info = []
        sensitive_keys = {"password", "secret"}
        for name, host_obj in nr.inventory.hosts.items():
            safe_data = {
                k: v
                for k, v in (host_obj.data or {}).items()
                if k not in sensitive_keys
            }
            hosts_info.append(
                {
                    "name": name,
                    "hostname": host_obj.hostname,
                    "platform": host_obj.platform,
                    "groups": [g.name for g in host_obj.groups],
                    "data": safe_data,
                }
            )
        return hosts_info


# Create an instance of the mock manager
mock_nr_mgr = MockNornirManager()


# Register validate_params as an MCP tool with a user-visible description
try:
    validate_params = mcp.tool(
        description="Validate input payloads against known Pydantic models; returns success, validation details, model schema, and example."
    )(make_validate_params(mock_nr_mgr))
except Exception as e:
    logger.warning(f"Failed to register 'validate_params' tool: {e}")


# Register prompts from prompts.py so users can add their own prompt_* functions
try:
    from .prompts import register_prompts

    register_prompts(mcp)
except Exception as e:
    logger.warning(f"Could not import or register prompts from prompts.py: {e}")


def main():
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
