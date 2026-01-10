"""Nornir MCP Server result formatters.

Contains functions to format Nornir results into standard response formats.
"""

from nornir.core.task import AggregatedResult


def format_results(
    result: AggregatedResult, key: str = "result", getter_name: str | None = None
) -> dict:
    """Format Nornir results into standard response format.

    Args:
        result: The aggregated result from Nornir task execution
        key: The dictionary key to use for the success data (default: "result")
        getter_name: Optional name of the getter to extract specific data (nested dict)

    Returns:
        Dictionary containing formatted results with success/error information

    """
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            formatted[host] = {
                "success": False,
                "error": {
                    "type": type(multi_result.exception).__name__,
                    "message": str(multi_result.exception),
                    "details": {
                        "platform": getattr(multi_result.host, "platform", "unknown"),
                    },
                },
            }
        else:
            # Extract result data
            data = multi_result[0].result

            # If a specific getter key is requested (e.g. for NAPALM)
            if getter_name and isinstance(data, dict):
                data = data.get(getter_name, data)

            formatted[host] = {"success": True, key: data}

    return formatted
