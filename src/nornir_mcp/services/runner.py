"""Nornir Execution Service."""

import asyncio
import logging
import os
import time
from collections.abc import Callable
from typing import Any

from nornir.core.exceptions import NornirExecutionError
from nornir.core.task import Result

from ..utils.results import error_response, format_results
from .inventory import (
    InventoryError,
    get_filtered_nornir,
)

logger = logging.getLogger(__name__)
GLOBAL_ERROR_HOST = "__global__"
TIMEOUT = int(os.environ.get("NORNIR_MCP_TIMEOUT", "300"))


def _global_error(message: str, code: str) -> dict[str, dict[str, Any]]:
    """Return a host-indexed error payload for global failures."""
    return {GLOBAL_ERROR_HOST: error_response(message, code=code)}


async def execute(
    task: Callable[..., Result],
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    **task_kwargs: Any,
) -> dict[str, dict[str, Any]]:
    """Execute a Nornir task and return formatted results.

    Args:
        task: Nornir task function to execute
        name: Filter by device name
        hostname: Filter by hostname
        group: Filter by group
        platform: Filter by platform
        **task_kwargs: Additional arguments passed to the task

    Returns:
        Dictionary mapping hostname to task results or error responses
    """
    try:
        nr = get_filtered_nornir(
            name=name, hostname=hostname, group=group, platform=platform
        )
        host_count = len(nr.inventory.hosts)
        logger.info(
            "Executing task %s.%s on %d hosts",
            task.__module__,
            task.__name__,
            host_count,
        )
    except InventoryError as exc:
        logger.exception("Inventory setup failed: %s (code=%s)", exc, exc.code)
        return _global_error(
            str(exc),
            code=exc.code,
        )

    start_time = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(nr.run, task=task, **task_kwargs),
            timeout=TIMEOUT,
        )
        duration = time.perf_counter() - start_time
        logger.info(
            "Task %s completed in %.2fs. Failed: %s",
            task.__name__,
            duration,
            result.failed,
        )
    except asyncio.TimeoutError:
        logger.error("Task %s timed out after %ds", task.__name__, TIMEOUT)
        return _global_error(
            f"Execution timed out after {TIMEOUT}s",
            code="timeout",
        )
    except NornirExecutionError as e:
        logger.exception("Nornir execution failed: %s", e)
        return _global_error(
            f"Nornir execution failed: {e}",
            code="execution_error",
        )

    return format_results(result)


__all__: list[str] = ["GLOBAL_ERROR_HOST", "execute"]
