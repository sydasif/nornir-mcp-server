"""Nornir MCP Server device filtering utilities.

Contains functions to filter Nornir inventory based on various criteria.
"""

import fnmatch

from nornir.core import Nornir
from nornir.core.filter import F


def filter_devices(nr: Nornir, filter_str: str) -> Nornir:
    """Filter Nornir inventory based on filter expression.

    Supports:
    - Exact hostname: 'router-01'
    - Multiple devices: 'router-01,router-02'
    - Group membership: 'edge_routers'
    - Data attributes: 'role=core', 'site=dc1'
    - Patterns: 'router-*'
    """
    # Comma-separated list
    if "," in filter_str:
        hosts = [h.strip() for h in filter_str.split(",")]
        return nr.filter(filter_func=lambda h: h.name in hosts)

    # Data attribute filter (key=value)
    if "=" in filter_str:
        key, value = filter_str.split("=", 1)
        return nr.filter(F(data__contains={key: value}))

    # Try exact hostname match
    if filter_str in nr.inventory.hosts:
        return nr.filter(name=filter_str)

    # Try group match
    if filter_str in nr.inventory.groups:
        return nr.filter(filter_func=lambda h: filter_str in [g.name for g in h.groups])

    # Pattern matching (glob-style)
    if "*" in filter_str:
        pattern = filter_str
        return nr.filter(filter_func=lambda h: fnmatch.fnmatch(h.name, pattern))

    raise ValueError(f"Invalid filter: {filter_str}")
