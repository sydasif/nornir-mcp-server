from pathlib import Path
import asyncio

from nornir_mcp.models import ErrorResponse, TaskResult
from nornir_mcp.services.runner import GLOBAL_ERROR_HOST
from nornir_mcp.tools.management import (
    backup_device_configs,
    send_config_commands,
)
from nornir_mcp.tools.monitoring import run_show_commands
from nornir_mcp.utils.common import error_response
from nornir_mcp.utils.security import validate_commands


def test_backup_device_configs_rejects_path_escape(
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

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))

    saved_path = Path(result["hosts"]["leaf-1"]["path"])
    assert result["hosts"]["leaf-1"]["status"] == "success"
    assert saved_path.parent == tmp_path
    assert saved_path.read_text(encoding="utf-8") == "hostname leaf-1"


def test_backup_device_configs_returns_hosts_key(monkeypatch, tmp_path: Path) -> None:
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

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))
    assert "hosts" in result
    assert "leaf-1" in result["hosts"]


def test_run_show_commands_returns_task_result_shape(monkeypatch) -> None:
    async def fake_execute(**kwargs):
        return {
            "router-01": {"success": True, "output": {"show version": "Cisco IOS..."}}
        }

    monkeypatch.setattr("nornir_mcp.tools.monitoring.execute", fake_execute)

    result = asyncio.run(run_show_commands.fn(commands=["show version"]))
    TaskResult.model_validate(result)


def test_run_show_commands_passes_through_global_error(monkeypatch) -> None:
    async def fake_execute(**kwargs):
        return {
            GLOBAL_ERROR_HOST: {
                "error": True,
                "code": "config_error",
                "message": "missing config",
            }
        }

    monkeypatch.setattr("nornir_mcp.tools.monitoring.execute", fake_execute)

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
    msg = validate_commands(["erase startup-config"])
    assert msg is not None
    result = error_response(
        "Command validation failed", details={"validation_error": msg}
    )
    ErrorResponse.model_validate(result)
