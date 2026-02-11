"""Nornir Execution Service."""

import asyncio
import os
from collections.abc import Callable
from typing import Any

from nornir.core import Nornir
from nornir.core.exceptions import NornirExecutionError
from nornir.core.task import Result

from ..application import get_nr
from ..models import DeviceFilters
from ..utils.errors import error_response
from ..utils.filters import apply_filters
from ..utils.formatters import format_results

# Default timeout: 5 minutes for network operations
DEFAULT_TIMEOUT = int(os.environ.get("NORNIR_MCP_TIMEOUT", "300"))


class NornirRunner:
    """Orchestrates Nornir task execution."""

    async def execute(
        self,
        task: Callable[..., Result],
        filters: DeviceFilters | None = None,
        timeout: int | None = None,
        **task_kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a Nornir task and return raw results.

        1. Gets fresh Nornir instance
        2. Applies Filters
        3. Offloads blocking task to thread with timeout
        4. Returns raw results dictionary
        """
        # 1. Setup & Filter
        nr = get_nr()
        try:
            nr = apply_filters(nr, filters)
        except ValueError as e:
            return error_response(str(e), code="filter_error")

        # 2. Execute in Thread (Non-blocking) with timeout
        timeout_secs = timeout if timeout is not None else DEFAULT_TIMEOUT
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(nr.run, task=task, **task_kwargs),
                timeout=timeout_secs,
            )
        except asyncio.TimeoutError:
            return error_response(
                f"Task execution timed out after {timeout_secs} seconds",
                code="timeout_error",
            )
        except NornirExecutionError as e:
            return error_response(
                f"Nornir execution failed: {e}",
                code="execution_error",
            )

        # 3. Standardize Output (Simple extraction)
        return format_results(result)

    def get_nr(self) -> Nornir:
        """Get a fresh Nornir instance for direct use."""
        return get_nr()


# Singleton instance for easy import
runner = NornirRunner()
