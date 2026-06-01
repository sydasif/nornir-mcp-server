from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from nornir_mcp.models import HostTaskResult
from nornir_mcp.utils.common import format_results, wrap_task_result


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


def test_wrap_task_result_empty():
    """Empty input returns TaskResult with empty hosts dict."""
    result = wrap_task_result({})
    assert result == {"hosts": {}}


def test_wrap_task_result_success():
    """Single success entry returns correct TaskResult shape."""
    raw = {"router-01": {"success": True, "output": "ok"}}
    result = wrap_task_result(raw)
    assert "hosts" in result
    assert result["hosts"]["router-01"]["success"] is True
    assert result["hosts"]["router-01"]["output"] == "ok"
    assert "error" not in result["hosts"]["router-01"]


def test_wrap_task_result_failure():
    """Failure entry returns correct TaskResult shape."""
    raw = {
        "router-01": {
            "success": False,
            "error": {"code": "fail", "message": "failed"},
        }
    }
    result = wrap_task_result(raw)
    assert result["hosts"]["router-01"]["success"] is False
    assert result["hosts"]["router-01"]["error"]["code"] == "fail"


def test_wrap_task_result_mixed():
    """Mixed success/failure entries are all preserved."""
    raw = {
        "host-1": {"success": True, "output": "data"},
        "host-2": {"success": False, "error": {"code": "err", "message": "bad"}},
    }
    result = wrap_task_result(raw)
    assert len(result["hosts"]) == 2
    assert result["hosts"]["host-1"]["success"] is True
    assert result["hosts"]["host-2"]["success"] is False


def test_wrap_task_result_extra_fields_rejected():
    """Entry with extra fields raises ValidationError."""
    raw = {
        "host-1": {
            "success": True,
            "output": "ok",
            "extra_field": "should not be here",
        }
    }
    with pytest.raises(ValidationError):
        wrap_task_result(raw)


def test_wrap_task_result_missing_required_field():
    """Entry missing required 'success' field raises ValidationError."""
    raw = {"host-1": {"output": "ok"}}
    with pytest.raises(ValidationError):
        wrap_task_result(raw)
