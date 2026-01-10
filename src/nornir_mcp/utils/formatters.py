"""Nornir MCP Server result formatters.

Contains functions to format Nornir results into standard response formats.
"""

from nornir.core.task import AggregatedResult


def format_nornir_results(result: AggregatedResult, getter_name: str = None) -> dict:
    """Format Nornir results into standard response format.

    Args:
        result: The aggregated result from Nornir task execution
        getter_name: Optional name of the getter to extract specific data

    Returns:
        Dictionary containing formatted results with success/error information

    """
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            formatted[host] = {
                "success": False,
                "error": {
                    "type": "CommandError",
                    "message": str(multi_result.exception),
                    "details": {
                        "platform": multi_result.host.platform,
                        "exception": type(multi_result.exception).__name__,
                    },
                },
            }
        else:
            # Extract result data
            data = multi_result[0].result
            if getter_name and isinstance(data, dict):
                data = data.get(getter_name, data)

            formatted[host] = {"success": True, "result": data}

    return formatted


def format_command_results(result: AggregatedResult) -> dict:
    """Format command execution results.

    Args:
        result: The aggregated result from command execution task

    Returns:
        Dictionary containing formatted command results with success/output information

    """
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            formatted[host] = {
                "success": False,
                "error": {
                    "type": type(multi_result.exception).__name__,
                    "message": str(multi_result.exception),
                },
            }
        else:
            formatted[host] = {"success": True, "output": multi_result[0].result}

    return formatted
