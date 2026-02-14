"""Nornir Execution Service."""

import asyncio
import os
from collections.abc import Callable
from typing import Any

from nornir.core import Nornir
from nornir.core.exceptions import NornirExecutionError
from nornir.core.task import Result

from ..application import get_nornir
from ..models import DeviceFilters
from ..utils.common import error_response, format_results
from ..utils.filters import apply_filters

GLOBAL_ERROR_HOST = "__global__"


class NornirRunner:
    """Orchestrates Nornir task execution."""

    @staticmethod
    def _global_error(message: str, code: str) -> dict[str, Any]:
        """Return a host-indexed error payload for global failures."""
        return {GLOBAL_ERROR_HOST: error_response(message, code=code)}

    async def execute(
        self,
        task: Callable[..., Result],
        filters: DeviceFilters | None = None,
        timeout: int | None = None,
        **task_kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a Nornir task and return formatted results.

        Args:
            task: Nornir task function to execute
            filters: Optional filters to select specific devices
            timeout: Optional timeout in seconds (default: NORNIR_MCP_TIMEOUT env var)
            **task_kwargs: Additional arguments passed to the task

        Returns:
            Dictionary mapping hostname to task results or error responses
        """
        # 1. Setup & Filter
        try:
            nr = get_nornir()
        except ValueError as e:
            return self._global_error(str(e), code="config_error")

        try:
            nr = apply_filters(nr, filters)
        except ValueError as e:
            return self._global_error(str(e), code="filter_error")

        # 2. Execute in Thread (Non-blocking) with timeout
        timeout_secs = (
            timeout
            if timeout is not None
            else int(os.environ.get("NORNIR_MCP_TIMEOUT", "300"))
        )
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(nr.run, task=task, **task_kwargs),
                timeout=timeout_secs,
            )
        except asyncio.TimeoutError:
            return self._global_error(
                f"Task execution timed out after {timeout_secs} seconds",
                code="timeout_error",
            )
        except NornirExecutionError as e:
            return self._global_error(
                f"Nornir execution failed: {e}",
                code="execution_error",
            )

        # 3. Standardize Output (Simple extraction)
        return format_results(result)

    def get_nornir(self) -> Nornir:
        """Get a fresh Nornir instance for direct use."""
        return get_nornir()


# Singleton instance for easy import
runner = NornirRunner()
