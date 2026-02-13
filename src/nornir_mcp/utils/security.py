"""Command validation and security utilities."""

import re

# Simple hardcoded denylist for dangerous commands
DENYLIST = {
    "exact": {
        "reload",
        "erase startup-config",
        "write erase",
        "delete flash:",
        "format flash:",
    },
    "keywords": {"erase", "format", "delete"},
    "patterns": [">", "<", ";", "&&"],
}


def validate_command(command: str) -> str | None:
    """Validate a command against the denylist.

    Args:
        command: Command string to validate

    Returns:
        Error message if invalid, None if valid
    """
    command_lower = command.lower().strip()

    # Check disallowed patterns (redirection, command chaining)
    for pattern in DENYLIST["patterns"]:
        if pattern in command_lower:
            return f"Command contains disallowed pattern: '{pattern}'"

    # Check exact commands
    if command_lower in DENYLIST["exact"]:
        return "Command is explicitly blacklisted"

    # Check keywords
    for keyword in DENYLIST["keywords"]:
        if re.search(rf"\b{re.escape(keyword)}\b", command_lower):
            return f"Command contains blacklisted keyword: '{keyword}'"

    return None


__all__ = ["validate_command"]
