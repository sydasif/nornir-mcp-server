# Nornir MCP Server

An MCP (Model Context Protocol) server built with **FastMCP** that exposes Nornir automation capabilities to Claude, enabling natural language interaction with network infrastructure. This server combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

The server provides **21 tools** organized by intent: 13 monitoring tools, 6 management tools, and 2 inventory tools.

## Features

- **Network Inventory Tools**: List devices, query groups, filter by attributes
- **Monitoring Tools**: Read-only commands for network state retrieval (facts, interfaces, BGP, LLDP, configs, ARP/MAC tables, routing tables, users, VLANs, BGP configuration)

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
- `get_interfaces`: Interface status, speed, errors (without IP information)
- `get_interfaces_ip`: Interface IP addresses information
- `get_bgp_neighbors`: BGP neighbor state information
- `get_bgp_neighbors_detail`: Detailed BGP neighbor information
- `get_bgp_config`: Retrieve BGP configuration from devices (with optional group and neighbor filtering)
- `get_lldp_neighbors`: LLDP neighbor information
- `get_lldp_neighbors_detail`: Detailed LLDP neighbor information
- `get_device_configs`: Retrieve device configuration text (running, startup, or candidate)
- `run_show_commands`: Execute show/display commands with optional parsing and security validation
- `get_arp_table`: Retrieve the ARP table for network devices (IP-to-MAC mappings)
- `get_mac_address_table`: Retrieve the MAC address table (CAM table) for switches
- `get_routing_table`: Retrieve routing information from network devices (with optional VRF filtering)
- `get_users`: Retrieve user account information from network devices
- `get_vlans`: Retrieve VLAN configuration details from network devices (with optional VLAN ID filtering)
- `get_network_instances`: Retrieve network instances (VRFs) information (replaces the old advanced monitoring function)


### Management Tools (State-Modifying Commands)

- `send_config_commands`: Send configuration commands to network devices via SSH with validation
- `backup_device_configs`: Save device configuration to local disk
- `file_copy`: Transfer files to/from network devices securely (supports SCP, SFTP, TFTP)

### Validation & Security Tools

- `validate_params`: Validate input parameters against Pydantic models with helpful error messages

## Usage

### Quick Start

1. **Copy example configuration:**
```bash
cp examples/conf/* .
```

2. **Run the server:**
```bash
nornir-mcp
```

3. **Configure Claude Desktop** (see integration section below)

### Running the Server

#### Local Development
```bash
# Basic startup
nornir-mcp

# With debug logging
LOG_LEVEL=DEBUG nornir-mcp

# Development mode with hot reload
fastmcp dev src/nornir_mcp/server.py
```

#### Docker Deployment
```bash
# Build and run with Docker Compose (recommended)
docker compose up --build

# Or run directly with Docker
docker build -t nornir-mcp .
docker run -v $(pwd)/examples/conf:/app/conf \
           -e LOG_LEVEL=INFO \
           -p 8000:8000 nornir-mcp
```

#### Environment Variables
- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MCP_HOST`: Server host (default: localhost)
- `MCP_PORT`: Server port (default: 8000)

### MCP Tools Usage Guide

#### Inventory Management

**List all devices:**
```bash
# Get all devices in inventory
list_devices()

# Filter by platform
list_devices(filters={"platform": "cisco_ios"})

# Filter by group
list_devices(filters={"group": "production"})
```

**List device groups:**
```bash
# Get all groups with member counts
list_device_groups()
```

#### Network Monitoring

**Device Information:**
```bash
# Get basic facts for all devices
get_device_facts()

# Get facts for specific device
get_device_facts(filters={"hostname": "R1"})

# Get facts for all Cisco devices
get_device_facts(filters={"platform": "cisco_ios"})
```

**Interface Monitoring:**
```bash
# Get detailed interface info for all devices
get_interfaces()

# Get interface info for specific device
get_interfaces(filters={"hostname": "R1"})

# Get interface counters
get_interfaces_counters()

# Get interface IP information
get_interfaces_ip()
```

**Routing & Connectivity:**
```bash
# Get routing table
get_routing_table()

# Get routing table for specific VRF
get_routing_table(vrf="VPN1")

# Get ARP table
get_arp_table()

# Get MAC address table
get_mac_address_table()
```

**Protocol-Specific Monitoring:**
```bash
# Get BGP neighbors
get_bgp_neighbors()

