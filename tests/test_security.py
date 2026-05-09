from nornir_mcp.utils.security import validate_command


def test_validate_command_rejects_dangerous_pattern() -> None:
    assert (
        validate_command("show version ; reload")
        == "Command contains disallowed pattern: ';'"
    )


def test_validate_command_rejects_blacklisted_keyword() -> None:
    assert (
        validate_command("delete vlan 10")
        == "Command contains blacklisted keyword: 'delete'"
    )


def test_validate_command_allows_read_only_show_command() -> None:
    assert validate_command("show interfaces status") is None
