"""NAPALM getter validation utilities."""

from typing import Any

# NAPALM getter support matrix based on NAPALM documentation
# Keys are platform names, values are lists of supported getter names
NAPALM_GETTER_SUPPORT: dict[str, list[str]] = {
    "eos": [
        "arp_table",
        "bgp_config",
        "bgp_neighbors",
        "bgp_neighbors_detail",
        "climate",
        "config",
        "environment",
        "facts",
        "firewall_policies",
        "interfaces",
        "interfaces_ip",
        "lldp_neighbors",
        "lldp_neighbors_detail",
        "mac_address_table",
        "network_instances",
        "ntp_peers",
        "ntp_servers",
        "ntp_stats",
        "probes",
        "probes_config",
        "route_to",
        "snmp",
        "users",
        "vlans",
    ],
    "ios": [
        "arp_table",
        "bgp_config",
        "bgp_neighbors",
        "bgp_neighbors_detail",
        "config",
        "environment",
        "facts",
        "interfaces",
        "interfaces_ip",
        "lldp_neighbors",
        "lldp_neighbors_detail",
        "mac_address_table",
        "ntp_peers",
        "ntp_servers",
        "ntp_stats",
        "route_to",
        "snmp",
        "users",
    ],
    "iosxr": [
        "arp_table",
        "bgp_config",
        "bgp_neighbors",
        "bgp_neighbors_detail",
        "config",
        "environment",
        "facts",
        "interfaces",
        "interfaces_ip",
        "lldp_neighbors",
        "lldp_neighbors_detail",
        "mac_address_table",
        "ntp_peers",
        "ntp_servers",
        "ntp_stats",
        "route_to",
        "users",
    ],
    "iosxr_netconf": [
        "bgp_config",
        "bgp_neighbors",
        "config",
        "facts",
        "interfaces",
        "interfaces_ip",
    ],
    "junos": [
        "arp_table",
        "bgp_config",
        "bgp_neighbors",
        "bgp_neighbors_detail",
        "climate",
        "config",
        "environment",
        "facts",
        "firewall_policies",
        "interfaces",
        "interfaces_ip",
        "lldp_neighbors",
        "lldp_neighbors_detail",
        "mac_address_table",
        "network_instances",
        "ntp_peers",
        "ntp_servers",
        "ntp_stats",
        "probes",
        "probes_config",
        "route_to",
        "users",
        "vlans",
    ],
    "nxos": [
        "arp_table",
        "bgp_config",
        "bgp_neighbors",
        "bgp_neighbors_detail",
        "config",
        "environment",
        "facts",
        "interfaces",
        "interfaces_ip",
        "lldp_neighbors",
        "lldp_neighbors_detail",
        "mac_address_table",
        "ntp_peers",
        "ntp_servers",
        "ntp_stats",
        "route_to",
        "snmp",
        "users",
        "vlans",
    ],
    "nxos_ssh": [
        "arp_table",
        "bgp_config",
        "bgp_neighbors",
        "bgp_neighbors_detail",
        "config",
        "facts",
        "interfaces",
        "interfaces_ip",
        "lldp_neighbors",
        "lldp_neighbors_detail",
        "mac_address_table",
        "ntp_servers",
        "users",
        "vlans",
    ],
}


def get_supported_getters(platform: str) -> list[str]:
    """Get list of supported getters for a platform.

    Args:
        platform: Platform name (e.g., 'eos', 'ios', 'junos')

    Returns:
        List of supported getter names
    """
    return NAPALM_GETTER_SUPPORT.get(platform, [])


def validate_getters(platform: str, getters: list[str]) -> tuple[list[str], list[str]]:
    """Validate getters for a specific platform.

    Args:
        platform: Platform name
        getters: List of getter names to validate

    Returns:
        Tuple of (valid_getters, invalid_getters)
    """
    if platform not in NAPALM_GETTER_SUPPORT:
        # Unknown platform: skip validation to avoid blocking valid drivers.
        return list(getters), []

    supported = set(get_supported_getters(platform))
    valid = []
    invalid = []

    for getter in getters:
        if getter in supported:
            valid.append(getter)
        else:
            invalid.append(getter)

    return valid, invalid


def is_getter_supported(platform: str, getter: str) -> bool:
    """Check if a specific getter is supported on a platform.

    Args:
        platform: Platform name
        getter: Getter name

    Returns:
        True if supported, False otherwise
    """
    supported = get_supported_getters(platform)
    return getter in supported


def get_validation_error_message(
    platform: str,
    invalid_getters: list[str],
    valid_getters: list[str] | None = None
) -> str:
    """Generate a helpful error message for unsupported getters.

    Args:
        platform: Platform name
        invalid_getters: List of unsupported getter names
        valid_getters: Optional list of valid getters that were requested

    Returns:
        Error message string
    """
    supported = get_supported_getters(platform)

    msg = f"The following getters are not supported on platform '{platform}': {', '.join(invalid_getters)}"

    if supported:
        msg += f".\nSupported getters for {platform}: {', '.join(supported[:10])}"
        if len(supported) > 10:
            msg += f" and {len(supported) - 10} more"

    return msg


__all__: list[str] = [
    "NAPALM_GETTER_SUPPORT",
    "get_supported_getters",
    "validate_getters",
    "is_getter_supported",
    "get_validation_error_message",
]