# Get detailed BGP neighbors
get_bgp_neighbors_detail()

# Get BGP configuration
get_bgp_config()

# Get LLDP neighbors
get_lldp_neighbors()

# Get detailed LLDP neighbors
get_lldp_neighbors_detail()
```

**Configuration & Users:**
```bash
# Get running configuration
get_device_configs(retrieve="running")

# Get startup configuration
get_device_configs(retrieve="startup")

# Get user accounts
get_users()

# Get VLAN information
get_vlans()
```

**Custom Commands:**
```bash
# Run safe show commands
run_show_commands(commands=["show version", "show interfaces"])

# Run commands with filtering
run_show_commands(
    commands=["show ip route", "show arp"],
    filters={"group": "core_routers"}
)
```



#### Network Management

**Configuration Management:**
```bash
# Send configuration commands (SAFE - validated)
send_config_commands(
    commands=[
        "interface Loopback100",
        "description MCP_MANAGED",
        "ip address 10.100.100.100 255.255.255.255"
    ],
    filters={"hostname": "R1"}
)

# Backup configurations
backup_device_configs(backup_directory="./backups")

# Backup specific device configs
backup_device_configs(
    filters={"group": "production"},
    backup_directory="./backups"
)
```

**File Operations:**
```bash
# Copy file to device
file_copy(
    source_file="./configs/new_config.txt",
    dest_file="running-config",
    direction="put",
    filters={"hostname": "R1"}
)

# Copy file from device
file_copy(
    source_file="running-config",
    dest_file="./backups/running-config.txt",
    direction="get",
    filters={"hostname": "R1"}
)
```

#### Validation & Security

**Input Validation:**
```bash
# Validate device parameters
validate_params({"device_name": "R1"}, "DeviceNameModel")

# Validate ping parameters
validate_params({
    "device_name": "R1",
    "destination": "8.8.8.8",
    "count": 5
}, "PingModel")

# Get validation schema
validate_params({}, "DeviceFilters")
```

### MCP Ecosystem Features

#### Prompts (Guided Troubleshooting)

**Available Prompts:**
- `prompt_troubleshoot_network_issue`: General network troubleshooting
- `prompt_troubleshoot_bgp`: BGP session troubleshooting
- `prompt_troubleshoot_interface`: Interface issue troubleshooting

**Usage:**
```bash
# These prompts are available in Claude when using the MCP server
# They provide structured troubleshooting workflows
```

#### Resources (Reference Data)

**Available Resources:**
- `resource://inventory/hosts`: Device inventory with metadata
- `resource://inventory/hosts/{keyword}`: Filtered host search
- `resource://inventory/groups`: Group information
- `resource://topology`: Network topology data
- `resource://cisco_ios_commands`: Command reference

**Usage:**
```bash
# Access via Claude's resource system
# These provide contextual information for troubleshooting
```

### Advanced Configuration

#### Command Blacklist Configuration

Create `conf/blacklist.yaml` for security:

```yaml
exact_commands:
  - reload
  - erase startup-config
  - write erase
  - delete flash:

keywords:
  - erase
  - format
  - delete
  - copy running-config startup-config

disallowed_patterns:
  - ">"
  - "<"
  - ";"
  - "&&"
  - "||"
```

#### Custom Logging

```yaml
logging:
  enabled: true
  level: INFO
  log_file: "nornir-mcp.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### Advanced Runner Configuration

```yaml
runner:
  plugin: threaded
  options:
    num_workers: 50
    max_rate: 10  # Max tasks per second

