"""Configuration Tools - Tools that modify device state."""

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_config

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.config import ensure_backup_directory, write_config_to_file


@mcp.tool()
async def send_config_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Send configuration commands to network devices (modifies device state).

    This function supports both individual and bulk configuration
    changes across multiple devices simultaneously.

    SECURITY WARNING: This tool modifies device configuration and can potentially
    disrupt network services. Always verify commands before execution.

    Args:
        commands: List of configuration commands to execute on the devices
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing command execution output for each targeted device

    Raises:
        ValueError: If commands list is empty or contains invalid commands
    """
    if not commands:
        raise ValueError("Command list cannot be empty")

    if not all(isinstance(cmd, str) and cmd.strip() for cmd in commands):
        raise ValueError("All commands must be non-empty strings")

    return await runner.execute(
        task=netmiko_send_config,
        filters=filters,
        formatter_key="output",
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
        path: Directory path to save backup files (default: "./backups")

    Returns:
        Dictionary containing summary of saved file paths for each targeted device
    """
    # First get the configurations
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": "running"}},
        getter_name="config",
    )

    # Validate the backup directory
    backup_path = ensure_backup_directory(path)

    backup_results = {}
    for hostname, data in result.items():
        if data.get("success"):
            # Extract the configuration content
            config_data = data.get("result", {})
            config_content = config_data.get("running", "")

            if config_content:
                # Write the configuration to file using helper function
                file_path = write_config_to_file(hostname, config_content, backup_path)

                backup_results[hostname] = {
                    "success": True,
                    "result": f"Configuration backed up to {file_path}",
                }
            else:
                backup_results[hostname] = {
                    "success": False,
                    "result": "No configuration content found to backup",
                }
        else:
            # Pass through the original error
            backup_results[hostname] = data

    return backup_results
