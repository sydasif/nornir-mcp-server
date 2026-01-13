"""Nornir MCP Server result formatters.

Contains functions to format Nornir results into standard response formats.
"""

from nornir.core.task import AggregatedResult


def format_results(result: AggregatedResult) -> dict:
    """Simple extraction of Nornir results.

    Returns a dictionary mapping hostname to the raw result data.
    If a task failed, the error information is returned instead of the result.

    Args:
        result: The aggregated result from Nornir task execution

    Returns:
        Dictionary {hostname: raw_result_data | error_dict}
    """
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            # Return error details directly
            formatted[host] = {
                "failed": True,
                "exception": str(multi_result.exception),
                "traceback": getattr(multi_result.exception, "traceback", None),
            }
        else:
            # Return the raw result data directly (stripping Nornir's MultiResult wrapper)
            # multi_result[0] is the result of the first (and usually only) task
            formatted[host] = multi_result[0].result

    return formatted
