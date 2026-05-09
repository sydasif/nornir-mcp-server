"""Shared inventory loading and filtering helpers."""

from nornir.core import Nornir

from ..application import get_nornir
from ..models import DeviceFilters
from ..utils.filters import apply_filters


class InventoryError(ValueError):
    """Raised when inventory operations fail."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def get_filtered_nornir(filters: DeviceFilters | None = None) -> Nornir:
    """Load Nornir from disk and apply optional inventory filters.

    This helper intentionally reloads ``config.yaml`` and inventory data on every
    call to preserve per-invocation behavior across all MCP tools.
    """
    try:
        nr = get_nornir()
    except ValueError as exc:
        raise InventoryError(str(exc), code="config_error") from exc

    try:
        return apply_filters(nr, filters)
    except ValueError as exc:
        raise InventoryError(str(exc), code="filter_error") from exc


__all__ = [
    "InventoryError",
    "get_filtered_nornir",
]
