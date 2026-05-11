import pytest
from pydantic import ValidationError
from nornir_mcp.models import (
    ErrorResponse,
    HostTaskResult,
    TaskResult,
    BackupFileInfo,
    BackupResult,
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


def test_task_result_dump_hosts():
    """TaskResult.model_dump_hosts() returns a plain dict keyed by hostname."""
    err_resp = ErrorResponse(code="err", message="msg")
    model = TaskResult(
        hosts={
            "host-1": HostTaskResult(success=True, output="ok"),
            "host-2": HostTaskResult(success=False, error=err_resp),
        }
    )
    hosts_dict = model.model_dump_hosts()
    assert "host-1" in hosts_dict
    assert "host-2" in hosts_dict
    assert hosts_dict["host-1"]["success"] is True
    assert hosts_dict["host-2"]["success"] is False


def test_backup_file_info_round_trip():
    """BackupFileInfo with all fields round-trips correctly."""
    data = {
        "path": "/tmp/backup.cfg",
        "size_bytes": 1024,
        "written_at": "2026-05-11T12:00:00Z",
        "status": "success",
    }
    model = BackupFileInfo(**data)
    dumped = model.model_dump()
    assert dumped == data

    validated = BackupFileInfo.model_validate(dumped)
    assert validated == model


def test_backup_result_round_trip():
    """BackupResult with mixed success/failure round-trips correctly."""
    err_resp = ErrorResponse(code="err", message="msg")
    file_info = BackupFileInfo(
        path="/tmp/ok.cfg", size_bytes=500, written_at="2026-05-11T12:00:00Z"
    )
    data = {
        "hosts": {
            "host-ok": file_info.model_dump(),
            "host-fail": err_resp.model_dump(),
        }
    }
    model = BackupResult(**data)
    dumped = model.model_dump()
    assert dumped == data

    validated = BackupResult.model_validate(dumped)
    assert validated == model
    assert isinstance(validated.hosts["host-ok"], BackupFileInfo)
    assert isinstance(validated.hosts["host-fail"], ErrorResponse)
