# Prompt: Fix Filter Logic in Nornir MCP Server

## Context
I have a Model Context Protocol (MCP) server that acts as a wrapper around **Nornir** to automate network devices. The server provides tools to list devices, get facts, run NAPALM getters, execute show commands, and send configuration changes.

## The Problem: Global Execution Bug
There is a systemic failure in how the `filters` parameter is handled. Across almost all tools, the `filters` argument provided by the LLM is being completely ignored by the backend. Instead of executing the requested action on a subset of devices, the server executes the action on **every device in the inventory**.

### Critical Danger Case
In the `send_config_commands` tool, if a filter is provided for a device that does **not** exist, the server does not return an error or do nothing; instead, it proceeds to apply the configuration changes to **all devices in the inventory**. This is a critical risk.

## Affected Tools & Observations
The following tools are confirmed to be ignoring the `filters` parameter:

1. **`list_network_devices`**: Returns all devices regardless of the filter.
2. **`get_device_facts`**: Returns facts for all devices regardless of the filter.
3. **`run_napalm_getter`**: Executes the getter on all devices regardless of the filter.
4. **`run_show_commands`**: Executes CLI commands on all devices regardless of the filter.
5. **`send_config_commands`**: Applies configuration to all devices regardless of the filter.

## Expected Behavior
1. **Filter Respect**: When a `filters` object is passed (e.g., `{"name": "R1"}`), the tool must only operate on devices that match those criteria.
2. **Empty Result Handling**: If a filter is provided but no devices match the criteria, the tool should return an empty result or a clear message stating that no devices matched the filter.
3. **No Global Fallback**: If a filter is specified, the tool must **never** fall back to "all devices" if the filter is invalid or empty.

## Implementation Requirements
Please review the source code for the Nornir MCP server and implement the following:

1. **Integrate Nornir Filtering**: Ensure that the `filters` parameter is correctly translated into a Nornir filter. You should be using `nr.filter(...)` or passing the filter to `nr.get_devices()`.
2. **Validate Filter Application**: 
   - Verify that the filtered list of devices is actually used as the target for the subsequent Nornir tasks.
   - Ensure that the task loop only iterates over the filtered device set.
3. **Fix `send_config_commands` Logic**: Add a check to ensure that if a filter is requested, the operation only proceeds if the filtered device set is not empty.
4. **Consistent Return Types**: Maintain the current return format (dictionary mapping hostnames to results) but ensure it only contains the filtered hosts.

## Verification Criteria
The fix is successful only if:
- Calling `get_device_facts(filters={"name": "R1"})` returns data **only** for R1.
- Calling `send_config_commands(commands=["..."], filters={"name": "NON_EXISTENT"})` results in **zero** changes to any device.
- Calling a tool without a filter still correctly operates on all devices (default behavior).
