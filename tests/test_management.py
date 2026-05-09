from pathlib import Path

from nornir_mcp.tools.management import backup_device_configs


def test_backup_device_configs_returns_security_error_for_path_escape(
    monkeypatch,
) -> None:
    import asyncio

    async def fake_execute(**kwargs):
        return {}

    monkeypatch.setattr("nornir_mcp.tools.management.runner.execute", fake_execute)

    result = asyncio.run(backup_device_configs.fn(path="../outside"))

    assert result["error"] is True
    assert result["code"] == "security_error"


def test_backup_device_configs_handles_runner_errors(
    monkeypatch, tmp_path: Path
) -> None:
    import asyncio

    async def fake_execute(**kwargs):
        return {
            "leaf-1": {
                "error": True,
                "code": "task_failed",
                "message": "device failure",
            }
        }

    monkeypatch.setattr("nornir_mcp.tools.management.runner.execute", fake_execute)
    monkeypatch.setattr(
        "nornir_mcp.tools.management.ensure_backup_directory",
        lambda path: tmp_path,
    )

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))

    assert result == {
        "leaf-1": {
            "error": True,
            "code": "backup_failed",
            "message": "Backup task failed",
            "details": {
                "error": True,
                "code": "task_failed",
                "message": "device failure",
            },
        }
    }


def test_backup_device_configs_writes_config(monkeypatch, tmp_path: Path) -> None:
    import asyncio

    async def fake_execute(**kwargs):
        return {
            "leaf-1": {
                "config": {
                    "running": "hostname leaf-1",
                }
            }
        }

    monkeypatch.setattr("nornir_mcp.tools.management.runner.execute", fake_execute)
    monkeypatch.setattr(
        "nornir_mcp.tools.management.ensure_backup_directory",
        lambda path: tmp_path,
    )

    result = asyncio.run(backup_device_configs.fn(path=str(tmp_path)))

    saved_path = Path(result["leaf-1"]["path"])
    assert result["leaf-1"]["status"] == "success"
    assert saved_path.parent == tmp_path
    assert saved_path.read_text(encoding="utf-8") == "hostname leaf-1"
