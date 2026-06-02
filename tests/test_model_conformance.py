import asyncio
from unittest.mock import MagicMock

import pytest

from nornir_mcp.models import (
    ErrorResponse,
    TaskResult,
)
from nornir_mcp.tools.inventory import list_network_devices
from nornir_mcp.tools.management import (
    backup_device_configs,
    send_config_commands,
)
from nornir_mcp.tools.monitoring import run_show_commands
from nornir_mcp.tools.monitoring import get_structured_data


def test_list_network_devices_returns_dict(monkeypatch):
    """Verify list_network_devices returns a valid dict structure."""
    nr = MagicMock()
    nr.inventory.hosts = {}
    nr.inventory.groups = {}
    monkeypatch.setattr(
        "nornir_mcp.tools.inventory.get_filtered_nornir", lambda **kwargs: nr
    )

    result = asyncio.run(list_network_devices.fn())
    assert isinstance(result, dict)


def test_get_structured_data_conforms_to_task_result(monkeypatch):
    """Verify get_structured_data output conforms to TaskResult."""

    async def fake_run_napalm_get(**kwargs):
        return {"leaf-1": {"success": True, "output": {"facts": {}}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.monitoring.run_napalm_get", fake_run_napalm_get
    )

    result = asyncio.run(get_structured_data.fn(getters=["facts"]))
    TaskResult.model_validate(result)


def test_run_show_commands_conforms_to_task_result(monkeypatch):
    """Verify run_show_commands output conforms to TaskResult."""

    async def fake_execute(**kwargs):
        return {"router-01": {"success": True, "output": {"show version": "Cisco"}}}

    monkeypatch.setattr("nornir_mcp.tools.monitoring.execute", fake_execute)

    result = asyncio.run(run_show_commands.fn(commands=["show version"]))
    TaskResult.model_validate(result)


def test_send_config_commands_conforms_to_task_result(monkeypatch):
    """Verify send_config_commands output conforms to TaskResult."""

    async def fake_execute(**kwargs):
        return {"router-01": {"success": True, "output": "Config applied"}}

    monkeypatch.setattr("nornir_mcp.tools.management.execute", fake_execute)

    result = asyncio.run(send_config_commands.fn(commands=["int lo0"]))
    TaskResult.model_validate(result)


def test_backup_device_configs_returns_hosts_dict(monkeypatch):
    """Verify backup_device_configs returns a dict with hosts key."""

    async def fake_run_napalm_get(**kwargs):
        return {
            "leaf-1": {
                "success": True,
                "output": {"config": {"running": "hostname leaf-1"}},
            }
        }

    monkeypatch.setattr(
        "nornir_mcp.tools.management.run_napalm_get", fake_run_napalm_get
    )

    result = asyncio.run(backup_device_configs.fn())
    assert "hosts" in result
    assert isinstance(result["hosts"], dict)


def test_error_response_rejects_unknown_fields():
    """Verify ErrorResponse rejects unknown fields."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ErrorResponse.model_validate(
            {"error": True, "code": "x", "message": "y", "unknown_key": "z"}
        )


def test_task_result_rejects_unknown_fields():
    """Verify TaskResult rejects unknown fields."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TaskResult.model_validate({"hosts": {}, "extra": "bad"})
