# Nornir MCP Server

An MCP (Model Context Protocol) server built with **FastMCP** that exposes Nornir automation capabilities to Claude, enabling natural language interaction with network infrastructure. This server combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

## Features

- **Network Inventory Tools**: List devices, query groups, filter by attributes
- **NAPALM Integration**: Standardized multi-vendor network operations (facts, interfaces, BGP, LLDP, config)
- **Netmiko Integration**: Flexible command execution and connectivity testing
- **Device Filtering**: Supports hostname, group, attribute, and pattern-based filtering
- **Structured Output**: Automatic parsing with TextFSM and Genie (where available)
- **Security Focused**: Sensitive information sanitization and read-only by default

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
  username: ${NETWORK_USER}
  password: ${NETWORK_PASS}
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
  username: ${NETWORK_USER}
  password: ${NETWORK_PASS}
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
  data:
    device_type: router
    tier: edge

core_switches:
  data:
    device_type: switch
    tier: core

production:
  data:
    environment: production
```

## Environment Variables

Set these environment variables:

```bash
export NORNIR_CONFIG_FILE=/absolute/path/to/config.yaml
export NETWORK_USER=your_username
export NETWORK_PASS=your_password
```

## Available Tools

The server provides the following MCP tools:

### Inventory Tools

- `list_devices`: Query network inventory with optional filters
- `get_device_groups`: List all inventory groups and their member counts

### NAPALM Tools (Normalized Multi-Vendor)

- `get_facts`: Basic device information (vendor, model, OS, uptime) - accepts direct parameters
- `get_interfaces`: Interface status, IP addresses, speed, errors
- `get_bgp_neighbors`: BGP neighbor status and statistics - accepts direct parameters
- `get_lldp_neighbors`: Network topology via LLDP - accepts direct parameters
- `get_config`: Device configuration retrieval with sanitization - accepts direct parameters

### Netmiko Tools (Flexible Command Execution)

- `run_show_commands`: Execute show/display commands with optional parsing - accepts direct parameters
- `check_connectivity`: Ping or traceroute from network devices - accepts direct parameters

## Usage

### Running the Server

```bash
# With environment variables set
export NORNIR_CONFIG_FILE=/path/to/config.yaml
nornir-mcp

# Or with direct specification
NORNIR_CONFIG_FILE=/path/to/config.yaml nornir-mcp
```

### Development Mode

```bash
# Run with hot reload for development
fastmcp dev src/nornir_mcp/server.py
```

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nornir-network": {
      "command": "nornir-mcp",
      "args": [],
      "env": {
        "NORNIR_CONFIG_FILE": "/absolute/path/to/config.yaml",
        "NETWORK_USER": "your-username",
        "NETWORK_PASS": "your-password"
      }
    }
  }
}
```

## Device Filtering

The server supports multiple filtering methods:

- **Exact hostname**: `"router-01"`
- **Multiple devices**: `"router-01,router-02,router-03"`
- **Group membership**: `"edge_routers"`
- **Data attributes**: `"role=core"`, `"site=datacenter-01"`
- **Pattern matching**: `"router-*"`, `"*-core-*"`

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

## Troubleshooting

### Common Issues

- **"No Nornir config found"**: Ensure `NORNIR_CONFIG_FILE` is set to an absolute path
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

1. Create a new module in `src/nornir_mcp/tools/`
2. Implement the tool using the `@mcp.tool()` decorator with direct parameters
3. Add tests in the `tests/` directory

## License

MIT License - see the [LICENSE](LICENSE) file for details.
