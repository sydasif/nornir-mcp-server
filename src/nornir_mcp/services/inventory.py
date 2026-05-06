"""Shared inventory loading and filtering helpers."""

from nornir.core import Nornir

from ..application import get_nornir
from ..models import DeviceFilters
from ..utils.filters import apply_filters


class InventoryConfigError(ValueError):
    """Raised when inventory configuration cannot be loaded."""

    code = "config_error"


class InventoryFilterError(ValueError):
    """Raised when inventory filtering fails."""

    code = "filter_error"


def get_filtered_nornir(filters: DeviceFilters | None = None) -> Nornir:
    """Load Nornir from disk and apply optional inventory filters.

    This helper intentionally reloads ``config.yaml`` and inventory data on every
    call to preserve per-invocation behavior across all MCP tools.
    """
    try:
        nr = get_nornir()
    except ValueError as exc:
        raise InventoryConfigError(str(exc)) from exc

    try:
        return apply_filters(nr, filters)
    except ValueError as exc:
        raise InventoryFilterError(str(exc)) from exc


__all__ = [
    "InventoryConfigError",
    "InventoryFilterError",
    "get_filtered_nornir",
]
