"""Nornir MCP Server device filtering utilities.

Contains functions to apply filters to Nornir inventory using the F object.
"""

from nornir.core import Nornir
from nornir.core.filter import F


def apply_filters(nr: Nornir, **filters) -> Nornir:
    """Apply filters to Nornir inventory using the F object.

    If no filters are provided, returns the unfiltered Nornir instance,
    which targets all hosts in the inventory (Nornir's default behavior).

    Args:
        nr: Nornir instance to filter
        **filters: Filter criteria as keyword arguments
            - hostname: Exact hostname match
            - group: Group membership (uses groups__contains)
            - platform: Platform match
            - Any data.* attribute using data__ prefix (e.g., data__role="core")

    Returns:
        Filtered Nornir instance (or unfiltered if no filters provided)

    Example:
        >>> apply_filters(nr)  # No filters = all hosts
        >>> apply_filters(nr, hostname="router-01")
        >>> apply_filters(nr, group="edge_routers")
        >>> apply_filters(nr, data__role="core")
        >>> apply_filters(nr, platform="cisco_ios", group="production")
    """
    # If no filters provided, return unfiltered (all hosts)
    if not filters:
        return nr

    # Special handling for common filter types
    if "hostname" in filters:
        nr = nr.filter(F(name=filters.pop("hostname")))

    if "group" in filters:
        nr = nr.filter(F(groups__contains=filters.pop("group")))

    # Apply remaining filters directly (platform, data__ attributes, etc.)
    if filters:
        nr = nr.filter(F(**filters))

    return nr
