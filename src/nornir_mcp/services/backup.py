"""Device configuration backup service."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..utils.files import ensure_backup_directory, write_config_to_file
from .napalm import run_napalm_get
from .runner import GLOBAL_ERROR_HOST


def _process_host(hostname: str, data: Any, backup_path: Path) -> dict[str, Any]:
    """Translate a single runner output entry into a backup record.

    Args:
        hostname: Device hostname (used as the key in the final summary).
        data: Per-host payload from the runner. May be a successful result
            dict, a failure dict, or a non-dict (defensive default).
        backup_path: Directory where config files are written.

    Returns:
        Either an error record (`{"error": True, "code": ..., "message": ...}`)
        or a success record with `path`, `size_bytes`, `written_at`, `status`.
    """
    if isinstance(data, dict) and not data.get("success", True):
        error_info = data.get("error", {})
        return {
            "error": True,
            "code": error_info.get("code", "backup_failed"),
            "message": error_info.get("message", "Backup task failed"),
        }

    output = data.get("output", {}) if isinstance(data, dict) else {}
    config_data = output.get("config", {})
    config = config_data.get("running", "") if isinstance(config_data, dict) else ""

    if not config:
        return {
            "error": True,
            "code": "no_config",
            "message": "No config data returned",
        }

    file_path = write_config_to_file(hostname, config, backup_path)
    return {
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
        "written_at": datetime.now(UTC).isoformat(),
        "status": "success",
    }


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

    return {
        "hosts": {
            hostname_: _process_host(hostname_, data, backup_path)
            for hostname_, data in result.items()
        },
    }


__all__: list[str] = ["backup_device_configs"]
