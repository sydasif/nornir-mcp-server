import pytest
from pydantic import ValidationError

from nornir_mcp.models import (
    ErrorResponse,
    HostTaskResult,
    TaskResult,
)


def test_error_response_round_trip():
    """A fully populated ErrorResponse round-trips correctly."""
    data = {
        "error": True,
        "code": "test_error",
        "message": "Test error message",
        "exception": "ValueError: invalid input",
        "details": {"field": "username", "reason": "too short"},
    }
    model = ErrorResponse(**data)
    dumped = model.model_dump()
    assert dumped == data

    validated = ErrorResponse.model_validate(dumped)
    assert validated == model


def test_error_response_defaults():
    """ErrorResponse with only required fields has correct defaults."""
    model = ErrorResponse(code="simple_error", message="Simple error")
    assert model.error is True
    assert model.exception is None
    assert model.details is None


def test_error_response_forbids_extra():
    """ErrorResponse.model_validate() raises ValidationError when an unknown key is present."""
    with pytest.raises(ValidationError):
        ErrorResponse.model_validate(
            {"code": "error", "message": "msg", "unknown_key": "bad"}
        )


def test_error_response_requires_code():
    """ErrorResponse.model_validate() raises ValidationError when code is missing."""
    with pytest.raises(ValidationError):
        ErrorResponse.model_validate({"message": "missing code"})


def test_host_task_result_success():
    """A successful HostTaskResult has success=True, output set, error=None."""
    model = HostTaskResult(success=True, output={"data": 123})
    assert model.success is True
    assert model.output == {"data": 123}
    assert model.error is None


def test_host_task_result_failure():
    """A failed HostTaskResult has success=False, output=None, error as a valid ErrorResponse."""
    error = ErrorResponse(code="fail", message="failed")
    model = HostTaskResult(success=False, output=None, error=error)
    assert model.success is False
    assert model.output is None
    assert model.error == error


def test_host_task_result_both_set():
    """HostTaskResult with both output and error set is valid at the model level."""
    error = ErrorResponse(code="fail", message="failed")
    model = HostTaskResult(success=False, output={"partial": "data"}, error=error)
    assert model.output == {"partial": "data"}
    assert model.error == error


def test_task_result_round_trip():
    """A TaskResult with mixed results round-trips correctly."""
    err_resp = ErrorResponse(code="err", message="msg")
    data = {
        "hosts": {
            "host-1": {"success": True, "output": "ok", "error": None},
            "host-2": {
                "success": False,
                "output": None,
                "error": err_resp.model_dump(),
            },
        }
    }
    model = TaskResult(**data)
    dumped = model.model_dump()
    assert dumped == data

    validated = TaskResult.model_validate(dumped)
    assert validated == model
