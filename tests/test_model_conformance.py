import asyncio
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from nornir_mcp.models import (
    BackupResult,
    ErrorResponse,
    InventorySummary,
    TaskResult,
)
from nornir_mcp.tools.inventory import list_network_devices
from nornir_mcp.tools.monitoring import get_device_structured_data
from nornir_mcp.tools.management import (
    backup_device_configs,
    run_show_commands,
    send_config_commands,
)


def test_list_network_devices_conforms_to_inventory_summary(monkeypatch):
    """Verify list_network_devices output conforms to InventorySummary."""
    nr = MagicMock()
    nr.inventory.hosts = {}
    nr.inventory.groups = {}
    monkeypatch.setattr(
        "nornir_mcp.tools.inventory.get_filtered_nornir", lambda filters=None: nr
    )

    result = asyncio.run(list_network_devices.fn())
    InventorySummary.model_validate(result)


def test_get_device_structured_data_conforms_to_task_result(monkeypatch):
    """Verify get_device_structured_data output conforms to TaskResult."""

    async def fake_run_napalm_get(**kwargs):
        return {"leaf-1": {"success": True, "output": {"facts": {}}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.monitoring.run_napalm_get", fake_run_napalm_get
    )

    result = asyncio.run(get_device_structured_data.fn(getters=["facts"]))
    TaskResult.model_validate(result)


def test_run_show_commands_conforms_to_task_result(monkeypatch):
    """Verify run_show_commands output conforms to TaskResult."""

    async def fake_run_netmiko_commands(**kwargs):
        return {"router-01": {"success": True, "output": {"show version": "Cisco"}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.management.run_netmiko_commands", fake_run_netmiko_commands
    )

    result = asyncio.run(run_show_commands.fn(commands=["show version"]))
    TaskResult.model_validate(result)


def test_send_config_commands_conforms_to_task_result(monkeypatch):
    """Verify send_config_commands output conforms to TaskResult."""

    async def fake_execute(**kwargs):
        return {"router-01": {"success": True, "output": "Config applied"}}

    monkeypatch.setattr("nornir_mcp.tools.management.execute", fake_execute)

    result = asyncio.run(send_config_commands.fn(commands=["int lo0"]))
    TaskResult.model_validate(result)


def test_backup_device_configs_conforms_to_backup_result(monkeypatch):
    """Verify backup_device_configs output conforms to BackupResult."""

    async def fake_run_napalm_get(**kwargs):
        return {"leaf-1": {"config": {"running": "hostname leaf-1"}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.management.run_napalm_get", fake_run_napalm_get
    )
    monkeypatch.setattr(
        "nornir_mcp.tools.management.ensure_backup_directory", lambda path: MagicMock()
    )

    def fake_write_config(host, content, folder):
        m = MagicMock(spec=Path)
        m.stat.return_value = MagicMock(st_size=100)
        return m

    monkeypatch.setattr(
        "nornir_mcp.tools.management.write_config_to_file", fake_write_config
    )

    result = asyncio.run(backup_device_configs.fn())
    BackupResult.model_validate(result)


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
