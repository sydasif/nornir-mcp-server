"""Configuration retrieval and backup utilities."""

from datetime import datetime
from pathlib import Path

from nornir_napalm.plugins.tasks import napalm_get

from .formatters import format_results


def ensure_backup_directory(backup_dir: str) -> Path:
    """Create backup directory if it doesn't exist."""
    path = Path(backup_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def process_config_request(
    nr,
    retrieve: str = "running",
    backup: bool = False,
    backup_directory: str = "./backups",
) -> dict:
    """Process configuration request: either retrieve to memory or backup to disk.

    Args:
        nr: The Nornir instance
        retrieve: Type of configuration ('running', 'startup', 'candidate')
        backup: If True, saves configs to file; if False, returns configs in response
        backup_directory: Directory to save backups if backup=True

    Returns:
        Dictionary containing either the config data or backup file paths
    """
    # Run NAPALM getter to retrieve configuration
    result = nr.run(
        task=napalm_get,
        getters=["config"],
        getters_options={"config": {"retrieve": retrieve}},
    )

    # Format the results
    formatted = format_results(result, getter_name="config")

    # If backup is requested, handle file writing
    if backup:
        backup_path = ensure_backup_directory(backup_directory)
        backup_results = {}

        for hostname, data in formatted.items():
            if data.get("success"):
                # Extract the configuration content
                config_data = data.get("result", {})
                config_content = config_data.get(retrieve, "")

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

    # If not backup, return the formatted config data directly
    return formatted
