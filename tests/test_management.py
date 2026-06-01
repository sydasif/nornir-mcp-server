from pathlib import Path
import asyncio

from nornir_mcp.models import ErrorResponse, TaskResult
from nornir_mcp.services.runner import GLOBAL_ERROR_HOST
from nornir_mcp.tools.management import (
    backup_device_configs,
    run_show_commands,
    send_config_commands,
)


def test_backup_device_configs_returns_security_error_for_path_escape(
    monkeypatch,
) -> None:
    async def fake_execute(**kwargs):
        return {}

    monkeypatch.setattr("nornir_mcp.services.napalm.execute", fake_execute)

    result = asyncio.run(backup_device_configs.fn(path="../outside"))

    assert result["error"] is True
    assert result["code"] == "security_error"


def test_backup_device_configs_handles_runner_errors(
    monkeypatch, tmp_path: Path
) -> None:
    async def fake_execute(**kwargs):
        return {
            "leaf-1": {
                "success": False,
                "error": {
                    "code": "task_failed",
                    "message": "device failure",
                },
            }
        }

    monkeypatch.setattr("nornir_mcp.services.napalm.execute", fake_execute)
    monkeypatch.setattr(
        "nornir_mcp.tools.management.ensure_backup_directory",
        lambda path: tmp_path,
    )

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))

    assert result["hosts"]["leaf-1"]["error"] is True
    assert result["hosts"]["leaf-1"]["code"] == "task_failed"


def test_backup_device_configs_writes_config(monkeypatch, tmp_path: Path) -> None:
    async def fake_execute(**kwargs):
        return {
            "leaf-1": {
                "success": True,
                "output": {
                    "config": {
                        "running": "hostname leaf-1",
                    }
                },
            }
        }

    monkeypatch.setattr("nornir_mcp.services.napalm.execute", fake_execute)
    monkeypatch.setattr(
        "nornir_mcp.tools.management.ensure_backup_directory",
        lambda path: tmp_path,
    )

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))

    saved_path = Path(result["hosts"]["leaf-1"]["path"])
    assert result["hosts"]["leaf-1"]["status"] == "success"
    assert saved_path.parent == tmp_path
    assert saved_path.read_text(encoding="utf-8") == "hostname leaf-1"
    from nornir_mcp.models import BackupResult

    BackupResult.model_validate(result)


def test_backup_device_configs_failure_validates_as_backup_result(
    monkeypatch, tmp_path: Path
) -> None:
    async def fake_execute(**kwargs):
        return {
            "leaf-1": {
                "success": False,
                "error": {
                    "code": "task_failed",
                    "message": "device failure",
                },
            }
        }

    monkeypatch.setattr("nornir_mcp.services.napalm.execute", fake_execute)
    monkeypatch.setattr(
        "nornir_mcp.tools.management.ensure_backup_directory",
        lambda path: tmp_path,
    )

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))
    from nornir_mcp.models import BackupResult

    BackupResult.model_validate(result)


def test_run_show_commands_returns_task_result_shape(monkeypatch) -> None:
    async def fake_run_netmiko_commands(**kwargs):
        return {
            "router-01": {"success": True, "output": {"show version": "Cisco IOS..."}}
        }

    monkeypatch.setattr(
        "nornir_mcp.tools.management.run_netmiko_commands", fake_run_netmiko_commands
    )

    result = asyncio.run(run_show_commands.fn(commands=["show version"]))
    TaskResult.model_validate(result)


def test_run_show_commands_passes_through_global_error(monkeypatch) -> None:
    async def fake_run_netmiko_commands(**kwargs):
        return {
            GLOBAL_ERROR_HOST: {
                "error": True,
                "code": "config_error",
                "message": "missing config",
            }
        }

    monkeypatch.setattr(
        "nornir_mcp.tools.management.run_netmiko_commands", fake_run_netmiko_commands
    )

    result = asyncio.run(run_show_commands.fn(commands=["show version"]))
    assert result[GLOBAL_ERROR_HOST]["error"] is True


def test_run_show_commands_returns_error_for_empty_commands() -> None:
    result = asyncio.run(run_show_commands.fn(commands=[]))
    assert result["error"] is True
    assert result["code"] == "empty_commands"


def test_send_config_commands_returns_task_result_shape(monkeypatch) -> None:
    async def fake_execute(**kwargs):
        return {"router-01": {"success": True, "output": "Config applied"}}

    monkeypatch.setattr("nornir_mcp.tools.management.execute", fake_execute)

    result = asyncio.run(send_config_commands.fn(commands=["interface loopback0"]))
    TaskResult.model_validate(result)


def test_send_config_commands_passes_through_global_error(monkeypatch) -> None:
    async def fake_execute(**kwargs):
        return {
            GLOBAL_ERROR_HOST: {
                "error": True,
                "code": "config_error",
                "message": "missing config",
            }
        }

    monkeypatch.setattr("nornir_mcp.tools.management.execute", fake_execute)

    result = asyncio.run(send_config_commands.fn(commands=["interface loopback0"]))
    assert result[GLOBAL_ERROR_HOST]["error"] is True


def test_send_config_commands_returns_error_for_empty_commands() -> None:
    result = asyncio.run(send_config_commands.fn(commands=[]))
    assert result["error"] is True
    assert result["code"] == "empty_commands"
    ErrorResponse.model_validate(result)


def test_validate_commands_error_conforms_to_error_response() -> None:
    from nornir_mcp.tools.management import _validate_commands

    result = _validate_commands([])
    assert result is not None
    ErrorResponse.model_validate(result)
