"""Advanced Monitoring Tools - Tools for detailed network monitoring."""

from nornir_napalm.plugins.tasks import napalm_get

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner


@mcp.tool()
async def get_bgp_config(device_name: str, group: str = "", neighbor: str = "") -> dict:
    """Retrieve BGP configuration from the device.

    Args:
        device_name: Name of the device to query
        group: Optional BGP group to filter
        neighbor: Optional BGP neighbor to filter

    Returns:
        BGP configuration information
    """
    filters = DeviceFilters(hostname=device_name)
    return await runner.execute(
        task=napalm_get, filters=filters, getters=["bgp_config"]
    )


@mcp.tool()
async def get_bgp_neighbors_detail(
    device_name: str, neighbor_address: str = ""
) -> dict:
    """Obtain a detailed view of all BGP neighbors.

    Args:
        device_name: Name of the device to query
        neighbor_address: Optional specific neighbor address to filter

    Returns:
        Detailed BGP neighbors information
    """
    filters = DeviceFilters(hostname=device_name)
    return await runner.execute(
        task=napalm_get, filters=filters, getters=["bgp_neighbors_detail"]
    )


@mcp.tool()
async def get_lldp_neighbors_detail(device_name: str, interface: str = "") -> dict:
    """Obtain a detailed view of all LLDP neighbors.

    Args:
        device_name: Name of the device to query
        interface: Optional specific interface to filter

    Returns:
        Detailed LLDP neighbors information
    """
    filters = DeviceFilters(hostname=device_name)
    return await runner.execute(
        task=napalm_get, filters=filters, getters=["lldp_neighbors_detail"]
    )


@mcp.tool()
async def get_network_instances(device_name: str, name: str = "") -> dict:
    """Retrieve a list of network instances (e.g., VRFs).

    Args:
        device_name: Name of the device to query
        name: Optional specific network instance name to filter

    Returns:
        Network instances information
    """
    filters = DeviceFilters(hostname=device_name)
    return await runner.execute(
        task=napalm_get, filters=filters, getters=["network_instances"]
    )
