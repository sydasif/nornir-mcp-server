"""Configuration Tools - Tools that modify device state."""

import logging

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.config import ensure_backup_directory, write_config_to_file
from ..utils.helpers import napalm_getter
from ..utils.security import CommandValidator
from ..utils.tasks import netmiko_file_transfer, netmiko_send_config

logger = logging.getLogger(__name__)


@mcp.tool()
async def send_config_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Send configuration commands to network devices.

    Args:
        commands: List of configuration commands
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw output from the configuration execution per host.
    """
    if not commands:
        raise ValueError("Command list cannot be empty")

    # Initialize command validator to prevent dangerous commands
    validator = CommandValidator()

    # Validate each command before execution
    for cmd in commands:
        validation_error = validator.validate(cmd)
        if validation_error:
            logger.warning(f"Command validation failed for '{cmd}': {validation_error}")
            return {
                "error": True,
                "validation_error": validation_error,
                "failed_command": cmd,
            }

    return await runner.execute(
        task=netmiko_send_config,
        filters=filters,
        config_commands=commands,
    )


@mcp.tool()
async def backup_device_configs(
    filters: DeviceFilters | None = None,
    path: str = "./backups",
) -> dict:
    """Save device configuration to the local disk.

    Args:
        filters: DeviceFilters object containing filter criteria
        path: Directory path to save backup files

    Returns:
        Summary of saved file paths.
    """
    # 1. Get configurations (Raw NAPALM structure: {'config': {'running': '...'}})
    result = await napalm_getter(
        getters=["config"],
        filters=filters,
        getters_options={"config": {"retrieve": "running"}},
    )

    backup_path = ensure_backup_directory(path)
    backup_results = {}

    for hostname, data in result.items():
        # Check if the host execution failed (data would be an error dict or missing keys)
        if isinstance(data, dict) and "config" in data:
            # Extract config content from raw NAPALM structure
            config_content = data["config"].get("running", "")

            if config_content:
                file_path = write_config_to_file(hostname, config_content, backup_path)
                backup_results[hostname] = {
                    "status": "success",
                    "path": file_path,
                }
            else:
                backup_results[hostname] = {
                    "status": "warning",
                    "message": "Empty configuration content",
                }
        else:
            # Propagate error info found in data
            backup_results[hostname] = {"status": "failed", "details": data}

    return backup_results


@mcp.tool()
async def file_copy(
    source_file: str,
    dest_file: str,
    filters: DeviceFilters | None = None,
    direction: str = "scp",
    file_system: str | None = None,
    disable_md5: bool = False,
) -> dict:
    """Transfer files to/from network devices securely.

    Args:
        source_file: Path to the source file
        dest_file: Path to the destination file on the device
        filters: DeviceFilters object containing filter criteria
        direction: Transfer protocol (scp, sftp, tftp)
        file_system: Optional file system path (e.g., "flash:", "bootflash:")
        disable_md5: Disable MD5 verification for transfer

    Returns:
        Dictionary with transfer results per host.
    """
    return await runner.execute(
        task=netmiko_file_transfer,
        filters=filters,
        source_file=source_file,
        dest_file=dest_file,
        direction=direction,
        file_system=file_system,
        disable_md5=disable_md5,
    )
