"""Filesystem helpers for device configuration backups."""

from datetime import UTC, datetime
from pathlib import Path


def ensure_backup_directory(backup_dir: str | Path) -> Path:
    """Create backup directory if it doesn't exist.

    Args:
        backup_dir: Path to the backup directory to create

    Returns:
        Path object pointing to the backup directory

    Raises:
        ValueError: If the path attempts directory traversal using '..'
    """
    path_str = str(backup_dir)
    if ".." in path_str:
        raise ValueError(
            "Security Error: Directory traversal using '..' is not allowed."
        )

    path = Path(backup_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_config_to_file(hostname: str, content: str, folder: Path) -> Path:
    """Write configuration content to a file.

    Args:
        hostname: Device hostname for filename
        content: Configuration content to write
        folder: Directory path to write the file to

    Returns:
        Path to the written file
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"{hostname}_{timestamp}.cfg"
    filepath = folder / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


__all__: list[str] = [
    "ensure_backup_directory",
    "write_config_to_file",
]
