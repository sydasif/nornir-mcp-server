"""Device configuration backup service."""

from datetime import UTC, datetime
from typing import Any

from ..utils.files import ensure_backup_directory, write_config_to_file
from .napalm import run_napalm_get
from .runner import GLOBAL_ERROR_HOST


async def backup_device_configs(
    path: str,
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Run NAPALM config getter, write per-host configs, return summary.

    Args:
        path: Backup directory path
        name: Filter by device name
        hostname: Filter by hostname
        group: Filter by group
        platform: Filter by platform

    Returns:
        Dictionary with 'hosts' key mapping hostname -> file info or error
    """
    backup_path = ensure_backup_directory(path)

    result = await run_napalm_get(
        getters=["config"],
        name=name,
        hostname=hostname,
        group=group,
        platform=platform,
        getters_options={"config": {"retrieve": "running"}},
    )

    if GLOBAL_ERROR_HOST in result:
        return result

    hosts: dict[str, Any] = {}
    for hostname_, data in result.items():
        if isinstance(data, dict) and not data.get("success", True):
            error_info = data.get("error", {})
            hosts[hostname_] = {
                "error": True,
                "code": error_info.get("code", "backup_failed"),
                "message": error_info.get("message", "Backup task failed"),
            }
            continue

        output = data.get("output", {}) if isinstance(data, dict) else {}
        config_data = output.get("config", {})
        config = config_data.get("running", "") if isinstance(config_data, dict) else ""

        if not config:
            hosts[hostname_] = {
                "error": True,
                "code": "no_config",
                "message": "No config data returned",
            }
            continue

        file_path = write_config_to_file(hostname_, config, backup_path)
        hosts[hostname_] = {
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size,
            "written_at": datetime.now(UTC).isoformat(),
            "status": "success",
        }

    return {"hosts": hosts}


__all__: list[str] = ["backup_device_configs"]
