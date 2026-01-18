# Nornir MCP Server

An MCP (Model Context Protocol) server built with **FastMCP** that exposes Nornir automation capabilities to Claude, enabling natural language interaction with network infrastructure. This server combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

## Features

- **Network Inventory Tools**: List devices, query groups, filter by attributes
- **Monitoring Tools**: Read-only commands for network state retrieval (facts, interfaces with IP addresses, BGP, LLDP, configs, ARP/MAC tables)
- **Management Tools**: State-modifying commands for network device management
- **Service-Intent Architecture**: Clean separation between monitoring (read) and management (write) operations
- **Device Filtering**: Supports hostname, group, attribute, and pattern-based filtering
- **Structured Output**: Standardized result formatting with error handling
- **Security Focused**: Sensitive information sanitization and intent-based access controls

## Prerequisites

- Python 3.11+
- uv package manager (recommended)
- Network access to target devices via SSH
- Valid Nornir configuration with device inventory

## Installation

### Using uv (Recommended)

```bash
# Install the server as a tool
uv tool install git+https://github.com/sydasif/nornir-stack.git

# Or install from local source
uv sync
```

### Using pip

```bash
pip install git+https://github.com/sydasif/nornir-stack.git
```

## Configuration

Create a `config.yaml` file with your Nornir configuration:

```yaml
inventory:
  plugin: SimpleInventory
  options:
    host_file: "inventory/hosts.yaml"
    group_file: "inventory/groups.yaml"

runner:
  plugin: threaded
  options:
    num_workers: 10

logging:
  enabled: true
  level: INFO
  log_file: "nornir.log"
```

### Example Inventory Files

**inventory/hosts.yaml**:

```yaml
router-01:
  hostname: 192.168.1.1
  username: your_username
  password: your_password
  platform: cisco_ios
  groups:
    - edge_routers
    - production
  data:
    site: datacenter-01
    role: edge
    vendor: cisco

switch-01:
  hostname: 192.168.1.2
  username: your_username
  password: your_password
  platform: cisco_nxos
  groups:
    - core_switches
    - production
  data:
    site: datacenter-01
    role: core
```

**inventory/groups.yaml**:

```yaml
edge_routers:
  username: group_default_username
  password: group_default_password
  data:
    device_type: router
    tier: edge

core_switches:
  username: group_default_username
  password: group_default_password
  data:
    device_type: switch
    tier: core

production:
  data:
    environment: production
```

## Configuration

The server looks for a `config.yaml` file in the current working directory. No environment variables are required.

## Available Tools

All tools accept a standard `filters` object for device selection.

The server provides the following MCP tools organized by intent:

### Inventory Tools

- `list_devices`: Query network inventory with optional filters
- `list_device_groups`: List all inventory groups and their member counts

### Operational Tools (Read-Only Commands)

- `get_device_facts`: Basic device information (vendor, model, OS, uptime)
- `get_interfaces_detailed`: Interface status, IP addresses, speed, errors
- `get_bgp_detailed`: BGP neighbor state and address-family details merged per neighbor
- `get_lldp_detailed`: Network topology via LLDP with summary and detailed information merged per interface
- `get_device_configs`: Retrieve device configuration text (running, startup, or candidate)
- `run_show_commands`: Execute show/display commands with optional parsing
- `get_arp_table`: Retrieve the ARP table for network devices (IP-to-MAC mappings)
- `get_mac_address_table`: Retrieve the MAC address table (CAM table) for switches

### Configuration Tools (State-Modifying Commands)

- `send_config_commands`: Send configuration commands to network devices via SSH (modifies device configuration)
- `backup_device_configs`: Save device configuration to local disk

## Usage

### Running the Server

```bash
# Ensure config.yaml exists in current directory and run
nornir-mcp
```

### Development Mode

```bash
# Run with hot reload for development
fastmcp dev src/nornir_mcp/server.py
```

### Architecture

The server implements a Version 2 Service-Intent Pattern with:

