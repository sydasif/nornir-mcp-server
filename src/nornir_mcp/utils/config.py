"""Configuration retrieval and backup utilities."""

import os
from datetime import datetime
from pathlib import Path

# Cache config path at module load time to avoid CWD changes affecting security root
_CONFIG_PATH = Path("config.yaml").resolve()


def _get_security_root() -> Path:
    """Get the security root directory for backup operations.

    Uses NORNIR_MCP_ROOT environment variable if set, otherwise
    falls back to the directory containing the Nornir config.yaml.
    """
    if root_env := os.environ.get("NORNIR_MCP_ROOT"):  # pyright: ignore[reportCallIssue]
        return Path(root_env).expanduser().resolve()

    # Fall back to config.yaml directory for stability (using cached path)
    if _CONFIG_PATH.exists():
        return _CONFIG_PATH.parent

    # Final fallback to CWD (for backward compatibility)
    return Path.cwd().resolve()


def ensure_backup_directory(backup_dir: str | Path) -> Path:
    """Create backup directory if it doesn't exist.

    Args:
        backup_dir: Path to the backup directory to create

    Returns:
        Path object pointing to the backup directory

    Raises:
        ValueError: If the backup directory path attempts to traverse outside the safe root
    """
    # Resolve the path and ensure it stays within the security root
    root_path = _get_security_root()
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
