import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

from nornir.core.exceptions import NornirExecutionError

from nornir_mcp.models import ErrorResponse
from nornir_mcp.services.inventory import InventoryError
from nornir_mcp.services.runner import GLOBAL_ERROR_HOST, execute


class FakeNornir:
    def __init__(self, run_impl: Callable[..., Any]) -> None:
        self.run_impl = run_impl
        self.inventory = SimpleNamespace(hosts={})

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


def test_execute_returns_execution_error(monkeypatch) -> None:
    def raise_execution_error(**kwargs: Any) -> Any:
        raise NornirExecutionError({"leaf-1": FakeMultiResult([FakeSubResult()])})

    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir",
        lambda filters=None: FakeNornir(run_impl=raise_execution_error),
    )

    result = asyncio.run(execute(task=lambda **_: None))

    assert result[GLOBAL_ERROR_HOST]["error"] is True
    assert result[GLOBAL_ERROR_HOST]["code"] == "execution_error"
    assert "Nornir execution failed:" in result[GLOBAL_ERROR_HOST]["message"]
    assert "leaf-1" in result[GLOBAL_ERROR_HOST]["message"]


def test_execute_global_error_conforms_to_error_response_shape(monkeypatch) -> None:
    """Verify that global errors conform to the ErrorResponse shape."""

    def raise_inventory_error(filters=None) -> None:
        raise InventoryError("missing config", code="config_error")

    monkeypatch.setattr(
        "nornir_mcp.services.runner.get_filtered_nornir", raise_inventory_error
    )

    result = asyncio.run(execute(task=lambda **_: None))

    assert GLOBAL_ERROR_HOST in result
    ErrorResponse.model_validate(result[GLOBAL_ERROR_HOST])
