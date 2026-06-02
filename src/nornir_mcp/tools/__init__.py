"""Nornir MCP Server tools package.

This module exposes the MCP tools grouped by operational intent:
- inventory: Read-only device and group listing from the Nornir inventory.
- monitoring: Read-only observability (show commands, NAPALM getters).
- management: State-changing operations (config push, backup, restore).
"""

from . import (  # noqa: F401
    inventory,
    management,
    monitoring,
)

__all__: list[str] = ["inventory", "management", "monitoring"]
