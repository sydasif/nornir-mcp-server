# Nornir MCP Server

An MCP (Model Context Protocol) server built with **FastMCP** that exposes Nornir automation capabilities to Claude, enabling natural language interaction with network infrastructure. This server combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

The server provides **26 tools** organized by intent: 16 monitoring tools, 6 management tools, 2 inventory tools, and 2 networking tools.

## Features

- **Network Inventory Tools**: List devices, query groups, filter by attributes
- **Monitoring Tools**: Read-only commands for network state retrieval (facts, interfaces, BGP, LLDP, configs, ARP/MAC tables, routing tables, users, VLANs)
- **Advanced Monitoring Tools**: Detailed BGP neighbors, LLDP neighbors, network instances (VRFs)
- **Networking Tools**: Ping and traceroute capabilities for connectivity testing
- **Management Tools**: State-modifying commands for network device management (config commands, backups, file transfers)
- **Validation & Security**: Command validation with configurable blacklists, comprehensive input validation
- **MCP Ecosystem**: Prompts system for guided troubleshooting workflows, resources for topology and command reference
- **Service-Intent Architecture**: Clean separation between monitoring (read) and management (write) operations
- **Device Filtering**: Supports hostname, group, attribute, and pattern-based filtering
- **Structured Output**: Standardized result formatting with error handling
- **Security Focused**: Sensitive information sanitization, command validation, and intent-based access controls
- **Production Ready**: Docker containerization, comprehensive configuration examples

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

The server looks for a `config.yaml` file in the current working directory. No environment variables are required.

### Quick Start with Examples

For immediate testing, copy the example configuration files:

```bash
# Copy example configuration files
cp examples/conf/* .

# Or use the provided config.yaml directly
# (already includes references to examples/conf/ files)
```

### Configuration Structure

Create a `config.yaml` file with your Nornir configuration:

```yaml
inventory:
  plugin: SimpleInventory
  options:
    host_file: "examples/conf/hosts.yaml"
    group_file: "examples/conf/groups.yaml"
    defaults_file: "examples/conf/defaults.yaml"

runner:
  plugin: threaded
  options:
    num_workers: 100

logging:
  enabled: false
```

### Example Inventory Files

**examples/conf/hosts.yaml**:

```yaml
R1:
  hostname: 192.168.100.101
  platform: ios
  username: cisco
  password: cisco
  groups:
    - cisco_ios
  data:
    role: core_router

R2:
  hostname: 192.168.100.102
  platform: ios
  groups:
    - cisco_ios
  data:
    role: core_router

R3:
  hostname: 192.168.100.103
  platform: ios
  groups:
    - cisco_ios
  data:
    role: core_router
```

**examples/conf/groups.yaml**:

```yaml
cisco_ios:
  platform: ios
  username: cisco
  password: cisco
  data:
    site: main_office
    region: us_west
```

**examples/conf/defaults.yaml**:

```yaml
username: admin
password: admin
platform: ios
data:
  site: unknown
  region: undefined
```

## Configuration

The server looks for a `config.yaml` file in the current working directory. No environment variables are required.

## Available Tools

All tools accept a standard `filters` object for device selection.

The server provides the following MCP tools organized by intent:

### Inventory Tools

- `list_devices`: Query network inventory with optional filters
- `list_device_groups`: List all inventory groups and their member counts

### Monitoring Tools (Read-Only Commands)

- `get_device_facts`: Basic device information (vendor, model, OS, uptime)
- `get_interfaces_detailed`: Interface status, IP addresses, speed, errors
- `get_bgp_detailed`: BGP neighbor state and address-family details merged per neighbor
- `get_lldp_detailed`: Network topology via LLDP with summary and detailed information merged per interface
- `get_device_configs`: Retrieve device configuration text (running, startup, or candidate)
- `run_show_commands`: Execute show/display commands with optional parsing and security validation
- `get_arp_table`: Retrieve the ARP table for network devices (IP-to-MAC mappings)
- `get_mac_address_table`: Retrieve the MAC address table (CAM table) for switches
- `get_routing_table`: Retrieve routing information from network devices (with optional VRF filtering)
- `get_users`: Retrieve user account information from network devices
- `get_vlans`: Retrieve VLAN configuration details from network devices (with optional VLAN ID filtering)

