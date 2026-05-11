"""Command validation and security utilities."""

# Simple hardcoded denylist for dangerous commands
DENYLIST = {
    "keywords": {"erase", "format", "delete", "reload"},
    "patterns": [">", "<", ";", "&&", "||"],
}

# Allowed prefixes for read-only commands
ALLOWED_SHOW_PREFIXES = (
    "show ",
    "display ",
    "get ",
    "ping ",
    "traceroute ",
    "terminal ",
)


def validate_command(command: str, read_only: bool = False) -> str | None:
    """Validate a command against security rules.

    Args:
        command: Command string to validate
        read_only: If True, enforce allowlist prefix for read-only tools

    Returns:
        Error message if invalid, None if valid
    """
    command_lower = command.lower().strip()

    # 1. For read-only tools, enforce an allowlist prefix
    if read_only:
        if not any(command_lower.startswith(p) for p in ALLOWED_SHOW_PREFIXES):
            return "Only read-only commands (show/display/get/ping/traceroute) are permitted."

    # 2. Check disallowed patterns (redirection, command chaining)
    for pattern in DENYLIST["patterns"]:
        if pattern in command_lower:
            return f"Command contains disallowed pattern: '{pattern}'"

    # 3. Check keywords - match only as the first token to reduce false positives
    # e.g., 'reload' is blocked, but 'show reload history' is allowed.
    first_token = command_lower.split()[0] if command_lower.split() else ""
    if first_token in DENYLIST["keywords"]:
        return f"Command starts with a blacklisted keyword: '{first_token}'"

    return None


__all__ = ["validate_command"]
