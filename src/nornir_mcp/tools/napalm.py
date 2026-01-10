from nornir_napalm.plugins.tasks import napalm_get

from ..server import get_nr, mcp
from ..utils.filters import filter_devices
from ..utils.formatters import format_nornir_results


def sanitize_configs(configs):
    """Remove sensitive information from configurations."""
    sanitized = {}
    for device, data in configs.items():
        if data.get("success") and data.get("result"):
            config = data["result"]
            # Remove passwords and other sensitive info
            if "running" in config:
                # Remove common sensitive patterns
                import re

                running_config = config["running"]
                # Remove password lines
                running_config = re.sub(
                    r"password \S+", "password <removed>", running_config
                )
                running_config = re.sub(
                    r"secret \S+", "secret <removed>", running_config
                )
                config["running"] = running_config
            sanitized[device] = {"success": True, "result": config}
        else:
            sanitized[device] = data
    return sanitized


@mcp.tool()
async def get_facts(devices: str) -> dict:
    """
    Retrieve basic device information including vendor, model, OS version,
    uptime, serial number, and hostname.

    This tool uses NAPALM's get_facts getter which provides normalized
    output across different vendor platforms.
    """
    # Filter devices based on request
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    # Run NAPALM getter
    result = filtered_nr.run(task=napalm_get, getters=["facts"])

    # Format results
    return format_nornir_results(result, "facts")


@mcp.tool()
async def get_interfaces(devices: str, interface: str | None = None) -> dict:
    """
    Get detailed interface information including status, IP addresses,
    MAC address, speed, MTU, and error counters.

    Args:
        devices: Device filter expression
        interface: Optional specific interface name to query
    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    result = filtered_nr.run(task=napalm_get, getters=["interfaces"])
    formatted = format_nornir_results(result, "interfaces")

    # Filter to specific interface if requested
    if interface:
        for _, data in formatted.items():
            if data.get("success") and data.get("result"):
                interfaces = data["result"]
                data["result"] = {k: v for k, v in interfaces.items() if k == interface}

    return formatted


@mcp.tool()
async def get_bgp_neighbors(devices: str) -> dict:
    """
    Get BGP neighbor status and statistics including state, uptime,
    remote AS, and prefix counts.
    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)
    result = filtered_nr.run(task=napalm_get, getters=["bgp_neighbors"])
    return format_nornir_results(result, "bgp_neighbors")


@mcp.tool()
async def get_lldp_neighbors(devices: str) -> dict:
    """
    Discover network topology via LLDP, showing connected devices
    and ports for each interface.
    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)
    result = filtered_nr.run(task=napalm_get, getters=["lldp_neighbors"])
    return format_nornir_results(result, "lldp_neighbors")


@mcp.tool()
async def get_config(
    devices: str, retrieve: str = "running", sanitized: bool = True
) -> dict:
    """
    Retrieve device configuration (running, startup, or candidate).
    Sensitive information like passwords is removed by default.
    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    result = filtered_nr.run(
        task=napalm_get,
        getters=["config"],
        getters_options={"config": {"retrieve": retrieve}},
    )

    formatted = format_nornir_results(result, "config")

    # Sanitize if requested
    if sanitized:
        formatted = sanitize_configs(formatted)

    return formatted