- **Services Layer**: `NornirRunner` service handles standardized execution, filtering, and result formatting
- **Intent-Based Tools**: Organized into operational (read-only) and configuration (state-modifying) categories
- **Centralized Processing**: All tools leverage the same execution pipeline for consistency

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nornir-network": {
      "command": "nornir-mcp",
      "workingDir": "/path/to/your/network/project",
      "args": []
    }
  }
}
```

## Device Filtering

All tools support optional filtering via a standard `filters` object. **If no filters are provided, the tool targets all devices in the inventory** (Nornir's default behavior).

The server supports schema-agnostic filtering through a Pydantic model with three core fields:

- **hostname**: Matches either the Nornir Inventory Name (ID) OR the actual device hostname/IP
- **group**: Matches group membership (e.g., "edge_routers", "production")
- **platform**: Matches platform type (e.g., "cisco_ios", "arista_eos")

Examples:

- "Get facts for all devices" → `get_device_facts()` (no filters)
- "Get facts for router-01" → `get_device_facts(filters=DeviceFilters(hostname="router-01"))`
- "Show interfaces on all edge routers" → `get_interfaces_detailed(filters=DeviceFilters(group="edge_routers"))`
- "Get interface GigabitEthernet0/0 on router-01" → `get_interfaces_detailed(filters=DeviceFilters(hostname="router-01"), interface="GigabitEthernet0/0")`
- "Get running config for all devices" → `get_device_configs(retrieve="running")`
- "Backup configurations for edge routers to ./backups" → `get_device_configs(filters=DeviceFilters(group="edge_routers"), backup=True, backup_directory="./backups")`
- "List all Cisco IOS devices in production" → `list_devices(filters=DeviceFilters(platform="cisco_ios", group="production"))`
- "Configure interface on router-01" → `send_config_commands(commands=["interface Loopback100", "description MCP_ADDED"], filters=DeviceFilters(hostname="router-01"))`

Multiple filters are combined with AND logic. Claude will intelligently choose the appropriate filter parameters based on your natural language request, or omit filters entirely to target all devices.

## Supported Platforms

**NAPALM** (normalized multi-vendor):

- `cisco_ios`, `cisco_nxos`, `cisco_iosxr`
- `arista_eos`
- `juniper_junos`

**Netmiko** (100+ platforms):

- All NAPALM platforms above
- `cisco_asa`, `cisco_ftd`
- `hp_comware`, `huawei`
- `dell_os10`, `paloalto_panos`
- And many more

## Security Best Practices

1. **Use read-only accounts** for network devices
2. **Prefer SSH keys** over passwords
3. **Set restrictive file permissions** on configuration files
4. **Use environment variables** for credentials
5. **Run in isolated management networks**
6. **Enable audit logging** for compliance
7. **Configuration backups are strictly sandboxed** to the local project directory to prevent path traversal vulnerabilities

## Troubleshooting

### Common Issues

- **"No Nornir config found"**: Ensure `config.yaml` exists in the current working directory
- **"Connection timeout"**: Verify network connectivity and SSH access
- **"Authentication failed"**: Check credentials and device access
- **"Platform not supported"**: Verify correct platform string in inventory

### Debugging

Enable debug logging by setting the environment variable:

```bash
export LOG_LEVEL=DEBUG
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nornir_mcp
```

### Adding New Tools

To add new tools:

1. Create a new module in `src/nornir_mcp/tools/` or add to existing modules:
   - `monitoring.py` for read-only commands
   - `management.py` for state-modifying commands
   - `inventory.py` for inventory-related operations
2. Implement the tool using the `@mcp.tool()` decorator with a standard `filters` parameter of type `DeviceFilters`
3. Leverage the `NornirRunner` service for standardized execution:

   ```python
   from ..services.runner import runner

   result = await runner.execute(
       task=your_nornir_task,
       filters=filters,
       # Additional parameters as needed
   )
   ```

4. Add tests in the `tests/` directory

## License

MIT License - see the [LICENSE](LICENSE) file for details.
