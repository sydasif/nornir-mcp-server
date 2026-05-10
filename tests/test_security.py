from nornir_mcp.utils.security import validate_command


def test_validate_command_rejects_dangerous_pattern() -> None:
    assert (
        validate_command("show version ; reload")
        == "Command contains disallowed pattern: ';'"
    )


def test_validate_command_rejects_blacklisted_keyword() -> None:
    assert (
        validate_command("delete vlan 10")
        == "Command starts with a blacklisted keyword: 'delete'"
    )

    assert (
        validate_command("reload") == "Command starts with a blacklisted keyword: 'reload'"
    )


def test_validate_command_allows_read_only_show_command() -> None:
    assert validate_command("show interfaces status") is None
    # 'reload' is in the middle, so it should be allowed now
    assert validate_command("show reload history") is None
    # enforcing read_only mode
    assert validate_command("config t", read_only=True) == "Only read-only commands (show/display/get/ping/traceroute) are permitted."