# Or use serial runner for debugging
runner:
  plugin: serial
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

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "nornir-network": {
      "command": "nornir-mcp",
      "workingDir": "/path/to/your/network/project",
      "args": [],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

For Linux/Windows, the config file is typically at:
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

#### Using MCP Features in Claude

**Natural Language Commands:**
```bash
# Device inventory
"Show me all network devices"
"List devices in the production group"
"Get facts for router R1"

# Monitoring
"Check interface status on all switches"
"Show BGP neighbors for core routers"
"Get routing table from R2"

# Connectivity testing
"Ping 8.8.8.8 from R1"
"Traceroute to google.com from R3"

# Configuration
"Backup running configs for all devices"
"Configure interface Loopback100 on R1"

# Validation
"Validate these BGP parameters: neighbor 10.0.0.1 remote-as 65001"
"Check if this device name is valid: R1"
```

**Using Prompts:**
```bash
# Structured troubleshooting
"I need to troubleshoot a BGP session issue with neighbor 10.0.0.1 on device R1"
"Help me diagnose why interface GigabitEthernet0/0 is down on switch S1"
"There's a general network connectivity problem in the datacenter"
```

**Accessing Resources:**
```bash
# Reference data
"Show me the network topology"
"What commands are available for Cisco IOS devices?"
"List all hosts in the inventory"
"Find devices with 'core' in their name"
```

## Device Filtering

All tools support optional filtering via a standard `filters` object. **If no filters are provided, the tool targets all devices in the inventory** (Nornir's default behavior).

### Filter Parameters

The server supports schema-agnostic filtering through a Pydantic model:

- **hostname** (str | None): Matches device inventory name (ID) or actual hostname/IP
- **group** (str | None): Matches group membership (e.g., "edge_routers", "production")
- **platform** (str | None): Matches platform type (e.g., "cisco_ios", "arista_eos")

### Filtering Examples

#### Basic Filtering
```bash
# No filters - target all devices
get_device_facts()

# Single device by inventory name
get_device_facts(filters={"hostname": "R1"})

# Single device by hostname/IP
get_device_facts(filters={"hostname": "192.168.100.101"})

# All devices in a group
get_interfaces(filters={"group": "core_routers"})

# All devices of a platform type
get_bgp_neighbors(filters={"platform": "cisco_ios"})
```

#### Advanced Filtering
```bash
# Multiple filters (AND logic)
list_devices(filters={"platform": "cisco_ios", "group": "production"})

# Specific interface on specific device (note: separate tools now)
get_interfaces(filters={"hostname": "R1"})
get_interfaces_ip(filters={"hostname": "R1"})

# Routing table for specific VRF on specific devices
get_routing_table(
    filters={"group": "core_routers"},
    vrf="VPN1"
)
```

#### Configuration Management Filtering
```bash
# Backup configs for production devices
backup_device_configs(
    filters={"group": "production"},
    backup_directory="./backups"
)

# Configure specific device
send_config_commands(
    commands=["interface Loopback100", "ip address 10.100.100.100 255.255.255.255"],
    filters={"hostname": "R1"}
)

# Configure all devices in a group
send_config_commands(
    commands=["logging buffered 100000"],
    filters={"platform": "cisco_ios"}
)
```



### Filter Logic

- **Multiple filters**: Combined with AND logic (device must match ALL criteria)
- **Empty filters**: Targets all devices in inventory
- **Partial matches**: Hostname matching is flexible (inventory name OR actual hostname)
- **Case sensitivity**: Platform and group names are case-sensitive

### Natural Language to Filters

Claude automatically translates natural language to appropriate filters:

- "Check all Cisco routers" → `{"platform": "cisco_ios"}`
- "Show me the core switches" → `{"group": "core_switches"}`
- "Get interface status for R1" → `{"hostname": "R1"}`
- "Backup production devices" → `{"group": "production"}`

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

### Common Issues & Solutions

#### Configuration Issues
- **"No Nornir config found"**
  - Ensure `config.yaml` exists in current working directory
  - Copy from `examples/conf/config.yaml` if needed
  - Check file permissions (readable by user running server)

- **"Inventory file not found"**
  - Verify paths in `config.yaml` are correct
  - Use absolute paths or ensure relative paths are from working directory
  - Copy example inventory files: `cp examples/conf/* .`

#### Connection Issues
- **"Connection timeout"**
  - Verify SSH access to devices: `ssh user@device-hostname`
  - Check network connectivity and firewall rules
  - Confirm device is reachable: `ping device-hostname`
  - Verify SSH service is running on device

- **"Authentication failed"**
  - Check username/password in inventory files
  - Verify SSH key authentication if configured
  - Confirm credentials work manually: `ssh user@device`
  - Check for expired passwords or account lockouts

#### Platform Issues
- **"Platform not supported"**
  - Verify correct platform string in inventory
  - Supported platforms: `cisco_ios`, `cisco_nxos`, `arista_eos`, etc.
  - Check platform name matches Netmiko/NAPALM expectations

- **"Command not found" or "Invalid command"**
  - Verify device platform supports the command
  - Some commands are platform-specific (e.g., `show ip arp` vs `show arp`)
  - Check device OS version compatibility

#### Tool-Specific Issues
- **"Command blocked by security policy"**
  - Command contains blacklisted keywords
  - Modify `conf/blacklist.yaml` or use different command
  - Some destructive commands are intentionally blocked

- **"Device not found in inventory"**
  - Check device name spelling in filters
  - Verify device exists in inventory files
  - Use `list_devices()` to see available devices

- **"Validation error"**
  - Check parameter types and required fields
  - Use `validate_params()` to check input format
  - Refer to model schemas for correct parameter structure

#### Docker Issues
- **"Permission denied"**
  - Ensure Docker daemon is running: `docker info`
  - Add user to docker group: `sudo usermod -aG docker $USER`
  - Or run with sudo: `sudo docker compose up`

- **"Port already in use"**
  - Change port mapping: `-p 8001:8000`
  - Find process using port: `lsof -i :8000`
  - Stop conflicting service

### Debugging & Logging

#### Enable Debug Logging
```bash
# Environment variable
export LOG_LEVEL=DEBUG
nornir-mcp

# Or inline
LOG_LEVEL=DEBUG nornir-mcp
```

#### Log Levels
- `DEBUG`: Detailed execution information, API calls, command output
- `INFO`: General operational messages, task completion
- `WARNING`: Non-critical issues, deprecated features
- `ERROR`: Serious problems requiring attention
- `CRITICAL`: System-level failures

#### Log File Configuration
```yaml
logging:
  enabled: true
  level: DEBUG
  log_file: "nornir-mcp.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### Common Debug Commands
```bash
# Test basic connectivity
ping device-hostname

# Test SSH access
ssh -o ConnectTimeout=10 user@device-hostname "show version"

# Test Nornir configuration
python -c "from src.nornir_mcp.application import get_nr; print('Nornir loaded:', len(get_nr().inventory.hosts), 'devices')"

# Validate configuration syntax
python -c "import yaml; yaml.safe_load(open('config.yaml')); print('Config syntax OK')"
```

### Performance Issues

#### Slow Command Execution
- **Large inventory**: Use filters to target specific devices
- **Network latency**: Optimize worker count in runner config
- **Device performance**: Some devices respond slower than others

#### Memory Usage
- **Large outputs**: Use filters to limit device count
- **Config backups**: Clean up old backup files regularly
- **Concurrent tasks**: Reduce `num_workers` if memory constrained

### Getting Help

#### Community Resources
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check this README and CLAUDE.md
- **Nornir Docs**: https://nornir.tech/
- **NAPALM Docs**: https://napalm.readthedocs.io/
- **Netmiko Docs**: https://netmiko.readthedocs.io/

#### Diagnostic Information
When reporting issues, include:
- Server version and platform
- Full error message and traceback
- Configuration (redact sensitive data)
- Device platform and version
- Steps to reproduce the issue

## Advanced Usage Patterns

### Batch Operations

```bash
# Configure multiple devices at once
send_config_commands(
    commands=[
        "snmp-server community public RO",
        "snmp-server location 'Data Center 1'"
    ],
    filters={"platform": "cisco_ios"}
)

# Backup all production configs
backup_device_configs(
    filters={"group": "production"},
    backup_directory="./backups/prod-$(date +%Y%m%d)"
)
```

### Conditional Operations

```bash
# Use validation to check parameters before execution
validation = validate_params({"device_name": "R1"}, "DeviceNameModel")
if validation["success"]:
    result = get_device_facts(filters={"hostname": "R1"})
```

### Monitoring Workflows

```bash
# Comprehensive health check
facts = get_device_facts()
interfaces = get_interfaces()
bgp = get_bgp_neighbors()
lldp = get_lldp_neighbors()

# Automated troubleshooting
if "BGP neighbor down" in some_condition:
    # Use prompt_troubleshoot_bgp
    detailed_bgp = get_bgp_neighbors_detail()  # Detailed neighbor information
    bgp_config = get_bgp_config()
```

### Integration Patterns

```bash
# Combine with other systems
devices = list_devices()
for device in devices:
    if device["platform"] == "cisco_ios":
        config = get_device_configs(filters={"hostname": device["name"]})
        # Process config, update CMDB, etc.
```

## MCP Ecosystem Deep Dive

### Prompts System

The server includes structured prompts for common troubleshooting scenarios:

#### Available Prompts
- **`prompt_troubleshoot_network_issue`**: Generic network problem diagnosis
  - Usage: "I need to troubleshoot a connectivity issue on device R1"
  - Provides: Step-by-step systematic approach

- **`prompt_troubleshoot_bgp`**: BGP session analysis
  - Usage: "BGP session with neighbor 10.0.0.1 is down on R1"
  - Provides: BGP-specific diagnostic workflow

- **`prompt_troubleshoot_interface`**: Interface problem resolution
  - Usage: "Interface GigabitEthernet0/0 is down on switch S1"
  - Provides: Interface-specific troubleshooting steps

#### Using Prompts in Claude
```bash
# Natural language triggers prompt selection
"Troubleshoot BGP issues on router R2"
"Help diagnose interface problems on switch S1"
"Network connectivity issues in the branch office"
```

### Resources System

Reference data accessible through Claude's resource system:

#### Inventory Resources
- **`resource://inventory/hosts`**: Complete device inventory
- **`resource://inventory/hosts/{keyword}`**: Filtered device search
- **`resource://inventory/groups`**: Group membership information

#### Network Resources
- **`resource://topology`**: Network topology visualization
- **`resource://cisco_ios_commands`**: Cisco IOS command reference

#### Using Resources
```bash
# Access reference data
"Show me the network topology"
"What commands are available for Cisco devices?"
"Find all core routers in the inventory"
"Show devices with 'edge' in their name"
```

### Validation System

Comprehensive input validation with helpful error messages:

#### Model Validation
```bash
# Device name validation
validate_params({"device_name": "R1"}, "DeviceNameModel")

# Ping parameters validation
validate_params({
    "device_name": "R1",
    "destination": "8.8.8.8",
    "count": 5
}, "PingModel")

# Get schema information
result = validate_params({}, "DeviceFilters")
# Returns model schema and example values
```

#### Error Handling
Validation provides:
- **Success/failure status**
- **Detailed error messages**
- **Correct parameter examples**
- **Suggested parameter corrections**

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nornir_mcp

# Run specific test file
pytest tests/test_inventory.py
```

### Adding New Tools

To add new tools:

1. Create a new module in `src/nornir_mcp/tools/` or add to existing modules:
      - `monitoring.py` for read-only commands (including detailed network state queries)
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

### Architecture Patterns

The codebase embraces domain-appropriate patterns:
- **NAPALM operations**: Use `napalm_getter` helper for structured data retrieval
- **Netmiko operations**: Use direct `runner.execute()` for command execution
- **Inventory operations**: Use direct `get_nr() + apply_filters()` for metadata queries

### Import Centralization

Nornir task imports are centralized in `src/nornir_mcp/utils/tasks.py`:
- All tool modules import from the centralized location instead of direct Nornir imports
- Makes Nornir version upgrades easier and reduces import scattering
- Maintains type safety and IDE support

### Helper Functions

Reusable helper functions in `src/nornir_mcp/utils/helpers.py`:
- `normalize_device_filters()`: Consistent device filter normalization across tools
- `napalm_getter()`: Standardized NAPALM getter execution pattern

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

## Contributing

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-org/nornir-mcp-server.git
cd nornir-mcp-server
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check . --fix
uv run ruff format .

# Development server
uv run fastmcp dev src/nornir_mcp/server.py
```

### Adding Features

1. **New Tools**: Follow the service-intent pattern in appropriate tool module
2. **New Platforms**: Add platform support in inventory configuration
3. **New Prompts**: Add to `prompts.py` with `prompt_` prefix
4. **New Resources**: Add to `resources.py` with `resource_` prefix
5. **New Validation**: Add models to `models.py` and register in validation helpers

### Code Standards

- **Linting**: `ruff check` and `ruff format`
- **Testing**: pytest with coverage reporting
- **Documentation**: Update README and docstrings
- **Commits**: Conventional commit format

## Version History

### v1.0.0 - Hybrid Implementation
- **26 MCP tools** across 6 categories
- **Advanced validation** with Pydantic models
- **Command security** with configurable blacklists
- **MCP ecosystem** with prompts and resources
- **Docker containerization**
- **Comprehensive documentation**

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
