"""Nornir Execution Service."""

import asyncio
from collections.abc import Callable
from typing import Any

from nornir.core.exceptions import NornirExecutionError
from nornir.core.task import Result

from ..models import DeviceFilters
from .inventory import (
    InventoryError,
    get_filtered_nornir,
)
from ..utils.common import error_response, format_results

GLOBAL_ERROR_HOST = "__global__"


def _global_error(message: str, code: str) -> dict[str, Any]:
    """Return a host-indexed error payload for global failures."""
    return {GLOBAL_ERROR_HOST: error_response(message, code=code)}


async def execute(
    task: Callable[..., Result],
    filters: DeviceFilters | None = None,
    **task_kwargs: Any,
) -> dict[str, Any]:
    """Execute a Nornir task and return formatted results.

    Args:
        task: Nornir task function to execute
        filters: Optional filters to select specific devices
        **task_kwargs: Additional arguments passed to the task

    Returns:
        Dictionary mapping hostname to task results or error responses
    """
    # 1. Setup & Filter
    try:
        nr = get_filtered_nornir(filters)
    except InventoryError as exc:
        return _global_error(
            str(exc),
            code=exc.code,
        )

    # 2. Execute in Thread (Non-blocking)
    try:
        result = await asyncio.to_thread(nr.run, task=task, **task_kwargs)
    except NornirExecutionError as e:
        return _global_error(
            f"Nornir execution failed: {e}",
            code="execution_error",
        )

    # 3. Standardize Output (Simple extraction)
    return format_results(result)


__all__ = ["execute"]
