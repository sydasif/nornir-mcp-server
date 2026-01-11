"""Nornir MCP Server Backup tool.

Provides a tool for backing up device configurations to files using NAPALM for normalized multi-vendor support.
"""

from datetime import datetime
from pathlib import Path

from nornir_napalm.plugins.tasks import napalm_get

from ..server import get_nr, mcp
from ..utils.filters import apply_filters, build_filters_dict
from ..utils.formatters import format_results


def create_backup_directory(backup_dir: str) -> Path:
    """Create backup directory if it doesn't exist."""
    path = Path(backup_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@mcp.tool()
async def backup_configurations(
    backup_directory: str = "./backups",
    retrieve: str = "running",
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Backup device configurations to timestamped files. Retrieves configurations using NAPALM and saves them to files with hostname and timestamp.

    If no filters are provided, backs up configurations from all devices in the inventory.

    Args:
        backup_directory: Directory to store backup files (default: "./backups")
        retrieve: Type of configuration to retrieve ('running', 'startup', 'candidate')
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing backup results for each targeted device

    Example:
        >>> await backup_configurations()  # Backup all devices
        {'router-01': {'success': True, 'result': 'Configuration backed up to backups/router-01_20231201_120000.cfg'}, ...}
        >>> await backup_configurations(hostname="router-01", backup_directory="./router_backups")
        {'router-01': {'success': True, 'result': 'Configuration backed up to router_backups/router-01_20231201_120000.cfg'}}
        >>> await backup_configurations(group="edge_routers", retrieve="startup")
        {'router-01': {'success': True, 'result': 'Configuration backed up to backups/router-01_20231201_120000.cfg'}, ...}
    """
    nr = get_nr()
    filters = build_filters_dict(
        hostname=hostname,
        group=group,
        platform=platform,
        data_role=data_role,
        data_site=data_site,
    )
    nr = apply_filters(nr, **filters)

    # Run NAPALM getter to retrieve configuration
    result = nr.run(
        task=napalm_get,
        getters=["config"],
        getters_options={"config": {"retrieve": retrieve}},
    )

    # Format the results
    formatted = format_results(result, getter_name="config")

    # Create backup directory
    backup_path = create_backup_directory(backup_directory)

    # Process results and save configurations to files
    backup_results = {}
    for hostname, data in formatted.items():
        if data.get("success"):
            # Extract the configuration content
            config_data = data.get("result", {})
            config_content = config_data.get("config", {}).get(retrieve, "")

            if config_content:
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{hostname}_{timestamp}.cfg"
                filepath = backup_path / filename

                # Write the configuration to file
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(config_content)

                backup_results[hostname] = {
                    "success": True,
                    "result": f"Configuration backed up to {filepath}",
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
