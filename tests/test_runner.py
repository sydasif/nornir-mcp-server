import asyncio
from collections.abc import Callable
from typing import Any

from nornir.core.exceptions import NornirExecutionError

from nornir_mcp.services.inventory import InventoryError
from nornir_mcp.services.runner import GLOBAL_ERROR_HOST, execute


class FakeNornir:
    def __init__(self, run_impl: Callable[..., Any]) -> None:
        self.run_impl = run_impl

    def run(self, **kwargs: Any) -> Any:
        return self.run_impl(**kwargs)


class FakeSubResult:
    name = "task"

    def __str__(self) -> str:
        return "boom"


class FakeMultiResult(list):
    failed = True


def test_execute_returns_config_error_when_config_is_missing(monkeypatch) -> None:
    def raise_config_error(filters=None) -> None:
        raise InventoryError("missing config", code="config_error")

    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir", raise_config_error
    )

    result = asyncio.run(execute(task=lambda **_: None))

    assert result == {
        GLOBAL_ERROR_HOST: {
            "error": True,
            "code": "config_error",
            "message": "missing config",
        }
    }


def test_execute_returns_filter_error(monkeypatch) -> None:
    def raise_filter_error(filters=None):
        raise InventoryError("bad filters", code="filter_error")

    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir", raise_filter_error
    )

    result = asyncio.run(execute(task=lambda **_: None))

    assert result == {
        GLOBAL_ERROR_HOST: {
            "error": True,
            "code": "filter_error",
            "message": "bad filters",
        }
    }


def test_execute_returns_timeout_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir",
        lambda filters=None: FakeNornir(run_impl=lambda **_: {}),
    )

    async def raise_timeout(awaitable: Any, timeout: int) -> Any:
        await awaitable
        raise asyncio.TimeoutError

    monkeypatch.setattr("nornir_mcp.services.runner.asyncio.wait_for", raise_timeout)

    result = asyncio.run(execute(task=lambda **_: None, timeout=5))

    assert result == {
        GLOBAL_ERROR_HOST: {
            "error": True,
            "code": "timeout_error",
            "message": "Task execution timed out after 5 seconds",
        }
    }


def test_execute_returns_timeout_config_error_for_invalid_env(monkeypatch) -> None:
    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir",
        lambda filters=None: FakeNornir(run_impl=lambda **_: {}),
    )
    monkeypatch.setenv("NORNIR_MCP_TIMEOUT", "not-a-number")

    result = asyncio.run(execute(task=lambda **_: None))

    assert result == {
        GLOBAL_ERROR_HOST: {
            "error": True,
            "code": "timeout_config_error",
            "message": "Invalid NORNIR_MCP_TIMEOUT value: 'not-a-number'",
        }
    }


def test_execute_returns_execution_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir",
        lambda filters=None: FakeNornir(run_impl=lambda **_: {}),
    )

    async def raise_execution_error(awaitable: Any, timeout: int) -> Any:
        await awaitable
        raise NornirExecutionError({"leaf-1": FakeMultiResult([FakeSubResult()])})

    monkeypatch.setattr(
        "nornir_mcp.services.runner.asyncio.wait_for", raise_execution_error
    )

    result = asyncio.run(execute(task=lambda **_: None, timeout=5))

    assert result[GLOBAL_ERROR_HOST]["error"] is True
    assert result[GLOBAL_ERROR_HOST]["code"] == "execution_error"
    assert "Nornir execution failed:" in result[GLOBAL_ERROR_HOST]["message"]
    assert "leaf-1" in result[GLOBAL_ERROR_HOST]["message"]
