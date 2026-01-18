"""Networking Tools - Tools for network connectivity and routing."""

from ..application import mcp
from ..services.runner import runner


@mcp.tool()
async def ping(
    destination: str,
    device_name: str,
    source: str = "",
    ttl: int = 255,
    timeout: int = 2,
    size: int = 100,
    count: int = 5,
    vrf: str = "",
    source_interface: str = "",
) -> dict:
    """Execute a ping from the specified device to the destination.

    Args:
        destination: Destination IP address or hostname
        device_name: Name of the device to ping from
        source: Source IP address
        ttl: TTL value for the ping packets
        timeout: Timeout for each ping attempt
        size: Size of ping packets
        count: Number of ping packets to send
        vrf: VRF to use for the ping
        source_interface: Interface to source the ping from

    Returns:
        Ping result containing success/failure information
    """
    # Import napalm ping inside the function to avoid circular imports
    from nornir_napalm.plugins.tasks import napalm_ping

    nr = runner.get_nr()
    host = nr.filter(name=device_name)

    if not host.inventory.hosts:
        return {
            "host": device_name,
            "success": False,
            "error_type": "InventoryError",
            "result": f"Device '{device_name}' not found.",
        }

    try:
        result = host.run(
            task=napalm_ping,
            dest=destination,
            source=source,
            ttl=ttl,
            timeout=timeout,
            size=size,
            count=count,
            vrf=vrf,
            name=f"Ping {destination} from {device_name}",
            raise_on_error=False,
        )

        # Extract the ping result from the Nornir result
        if device_name in result:
            ping_result = result[device_name][0].result
            return ping_result
        else:
            return {
                "success": False,
                "error": f"Device {device_name} not found in results",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

    try:
        result = host.run(
            task=napalm_ping,
            dest=destination,
            source=source,
            ttl=ttl,
            timeout=timeout,
            size=size,
            count=count,
            vrf=vrf,
            name=f"Ping {destination} from {device_name}",
            raise_on_error=False,
        )

        # Extract the ping result from the Nornir result
        if device_name in result:
            ping_result = result[device_name][0].result
            return ping_result
        else:
            return {
                "success": False,
                "error": f"Device {device_name} not found in results",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def traceroute(
    destination: str,
    device_name: str,
    source: str = "",
    ttl: int = 255,
    timeout: int = 2,
    vrf: str = "",
) -> dict:
    """Execute a traceroute from the specified device to the destination.

    Args:
        destination: Destination IP address or hostname
        device_name: Name of the device to traceroute from
        source: Source IP address
        ttl: Maximum TTL for traceroute
        timeout: Timeout for each hop
        vrf: VRF to use for the traceroute

    Returns:
        Traceroute result containing success/failure information and hop details
    """
    nr = runner.get_nr()
    host = nr.filter(name=device_name)

    if not host.inventory.hosts:
        return {
            "host": device_name,
            "success": False,
            "error_type": "InventoryError",
            "result": f"Device '{device_name}' not found.",
        }

    try:
        # Try to use napalm traceroute if available
        result = host.run(
            task=_traceroute_task,
            dest=destination,
            source=source,
            ttl=ttl,
            timeout=timeout,
            vrf=vrf,
            name=f"Traceroute {destination} from {device_name}",
            raise_on_error=False,
        )

        # Extract the traceroute result from the Nornir result
        if device_name in result:
            traceroute_result = result[device_name][0].result
            return traceroute_result
        else:
            return {
                "success": False,
                "error": f"Device {device_name} not found in results",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _traceroute_task(
    task, dest: str, source: str = "", ttl: int = 255, timeout: int = 2, vrf: str = ""
):
    """Execute a traceroute using the NAPALM connection if supported, otherwise fall back to a CLI traceroute."""
    from nornir.core.task import Result

    try:
        connection = task.host.get_connection("napalm", task.nornir.config)

        # Prefer a native traceroute method on the connection (some drivers may implement this)
        traceroute_fn = getattr(connection, "traceroute", None)
        if callable(traceroute_fn):
            # Some drivers may accept different argument names; try a best-effort call
            try:
                result = traceroute_fn(
                    dest, source=source or None, ttl=ttl, timeout=timeout, vrf=vrf
                )
            except TypeError:
                # Fallback to calling with only mandatory args
                result = traceroute_fn(dest)
            return Result(host=task.host, result=result)

        # Fallback: try issuing a CLI traceroute command via connection.cli()
        # This is a conservative invocation -- device-specific flags are not used here.
        cmd = f"traceroute {dest}"
        output = connection.cli([cmd])
        # connection.cli commonly returns a dict mapping command->output
        if isinstance(output, dict):
            return Result(host=task.host, result=output.get(cmd, output))
        return Result(host=task.host, result=output)
    except Exception:
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"Exception within _traceroute_task for {task.host.name}", exc_info=True
        )
        raise
