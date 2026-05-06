"""Shared inventory loading and filtering helpers."""

from nornir.core import Nornir

from ..application import get_nornir
from ..models import DeviceFilters
from ..utils.filters import apply_filters


class InventoryConfigError(ValueError):
    """Raised when inventory configuration cannot be loaded."""


class InventoryFilterError(ValueError):
    """Raised when inventory filtering fails."""


def inventory_error_code(
    exc: InventoryConfigError | InventoryFilterError,
) -> str:
    """Map inventory exceptions to standardized error codes."""
    if isinstance(exc, InventoryConfigError):
        return "config_error"
    return "filter_error"


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
    "inventory_error_code",
    "get_filtered_nornir",
]
