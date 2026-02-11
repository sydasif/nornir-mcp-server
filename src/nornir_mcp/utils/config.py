"""Configuration retrieval and backup utilities."""

from datetime import datetime
from pathlib import Path


def ensure_backup_directory(backup_dir: str | Path) -> Path:
    """Create backup directory if it doesn't exist.

    Args:
        backup_dir: Path to the backup directory to create

    Returns:
        Path object pointing to the backup directory

    Raises:
        ValueError: If the backup directory path attempts to traverse outside the safe root
    """
    # Resolve the path and ensure it stays within the current working directory
    root_path = Path.cwd().resolve()
    requested = Path(backup_dir).expanduser()
    if requested.is_absolute():
        target_path = requested.resolve()
    else:
        target_path = (root_path / requested).resolve()

    if not target_path.is_relative_to(root_path):
        raise ValueError(f"Security Error: Backup directory must be within {root_path}")

    target_path.mkdir(parents=True, exist_ok=True)
    return target_path


def write_config_to_file(hostname: str, content: str, folder: Path) -> str:
    """Write configuration content to a file.

    Args:
        hostname: Device hostname for filename
        content: Configuration content to write
        folder: Directory path to write the file to

    Returns:
        Path to the written file as a string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{hostname}_{timestamp}.cfg"
    filepath = folder / filename
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)
