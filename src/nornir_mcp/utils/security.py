"""Command validation and security utilities."""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class CommandValidator:
    """Handles validation of commands against a configurable blacklist."""

    def __init__(self, blacklist_file: Path | None = None) -> None:
        if blacklist_file is None:
            # Look for blacklist file in conf directory relative to current working directory
            blacklist_file = Path.cwd() / "conf" / "blacklist.yaml"

        self.blacklist = self._load_blacklist(blacklist_file)

    def _load_blacklist(self, file_path: Path) -> dict[str, list[str]]:
        default_blacklist: dict[str, list[str]] = {
            "exact_commands": [],
            "keywords": [],
            "disallowed_patterns": [],
        }
        if not file_path.exists():
            logger.warning(
                "Blacklist file not found. Command validation will be limited."
            )
            return default_blacklist
        try:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
            if data is None:
                logger.warning(
                    f"Blacklist file '{file_path}' is empty. Using default restrictions."
                )
                return default_blacklist

            normalized_data = {
                key.lower(): _normalize_blacklist_value(value)
                for key, value in data.items()
            }

            default_blacklist.update(normalized_data)
            logger.info(f"Command blacklist loaded successfully from '{file_path}'.")
            return default_blacklist
        except (OSError, yaml.YAMLError) as exc:
            logger.error(
                f"Failed to load or parse blacklist file '{file_path}': {exc}",
                exc_info=True,
            )
            return default_blacklist

    def validate(self, command: str) -> str | None:
        """Validate a command against the blacklist.

        Returns None if command is valid, or an error message if invalid.
        """
        command_lower = command.lower().strip()

        # Check disallowed patterns first (e.g., redirection, command chaining)
        for pattern in self.blacklist.get("disallowed_patterns", []):
            if pattern.lower() in command_lower:
                return f"Command contains disallowed pattern: '{pattern}'"

        # Check exact commands
        if command_lower in self.blacklist.get("exact_commands", []):
            return "Command is explicitly blacklisted."

        # Check keywords
        for keyword in self.blacklist.get("keywords", []):
            if re.search(rf"\b{re.escape(keyword.lower())}\b", command_lower):
                return f"Command contains blacklisted keyword: '{keyword}'"

        return None


def _normalize_blacklist_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    return [str(value).lower()]
