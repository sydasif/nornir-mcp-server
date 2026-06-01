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
            return (
                f"Only read-only commands are permitted. "
                f"Allowed prefixes: {', '.join(p.strip() for p in ALLOWED_SHOW_PREFIXES)}"
            )

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


def validate_commands(commands: list[str], read_only: bool = False) -> str | None:
    """Validate a list of commands against security rules.

    Args:
        commands: List of commands to validate
        read_only: Whether to enforce read-only prefixes

    Returns:
        Error message if any command is invalid, None if all are valid
    """
    for cmd in commands:
        validation_error = validate_command(cmd, read_only=read_only)
        if validation_error:
            return validation_error

    return None


__all__ = ["validate_command", "validate_commands"]