### Advanced Monitoring Tools (Detailed Network State)

- `get_bgp_config`: Retrieve BGP configuration from devices
- `get_bgp_neighbors_detail`: Obtain detailed BGP neighbor information
- `get_lldp_neighbors_detail`: Obtain detailed LLDP neighbor information
- `get_network_instances`: Retrieve network instances (VRFs) information

### Networking Tools (Connectivity Testing)

- `ping`: Execute ping from devices to test connectivity
- `traceroute`: Execute traceroute from devices for path analysis

### Management Tools (State-Modifying Commands)

- `send_config_commands`: Send configuration commands to network devices via SSH with validation
- `backup_device_configs`: Save device configuration to local disk
- `file_copy`: Transfer files to/from network devices securely (supports SCP, SFTP, TFTP)

### Validation & Security Tools

- `validate_params`: Validate input parameters against Pydantic models with helpful error messages

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

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run directly with Docker
docker build -t nornir-mcp .
docker run -v $(pwd)/examples/conf:/app/conf -p 8000:8000 nornir-mcp
```

### Architecture

The server implements a Service-Intent Pattern with:

- **Application Layer** (`application.py`): Initializes FastMCP and manages Nornir configuration
- **Server Entry Point** (`server.py`): Main entry point that registers tools, prompts, and resources
- **Service Layer** (`services/runner.py`): `NornirRunner` handles standardized execution, filtering, and result formatting
- **Tool Categories** (`tools/`): Organized by intent (monitoring, management, inventory, networking, advanced monitoring)
- **Validation Layer** (`utils/validation_helpers.py`): Comprehensive input validation with helpful error messages
- **Security Layer** (`utils/security.py`): Command validation with configurable blacklists
- **MCP Ecosystem**: Prompts (`prompts.py`) and Resources (`resources.py`) for enhanced Claude integration
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

1. **Use read-only accounts** for network devices when possible
2. **Prefer SSH keys** over passwords for authentication
3. **Set restrictive file permissions** on configuration files (600 for YAML files)
4. **Use environment variables** for credentials instead of hardcoded values
5. **Run in isolated management networks** to limit exposure
6. **Enable audit logging** for compliance and troubleshooting
7. **Configuration backups are strictly sandboxed** to prevent path traversal vulnerabilities
8. **Command validation** with configurable blacklists prevents dangerous operations
9. **Input validation** ensures all parameters are properly validated before execution
10. **Sensitive data sanitization** removes passwords and secrets from resource outputs

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
    - `advanced_monitoring.py` for detailed network state queries
    - `networking.py` for connectivity testing tools
    - `management.py` for state-modifying commands
    - `inventory.py` for inventory-related operations
2. Implement the tool using the `@mcp.tool()` decorator with a standard `filters` parameter of type `DeviceFilters`
3. Leverage the `NornirRunner` service for standardized execution:

    ```python
    from ..services.runner import runner

    @mcp.tool()
    async def new_tool(filters: DeviceFilters | None = None) -> dict:
        return await runner.execute(
            task=your_nornir_task,
            filters=filters,
            # Additional parameters as needed
        )
    ```

4. Add tests in the `tests/` directory

### Adding Validation Models

To add new validation models for input validation:

1. Add models to `src/nornir_mcp/models.py` following Pydantic conventions
2. Register models in `MODEL_MAP` in `utils/validation_helpers.py`
3. The `validate_params` tool will automatically support the new models

### Adding Prompts

To add troubleshooting prompts:

1. Add prompt functions to `src/nornir_mcp/prompts.py` with names starting with `prompt_`
2. Functions are automatically registered when the server starts

### Adding Resources

To add MCP resources:

1. Add resource functions to `src/nornir_mcp/resources.py` with names starting with `resource_`
2. Functions are automatically registered when the server starts

### Command Security

Configure command validation by creating a `conf/blacklist.yaml` file:

```yaml
exact_commands:
  - reload
  - erase startup-config
keywords:
  - erase
  - format
disallowed_patterns:
  - ">"
  - ";"
```

## License

MIT License - see the [LICENSE](LICENSE) file for details.
