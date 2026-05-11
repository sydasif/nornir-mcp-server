from unittest.mock import MagicMock
from nornir_mcp.utils.common import format_results
from nornir_mcp.models import HostTaskResult


def create_mock_result(success: bool, result_data=None, exception=None):
    """Helper to create a mock Nornir result object."""
    mock_result = MagicMock()
    mock_result.failed = not success

    # multi_result is an iterable of results per host
    inner_result = MagicMock()
    inner_result.result = result_data
    inner_result.exception = exception

    mock_result.__iter__ = lambda self: iter([inner_result])
    mock_result.__getitem__ = lambda self, i: inner_result
    return mock_result


def test_format_results_success():
    """Successful result should wrap in HostTaskResult with success=True."""
    data = {"key": "value"}
    mock_aggregated = {"host-1": create_mock_result(True, result_data=data)}

    formatted = format_results(mock_aggregated)

    assert "host-1" in formatted
    res = formatted["host-1"]
    assert res["success"] is True
    assert res["output"] == data
    assert "error" not in res
    # Verify it validates as a HostTaskResult
    HostTaskResult.model_validate(res)


def test_format_results_empty():
    """Empty result should wrap in HostTaskResult with success=False and empty_result code."""
    mock_aggregated = {"host-1": []}  # empty multi_result

    formatted = format_results(mock_aggregated)

    assert "host-1" in formatted
    res = formatted["host-1"]
    assert res["success"] is False
    assert res["error"]["code"] == "empty_result"
    assert res["error"]["message"] == "No results returned"
    HostTaskResult.model_validate(res)


def test_format_results_failure():
    """Failed result should wrap in HostTaskResult with success=False and task_failed code."""
    exc = ValueError("Something went wrong")
    mock_aggregated = {"host-1": create_mock_result(False, exception=exc)}

    formatted = format_results(mock_aggregated)

    assert "host-1" in formatted
    res = formatted["host-1"]
    assert res["success"] is False
    assert res["error"]["code"] == "task_failed"
    assert res["error"]["message"] == "Task failed"
    assert "Something went wrong" in res["error"]["exception"]
    HostTaskResult.model_validate(res)
