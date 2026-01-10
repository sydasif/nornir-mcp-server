
# Nornir MCP Server for Network Engineering

## Overview

An MCP (Model Context Protocol) server built with **FastMCP** that exposes Nornir automation capabilities to Claude, enabling natural language interaction with network infrastructure. This server combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

FastMCP provides a modern, decorator-based framework that makes building MCP servers clean and efficient with automatic validation, error handling, and development tools.

## Architecture

```
Claude (MCP Client)
    ↓
FastMCP Server (nornir-mcp)
    ↓
Your Nornir Configuration (config.yaml)
    ↓
Nornir Framework
    ├── NAPALM Plugin (Standardized Operations)
    └── Netmiko Plugin (Raw Commands)
        ↓
Your Network Devices (SSH/API)
```

## Why FastMCP?

[FastMCP](https://github.com/jlowin/fastmcp) is a modern Python framework for building MCP servers with minimal boilerplate:

- **🎯 Simple decorator-based API** - Define tools with `@mcp.tool()`
- **✅ Automatic validation** - Uses Pydantic for type-safe parameters
- **🔄 Hot reload** - Instant updates during development
- **⚡ Async-first** - Efficient concurrent request handling
- **🧪 Built-in testing** - Test utilities included
- **📝 Auto-documentation** - Tools are self-documenting

Example of how clean FastMCP code is:

```python
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("My Server")

class GetFactsRequest(BaseModel):
    devices: str

@mcp.tool()
async def get_facts(request: GetFactsRequest) -> dict:
    """Get device facts from network devices."""
    # Your logic here
    return results
```

## Quick Start

### 1. Install the Server

```bash
# Using uv (recommended)
uv tool install git+https://github.com/sydasif/nornir-stack.git

# Or using pip
pip install git+https://github.com/sydasif/nornir-stack.git
```

### 2. Prepare Nornir Configuration

Create a `config.yaml` with your network inventory:

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
```

### 3. Configure Environment

```bash
export NORNIR_CONFIG_FILE=/absolute/path/to/config.yaml
export NETWORK_USER=your-username
export NETWORK_PASS=your-password
```

### 4. Test the Server (Development Mode)

```bash
# Run with hot reload
fastmcp dev nornir-mcp

# Test a specific tool
fastmcp run nornir-mcp --tool list_devices
```

### 5. Integrate with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nornir-network": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sydasif/nornir-stack.git", "nornir-mcp"],
      "env": {
        "NORNIR_CONFIG_FILE": "/absolute/path/to/config.yaml",
        "NETWORK_USER": "your-username",
        "NETWORK_PASS": "your-password"
      }
    }
  }
}
```

### 6. Start Using

Restart Claude Desktop and ask:

- "List all devices in my network"
- "Check BGP status on edge routers"
- "Show interface errors on core switches"

## Installation & Requirements

### System Requirements

- **Python**: 3.10 or higher
- **Package Manager**: uv (recommended) or pip
- **Network Access**: SSH connectivity to your devices
- **Nornir Config**: Existing inventory and configuration

### Core Dependencies

```txt
# Framework
fastmcp >= 0.2.0

# Nornir Core & Plugins
nornir >= 3.4.0
nornir-napalm >= 0.4.0
nornir-netmiko >= 1.0.0

# Network Automation
napalm >= 4.1.0
netmiko >= 4.3.0

# Parsing & Data Processing
textfsm >= 1.1.3
genie >= 23.12
pyats >= 23.12

# Validation & Config
pydantic >= 2.0.0
pyyaml >= 6.0
```

### Installation Methods

**Method 1: uv tool (Recommended)**

```bash
uv tool install git+https://github.com/sydasif/nornir-stack.git
```

**Method 2: pip**

```bash
pip install git+https://github.com/sydasif/nornir-stack.git
```

**Method 3: From Source**

```bash
git clone https://github.com/sydasif/nornir-stack.git
cd nornir-stack
pip install -e .
```

### Verify Installation

```bash
# Check version
nornir-mcp --version

# List available tools
fastmcp inspect nornir-mcp

# Run health check
fastmcp run nornir-mcp --tool list_devices --params '{}'
```

## Project Structure

```
nornir-mcp-server/
├── src/
│   ├── nornir_mcp/
│   │   ├── __init__.py
│   │   ├── server.py           # FastMCP server initialization
│   │   ├── config.py           # Configuration management
│   │   ├── models.py           # Pydantic request/response models
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── napalm.py       # NAPALM-based tools
│   │   │   ├── netmiko.py      # Netmiko-based tools
│   │   │   ├── inventory.py    # Inventory tools
│   │   │   └── config_mgmt.py  # Config management tools
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── nornir_helper.py # Nornir utilities
│   │       ├── filters.py       # Device filtering logic
│   │       └── formatters.py    # Result formatting
│   │
├── tests/
│   ├── test_napalm_tools.py
│   ├── test_netmiko_tools.py
│   └── conftest.py              # Pytest fixtures
│
├── examples/
│   ├── config.yaml              # Example Nornir config
│   └── inventory/
│       ├── hosts.yaml
│       └── groups.yaml
│
├── pyproject.toml               # Package configuration
├── requirements.txt
└── README.md
```

## FastMCP Server Implementation

### Main Server File

```python
# src/nornir_mcp/server.py
from fastmcp import FastMCP
from nornir import InitNornir
import os
from pathlib import Path

# Initialize FastMCP with metadata
mcp = FastMCP(
    "Nornir Network Automation",
    dependencies=["nornir", "napalm", "netmiko"]
)

# Initialize Nornir from config
def get_nornir():
    config_file = os.getenv("NORNIR_CONFIG_FILE")
    if not config_file:
        # Try local config.yaml
        config_file = Path.cwd() / "config.yaml"
        if not config_file.exists():
            raise ValueError(
                "No Nornir config found. Set NORNIR_CONFIG_FILE or "
                "create config.yaml in current directory"
            )

    return InitNornir(config_file=str(config_file))

# Global Nornir instance
nr = get_nornir()

# Import all tool modules (they register via @mcp.tool())
from .tools import napalm, netmiko, inventory, config_mgmt

# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
```

### Pydantic Models

```python
# src/nornir_mcp/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class DeviceFilter(BaseModel):
    """Base model for device filtering."""
    devices: str = Field(
        description="Device hostname, comma-separated list, or filter (e.g., 'role=core')"
    )

class NapalmGetterRequest(BaseModel):
    """Request for NAPALM getter operations."""
    devices: str = Field(description="Device filter expression")

class NetmikoCommandRequest(BaseModel):
    """Request for Netmiko command execution."""
    devices: str = Field(description="Device filter expression")
    commands: List[str] = Field(description="List of show commands")
    use_textfsm: bool = Field(default=False, description="Parse with TextFSM")
    use_genie: bool = Field(default=False, description="Parse with Genie")

class ConfigRequest(BaseModel):
    """Request for configuration retrieval."""
    devices: str = Field(description="Device filter expression")
    retrieve: Literal["running", "startup", "candidate"] = Field(
        default="running",
        description="Which config to retrieve"
    )
    sanitized: bool = Field(
        default=True,
        description="Remove sensitive information"
    )

class ConnectivityRequest(BaseModel):
    """Request for connectivity testing."""
    devices: str = Field(description="Device filter expression")
    target: str = Field(description="IP or hostname to test")
    test_type: Literal["ping", "traceroute"] = Field(default="ping")
    count: int = Field(default=5, description="Packet count for ping")
    vrf: Optional[str] = Field(default=None, description="VRF name")

class DeviceResult(BaseModel):
    """Standard device operation result."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class ToolResponse(BaseModel):
    """Standard tool response format."""
    results: Dict[str, DeviceResult]
    summary: Optional[str] = None
```

### Tool Implementation Examples

```python
# src/nornir_mcp/tools/napalm.py
from fastmcp import Context
from nornir_napalm.plugins.tasks import napalm_get
from ..server import mcp, nr
from ..models import NapalmGetterRequest, DeviceResult
from ..utils.filters import filter_devices
from ..utils.formatters import format_nornir_results

@mcp.tool()
async def get_facts(request: NapalmGetterRequest) -> dict:
    """
    Retrieve basic device information including vendor, model, OS version,
    uptime, serial number, and hostname.

    This tool uses NAPALM's get_facts getter which provides normalized
    output across different vendor platforms.
    """
    # Filter devices based on request
    filtered_nr = filter_devices(nr, request.devices)

    # Run NAPALM getter
    result = filtered_nr.run(task=napalm_get, getters=["facts"])

    # Format results
    return format_nornir_results(result, "facts")

@mcp.tool()
async def get_interfaces(
    devices: str,
    interface: Optional[str] = None
) -> dict:
    """
    Get detailed interface information including status, IP addresses,
    MAC address, speed, MTU, and error counters.

    Args:
        devices: Device filter expression
        interface: Optional specific interface name to query
    """
    filtered_nr = filter_devices(nr, devices)

    result = filtered_nr.run(task=napalm_get, getters=["interfaces"])
    formatted = format_nornir_results(result, "interfaces")

    # Filter to specific interface if requested
    if interface:
        for device, data in formatted.items():
            if data.get("success") and data.get("result"):
                interfaces = data["result"]
                data["result"] = {
                    k: v for k, v in interfaces.items()
                    if k == interface
                }

    return formatted

@mcp.tool()
async def get_bgp_neighbors(request: NapalmGetterRequest) -> dict:
    """
    Get BGP neighbor status and statistics including state, uptime,
    remote AS, and prefix counts.
    """
    filtered_nr = filter_devices(nr, request.devices)
    result = filtered_nr.run(task=napalm_get, getters=["bgp_neighbors"])
    return format_nornir_results(result, "bgp_neighbors")

@mcp.tool()
async def get_lldp_neighbors(request: NapalmGetterRequest) -> dict:
    """
    Discover network topology via LLDP, showing connected devices
    and ports for each interface.
    """
    filtered_nr = filter_devices(nr, request.devices)
    result = filtered_nr.run(task=napalm_get, getters=["lldp_neighbors"])
    return format_nornir_results(result, "lldp_neighbors")

@mcp.tool()
async def get_config(request: ConfigRequest) -> dict:
    """
    Retrieve device configuration (running, startup, or candidate).
    Sensitive information like passwords is removed by default.
    """
    filtered_nr = filter_devices(nr, request.devices)

    result = filtered_nr.run(
        task=napalm_get,
        getters=["config"],
        retrieve=request.retrieve
    )

    formatted = format_nornir_results(result, "config")

    # Sanitize if requested
    if request.sanitized:
        formatted = sanitize_configs(formatted)

    return formatted
```

```python
# src/nornir_mcp/tools/netmiko.py
from fastmcp import Context
from nornir_netmiko.tasks import netmiko_send_command
from ..server import mcp, nr
from ..models import NetmikoCommandRequest, ConnectivityRequest
from ..utils.filters import filter_devices
from ..utils.formatters import format_command_results

@mcp.tool()
async def run_show_commands(request: NetmikoCommandRequest) -> dict:
    """
    Execute show/display commands on network devices via SSH.

    Supports automatic platform detection and optional parsing with
    TextFSM or Cisco Genie for structured output.

    Example commands by platform:
    - Cisco IOS: show ip interface brief, show version
    - Cisco NX-OS: show interface brief, show vpc
    - Arista: show interfaces status, show ip route
    - Juniper: show interfaces terse, show route
    """
    filtered_nr = filter_devices(nr, request.devices)

    results = {}
    for command in request.commands:
        result = filtered_nr.run(
            task=netmiko_send_command,
            command_string=command,
            use_textfsm=request.use_textfsm,
            use_genie=request.use_genie
        )
        results[command] = format_command_results(result)

    return results

@mcp.tool()
async def check_connectivity(request: ConnectivityRequest) -> dict:
    """
    Execute ping or traceroute from network devices to test reachability.

    Automatically formats the correct command based on device platform
    and test type. Supports VRF-aware testing.
    """
    filtered_nr = filter_devices(nr, request.devices)

    # Build platform-specific command
    def build_ping_command(task):
        platform = task.host.platform
        cmd = build_ping_cmd(
            platform,
            request.target,
            request.test_type,
            request.count,
            request.vrf
        )
        return task.run(task=netmiko_send_command, command_string=cmd)

    result = filtered_nr.run(task=build_ping_command)
    return format_command_results(result)
```

```python
# src/nornir_mcp/tools/inventory.py
from ..server import mcp, nr
from ..utils.filters import filter_devices

@mcp.tool()
async def list_devices(
    filter: Optional[str] = None,
    details: bool = False
) -> dict:
    """
    Query network inventory with optional filters.

    Returns device names, IPs, platforms, and groups. Use 'details=true'
    for full inventory attributes.

    Filter examples:
    - 'role=core' - devices where data.role is 'core'
    - 'site=dc1' - devices at datacenter 1
    - 'edge_routers' - devices in edge_routers group
    """
    if filter:
        filtered_nr = filter_devices(nr, filter)
    else:
        filtered_nr = nr

    devices = []
    for host_name, host in filtered_nr.inventory.hosts.items():
        device_info = {
            "name": host_name,
            "hostname": host.hostname,
            "platform": host.platform,
            "groups": [g.name for g in host.groups]
        }

        if details:
            device_info["data"] = host.data

        devices.append(device_info)

    return {
        "total_devices": len(devices),
        "devices": devices
    }

@mcp.tool()
async def get_device_groups() -> dict:
    """
    List all inventory groups and their member counts.

    Useful for discovering available device groupings like roles,
    sites, or device types.
    """
    groups = {}
    for group_name, group in nr.inventory.groups.items():
        members = [
            h.name for h in nr.inventory.hosts.values()
            if group in h.groups
        ]
        groups[group_name] = {
            "count": len(members),
            "members": members
        }

    return {"groups": groups}
```

### Utility Functions

```python
# src/nornir_mcp/utils/filters.py
from nornir.core import Nornir
from nornir.core.filter import F

def filter_devices(nr: Nornir, filter_str: str) -> Nornir:
    """
    Filter Nornir inventory based on filter expression.

    Supports:
    - Exact hostname: 'router-01'
    - Multiple devices: 'router-01,router-02'
    - Group membership: 'edge_routers'
    - Data attributes: 'role=core', 'site=dc1'
    - Patterns: 'router-*'
    """
    # Comma-separated list
    if ',' in filter_str:
        hosts = [h.strip() for h in filter_str.split(',')]
        return nr.filter(filter_func=lambda h: h.name in hosts)

    # Data attribute filter (key=value)
    if '=' in filter_str:
        key, value = filter_str.split('=', 1)
        return nr.filter(F(data__contains={key: value}))

    # Try exact hostname match
    if filter_str in nr.inventory.hosts:
        return nr.filter(name=filter_str)

    # Try group match
    if filter_str in nr.inventory.groups:
        return nr.filter(filter_func=lambda h: filter_str in [g.name for g in h.groups])

    # Pattern matching (glob-style)
    if '*' in filter_str:
        import fnmatch
        pattern = filter_str
        return nr.filter(filter_func=lambda h: fnmatch.fnmatch(h.name, pattern))

    raise ValueError(f"Invalid filter: {filter_str}")
```

```python
# src/nornir_mcp/utils/formatters.py
from nornir.core.task import AggregatedResult, MultiResult
from typing import Dict, Any

def format_nornir_results(result: AggregatedResult, getter_name: str = None) -> Dict:
    """Format Nornir results into standard response format."""
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            formatted[host] = {
                "success": False,
                "error": {
                    "type": "CommandError",
                    "message": str(multi_result.exception),
                    "details": {
                        "platform": result[host].host.platform,
                        "exception": type(multi_result.exception).__name__
                    }
                }
            }
        else:
            # Extract result data
            data = multi_result[0].result
            if getter_name and isinstance(data, dict):
                data = data.get(getter_name, data)

            formatted[host] = {
                "success": True,
                "result": data
            }

    return formatted

def format_command_results(result: AggregatedResult) -> Dict:
    """Format command execution results."""
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            formatted[host] = {
                "success": False,
                "error": {
                    "type": type(multi_result.exception).__name__,
                    "message": str(multi_result.exception)
                }
            }
        else:
            formatted[host] = {
                "success": True,
                "output": multi_result[0].result
            }

    return formatted
```

## Configuration

### Nornir Configuration

The server requires a standard Nornir `config.yaml`. It locates the configuration:

1. **Environment Variable**: `NORNIR_CONFIG_FILE` (absolute path) - **Recommended**
2. **Local File**: `config.yaml` in current working directory

### Minimum Configuration

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
```

### Production Configuration

```yaml
inventory:
  plugin: SimpleInventory
  options:
    host_file: "inventory/hosts.yaml"
    group_file: "inventory/groups.yaml"
    defaults_file: "inventory/defaults.yaml"

runner:
  plugin: threaded
  options:
    num_workers: 20

logging:
  enabled: true
  level: INFO
  log_file: "nornir.log"
  to_console: true

user_defined:
  connection_options:
    napalm:
      extras:
        timeout: 60
        optional_args:
          global_delay_factor: 2
    netmiko:
      extras:
        timeout: 120
        session_timeout: 60
        auth_timeout: 30
```

### Inventory Structure

**hosts.yaml:**

```yaml
router-edge-01:
  hostname: 192.168.1.1
  platform: cisco_ios
  username: ${NETWORK_USER}
  password: ${NETWORK_PASS}
  groups:
    - edge_routers
    - production
    - datacenter-01
  data:
    site: datacenter-01
    role: edge
    vendor: cisco
    model: ISR4451

switch-core-01:
  hostname: 192.168.2.1
  platform: cisco_nxos
  groups:
    - core_switches
    - production
    - datacenter-01
  data:
    site: datacenter-01
    role: core
    vendor: cisco
```

**groups.yaml:**

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

datacenter-01:
  data:
    location: US-EAST-1
```

### Credential Management

**Never hardcode credentials!** Use environment variables:

```yaml
# In hosts.yaml or defaults.yaml
username: ${NETWORK_USER}
password: ${NETWORK_PASS}
```

```bash
# In your shell or .env file
export NETWORK_USER="readonly-user"
export NETWORK_PASS="secure-password"
```

**Better: Use SSH Keys**

```yaml
connection_options:
  netmiko:
    extras:
      use_keys: true
      key_file: ~/.ssh/network_rsa
```

### Supported Platforms

**NAPALM** (normalized multi-vendor):

- `cisco_ios`, `cisco_nxos`, `cisco_iosxr`
- `arista_eos`
- `juniper_junos`

**Netmiko** (100+ platforms):

- All NAPALM platforms above
- `cisco_asa`, `cisco_ftd`
- `hp_comware`, `huawei`
- `dell_os10`, `paloalto_panos`
- [Full list](https://github.com/ktbyers/netmiko#supports)

## Device Filtering

### Filter Syntax

Format: `attribute=value` or special patterns

**Supported Filters:**

1. **Exact hostname**: `"router-01"`
2. **Multiple devices**: `"router-01,router-02,router-03"`
3. **Group membership**: `"edge_routers"`
4. **Data attributes**: `"role=core"`, `"site=dc1"`
5. **Pattern matching**: `"router-*"`, `"*-core-*"`

### Examples

```python
# Single device
"router-01"

# Multiple devices
"router-01,router-02,switch-01"

# All devices in group
"edge_routers"

# By data attribute
"role=core"           # data.role == 'core'
"site=datacenter-01"  # data.site == 'datacenter-01'
"vendor=cisco"        # data.vendor == 'cisco'

# Pattern matching
"router-*"            # All routers
"*-core-*"           # All core devices
"switch-dc1-*"       # All DC1 switches
```

### Current Limitations

Boolean operators (AND/OR) are not yet implemented. For complex filters:

- Create inventory groups that match your criteria
- Use multiple tool calls
- Filter results in Claude's response

## Claude Desktop Integration

### Configuration Location

- **macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

### Configuration Examples

**Option 1: Using uvx (Recommended - No Installation Required)**

```json
{
  "mcpServers": {
    "nornir-network": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/sydasif/nornir-stack.git",
        "nornir-mcp"
      ],
      "env": {
        "NORNIR_CONFIG_FILE": "/absolute/path/to/config.yaml",
        "NETWORK_USER": "your-username",
        "NETWORK_PASS": "your-password"
      }
    }
  }
}
```

**Option 2: After Installing with uv tool**

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

**Option 3: Development Mode (with working directory)**

```json
{
  "mcpServers": {
    "nornir-network": {
      "command": "fastmcp",
      "args": ["dev", "/path/to/nornir-mcp/src/nornir_mcp/server.py"],
      "cwd": "/path/to/directory/with/config.yaml",
      "env": {
        "NETWORK_USER": "your-username",
        "NETWORK_PASS": "your-password"
      }
    }
  }
}
```

### Security Best Practices

1. **Use environment variables** that are already set system-wide
2. **Restrict file permissions**: `chmod 600 claude_desktop_config.json`
3. **Prefer SSH keys** over passwords
4. **Use read-only accounts** for network devices
5. **Never commit** config files with credentials to Git

### Verify Integration

1. Restart Claude Desktop (completely quit and reopen)
2. Start a new conversation
3. Test with: "List all devices in my network inventory"
4. Claude should use the `list_devices` tool

## MCP Tools Reference

### NAPALM Tools (Normalized Multi-Vendor)

#### get_facts

Get basic device info: vendor, model, OS version, uptime, serial number.

```python
Parameters:
  devices: str  # Device filter

Example:
  "Show OS version on all edge routers"
  "What's the uptime on router-01?"
```

#### get_interfaces

Detailed interface info: status, IPs, MAC, speed, MTU, errors.

```python
Parameters:
  devices: str
  interface: Optional[str]  # Specific interface

Example:
  "Show down interfaces on all switches"
  "Get status of Gi0/0/1 on router-01"
```

#### get_config

Retrieve running/startup configuration, sanitized by default.

```python
Parameters:
  devices: str
  retrieve: "running" | "startup" | "candidate"
  sanitized: bool = True

Example:
  "Get running config from router-01"
  "Show startup config on edge routers"
```

#### get_bgp_neighbors

BGP neighbor status: state, uptime, AS, prefix counts.

```python
Parameters:
  devices: str

Example:
  "Are all BGP sessions up on edge routers?"
  "Show BGP neighbors on router-01"
```

#### get_lldp_neighbors

Network topology via LLDP: connected devices and ports.

```python
Parameters:
  devices: str

Example:
  "Show network topology for datacenter-01"
  "What's connected to switch-core-01?"
```

### Netmiko Tools (Flexible Command Execution)

#### run_show_commands

Execute show/display commands with optional parsing.

```python
Parameters:
  devices: str
  commands: List[str]
  use_textfsm: bool = False
  use_genie: bool = False

Example:
  "Run 'show ip interface brief' on all routers"
  "Execute 'show inventory' and parse with TextFSM"
```

#### check_connectivity

Ping or traceroute from network devices.

```python
Parameters:
  devices: str
  target: str  # IP or hostname
  test_type: "ping" | "traceroute" = "ping"
  count: int = 5
  vrf: Optional[str] = None

Example:
  "Ping 8.8.8.8 from all edge routers"
  "Traceroute to 10.1.1.1 from router-01"
```

### Inventory Tools

#### list_devices

Query inventory with optional filters and detail levels.

```python
Parameters:
  filter: Optional[str] = None
  details: bool = False

Example:
  "List all devices"
  "Show devices in datacenter-01 with details"
```

#### get_device_groups

List all groups and member counts.

```python
Parameters: (none)

Example:
  "What groups are available?"
  "Show all device groups"
```

## Development with FastMCP

### Development Server with Hot Reload

FastMCP includes a built-in development server that automatically reloads when code changes:

```bash
# Start development server
fastmcp dev src/nornir_mcp/server.py

# Server will reload automatically when you edit code
# Great for rapid iteration!
```

### Testing Individual Tools

```bash
# Test a specific tool
fastmcp run nornir-mcp --tool get_facts --params '{"devices": "router-01"}'

# List all available tools
fastmcp inspect nornir-mcp

# Get tool schema
fastmcp inspect nornir-mcp --tool get_facts
```

### Interactive Development

```python
# Use FastMCP's development utilities
from fastmcp.testing import MCPTestClient
from nornir_mcp.server import mcp

async def test_tool():
    async with MCPTestClient(mcp) as client:
        # Test a tool
        result = await client.call_tool(
            "get_facts",
            {"devices": "router-01"}
        )
        print(result)

# Run with asyncio
import asyncio
asyncio.run(test_tool())
```

### Unit Testing with Pytest

```python
# tests/test_napalm_tools.py
import pytest
from fastmcp.testing import MCPTestClient
from nornir_mcp.server import mcp
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_get_facts_success():
    """Test successful device facts retrieval."""
    async with MCPTestClient(mcp) as client:
        # Mock Nornir result
        mock_result = {
            "router-01": {
                "success": True,
                "result": {
                    "vendor": "Cisco",
                    "model": "ISR4451",
                    "os_version": "17.6.3"
                }
            }
        }

        with patch('nornir_mcp.tools.napalm.filter_devices'):
            result = await client.call_tool(
                "get_facts",
                {"devices": "router-01"}
            )

            assert "router-01" in result
            assert result["router-01"]["success"] is True
            assert "vendor" in result["router-01"]["result"]

@pytest.mark.asyncio
async def test_get_facts_connection_error():
    """Test handling of connection failures."""
    async with MCPTestClient(mcp) as client:
        # Test error handling
        result = await client.call_tool(
            "get_facts",
            {"devices": "unreachable-device"}
        )

        assert result["unreachable-device"]["success"] is False
        assert "error" in result["unreachable-device"]

@pytest.mark.asyncio
async def test_invalid_filter():
    """Test invalid filter handling."""
    async with MCPTestClient(mcp) as client:
        with pytest.raises(ValueError):
            await client.call_tool(
                "get_facts",
                {"devices": "invalid!@#$"}
            )
```

### Integration Testing

```python
# tests/test_integration.py
import pytest
from fastmcp.testing import MCPTestClient
from nornir_mcp.server import mcp

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """Test a complete workflow across multiple tools."""
    async with MCPTestClient(mcp) as client:
        # 1. List devices
        devices = await client.call_tool("list_devices", {})
        assert devices["total_devices"] > 0

        # 2. Get facts from first device
        first_device = devices["devices"][0]["name"]
        facts = await client.call_tool(
            "get_facts",
            {"devices": first_device}
        )
        assert facts[first_device]["success"] is True

        # 3. Get interfaces
        interfaces = await client.call_tool(
            "get_interfaces",
            {"devices": first_device}
        )
        assert len(interfaces[first_device]["result"]) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_device_operations():
    """Test operations across multiple devices."""
    async with MCPTestClient(mcp) as client:
        # Test with device group
        result = await client.call_tool(
            "get_facts",
            {"devices": "edge_routers"}
        )

        # Verify partial success handling
        successful = sum(1 for r in result.values() if r["success"])
        assert successful > 0
```

### Pytest Configuration

```python
# tests/conftest.py
import pytest
from nornir import InitNornir
from pathlib import Path

@pytest.fixture(scope="session")
def test_config_path():
    """Path to test Nornir configuration."""
    return Path(__file__).parent / "fixtures" / "config.yaml"

@pytest.fixture(scope="session")
def nornir_instance(test_config_path):
    """Nornir instance for testing."""
    return InitNornir(config_file=str(test_config_path))

@pytest.fixture
def mock_device_result():
    """Mock successful device result."""
    return {
        "success": True,
        "result": {
            "hostname": "test-router",
            "vendor": "Cisco",
            "model": "ISR4451",
            "os_version": "17.6.3",
            "uptime": 86400
        }
    }

@pytest.fixture
def mock_error_result():
    """Mock error result."""
    return {
        "success": False,
        "error": {
            "type": "ConnectionError",
            "message": "Connection timeout",
            "details": {
                "platform": "cisco_ios",
                "exception": "NetmikoTimeoutException"
            }
        }
    }
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nornir_mcp --cov-report=html

# Run specific test file
pytest tests/test_napalm_tools.py

# Run integration tests only
pytest -m integration

# Run with verbose output
pytest -v

# Run and watch for changes
pytest-watch
```

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/sydasif/nornir-stack.git
cd nornir-stack

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Style

This project uses:

- **black** for code formatting
- **ruff** for linting
- **mypy** for type checking
- **pytest** for testing

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all checks
pre-commit run --all-files
```

### Adding New Tools

1. **Create tool module** in `src/nornir_mcp/tools/`
2. **Define Pydantic models** in `src/nornir_mcp/models.py`
3. **Implement tool** using `@mcp.tool()` decorator
4. **Add tests** in `tests/`
5. **Update documentation**

Example:

```python
# src/nornir_mcp/tools/my_tool.py
from fastmcp import Context
from ..server import mcp, nr
from ..models import MyToolRequest

@mcp.tool()
async def my_new_tool(request: MyToolRequest) -> dict:
    """
    Description of what this tool does.

    Explain usage, parameters, and return values.
    """
    # Implementation
    pass
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Make your changes
4. Add tests
5. Run test suite (`pytest`)
6. Update documentation
7. Commit changes (`git commit -m 'Add amazing tool'`)
8. Push to branch (`git push origin feature/amazing-tool`)
9. Open Pull Request

### Testing Guidelines

- Write tests for all new tools
- Aim for >80% code coverage
- Include both unit and integration tests
- Test error conditions
- Mock external dependencies

## Error Handling

### Standard Error Format

All tools return consistent error responses:

```json
{
  "device-name": {
    "success": false,
    "error": {
      "type": "ConnectionError",
      "message": "Failed to connect: Connection timeout",
      "details": {
        "platform": "cisco_ios",
        "hostname": "192.168.1.1",
        "exception": "NetmikoTimeoutException",
        "timestamp": "2025-01-09T14:30:22Z"
      }
    }
  }
}
```

### Error Types

| Type | Description | Common Causes |
|------|-------------|---------------|
| `ConnectionError` | Cannot reach device | Wrong IP, firewall, SSH disabled |
| `AuthenticationError` | Invalid credentials | Wrong username/password, missing keys |
| `CommandError` | Command failed | Invalid syntax, insufficient privileges |
| `TimeoutError` | Operation timeout | Slow device, large output |
| `UnsupportedPlatformError` | Platform not supported | Wrong platform string |
| `InventoryError` | Device not found | Typo in name, wrong filter |
| `ConfigurationError` | Invalid config | Missing/malformed config.yaml |

### Error Handling in FastMCP

```python
# Automatic error handling with FastMCP
@mcp.tool()
async def get_facts(request: NapalmGetterRequest) -> dict:
    """FastMCP automatically catches and formats exceptions."""
    try:
        filtered_nr = filter_devices(nr, request.devices)
        result = filtered_nr.run(task=napalm_get, getters=["facts"])
        return format_nornir_results(result, "facts")
    except ValueError as e:
        # Custom error for invalid filters
        raise ValueError(f"Invalid device filter: {request.devices}") from e
    except Exception as e:
        # FastMCP will format this as a proper MCP error
        raise

# Partial success handling
def format_nornir_results(result: AggregatedResult, getter: str) -> dict:
    """Handle mix of successful and failed devices."""
    formatted = {}

    for host, multi_result in result.items():
        if multi_result.failed:
            formatted[host] = {
                "success": False,
                "error": {
                    "type": type(multi_result.exception).__name__,
                    "message": str(multi_result.exception),
                    "details": {
                        "platform": result[host].host.platform
                    }
                }
            }
        else:
            formatted[host] = {
                "success": True,
                "result": multi_result[0].result.get(getter, {})
            }

    return formatted
```

### Troubleshooting Guide

**"Device not found in inventory"**

```bash
# Check device exists
fastmcp run nornir-mcp --tool list_devices

# Check filter syntax
fastmcp run nornir-mcp --tool list_devices --params '{"filter": "role=core"}'
```

**"Connection timeout"**

```bash
# Verify network connectivity
ping 192.168.1.1

# Test SSH manually
ssh admin@192.168.1.1

# Check firewall rules
# Ensure NORNIR_CONFIG_FILE is set correctly
echo $NORNIR_CONFIG_FILE
```

**"Authentication failed"**

```bash
# Verify credentials are set
echo $NETWORK_USER
echo $NETWORK_PASS  # Don't actually do this in production!

# Test credentials manually
ssh $NETWORK_USER@192.168.1.1

# Check platform string matches device
# Verify enable password if required
```

**"Config file not found"**

```bash
# Check environment variable
echo $NORNIR_CONFIG_FILE

# Verify file exists
ls -la $NORNIR_CONFIG_FILE

# Check working directory has config.yaml
ls -la config.yaml
```

**"Platform not supported"**

- Verify platform string in inventory matches device OS
- Check NAPALM/Netmiko supported platforms
- Ensure correct driver is installed

## Deployment

### Development Mode

For active development with automatic reload:

```bash
# Start development server
fastmcp dev src/nornir_mcp/server.py

# Server reloads automatically when code changes
# Access at the MCP endpoint
```

### Production Deployment

**Option 1: System-wide installation**

```bash
# Install with uv
uv tool install git+https://github.com/sydasif/nornir-stack.git

# Run the server
nornir-mcp
```

**Option 2: Virtual environment**

```bash
# Create venv
python -m venv venv
source venv/bin/activate

# Install
pip install git+https://github.com/sydasif/nornir-stack.git

# Run
nornir-mcp
```

**Option 3: systemd Service (Linux)**

```ini
# /etc/systemd/system/nornir-mcp.service
[Unit]
Description=Nornir MCP Server
After=network.target

[Service]
Type=simple
User=netadmin
Group=netadmin
WorkingDirectory=/opt/nornir-mcp
Environment="NORNIR_CONFIG_FILE=/etc/nornir/config.yaml"
Environment="NETWORK_USER=readonly"
Environment="NETWORK_PASS=secure-password"
ExecStart=/usr/local/bin/nornir-mcp
Restart=on-failure
RestartSec=5s

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/nornir

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nornir-mcp
sudo systemctl start nornir-mcp

# Check status
sudo systemctl status nornir-mcp

# View logs
sudo journalctl -u nornir-mcp -f
```

**Option 4: Docker**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 netadmin && \
    chown -R netadmin:netadmin /app
USER netadmin

# Volume for config
VOLUME ["/config"]

# Environment
ENV NORNIR_CONFIG_FILE=/config/config.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD fastmcp run nornir-mcp --tool list_devices --params '{}' || exit 1

# Run server
CMD ["fastmcp", "run", "src/nornir_mcp/server.py"]
```

```bash
# Build image
docker build -t nornir-mcp:latest .

# Run container
docker run -d \
  --name nornir-mcp \
  -v /path/to/config:/config \
  -e NETWORK_USER=admin \
  -e NETWORK_PASS=password \
  --restart unless-stopped \
  nornir-mcp:latest

# View logs
docker logs -f nornir-mcp
```

**Option 5: Docker Compose**

```yaml
# docker-compose.yml
version: '3.8'

services:
  nornir-mcp:
    build: .
    container_name: nornir-mcp
    volumes:
      - ./config:/config:ro
      - ./logs:/var/log/nornir
    environment:
      - NORNIR_CONFIG_FILE=/config/config.yaml
      - NETWORK_USER=${NETWORK_USER}
      - NETWORK_PASS=${NETWORK_PASS}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "fastmcp", "run", "nornir-mcp", "--tool", "list_devices"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
# Start with compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NORNIR_CONFIG_FILE` | Yes | Absolute path to config.yaml | `/etc/nornir/config.yaml` |
| `NETWORK_USER` | Yes* | Default username for devices | `admin` |
| `NETWORK_PASS` | Yes* | Default password for devices | `secure-password` |
| `PYTHONUNBUFFERED` | No | Disable Python output buffering | `1` |
| `LOG_LEVEL` | No | Logging level | `INFO` |

*Required unless using SSH keys or per-device credentials

### Security Hardening

**1. Use Read-Only Accounts**

```yaml
# Create read-only user on devices
username readonly-user privilege 1 secret your-password

# Grant only show commands
privilege exec level 1 show
```

**2. SSH Key Authentication**

```yaml
# In Nornir inventory
connection_options:
  netmiko:
    extras:
      use_keys: true
      key_file: /home/netadmin/.ssh/network_rsa
```

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/network_rsa

# Copy to devices
ssh-copy-id -i ~/.ssh/network_rsa.pub admin@router-01
```

**3. Secrets Management**

Using HashiCorp Vault:

```python
# src/nornir_mcp/config.py
import hvac

def get_credentials():
    client = hvac.Client(url='http://vault:8200')
    client.token = os.getenv('VAULT_TOKEN')

    secret = client.secrets.kv.v2.read_secret_version(
        path='network/credentials'
    )

    return {
        'username': secret['data']['data']['username'],
        'password': secret['data']['data']['password']
    }
```

**4. Network Segmentation**

- Run MCP server in management VLAN
- Use jump host/bastion for device access
- Firewall rules to restrict SSH to management network

**5. Audit Logging**

```python
# Add audit logging to tools
import logging
from datetime import datetime

audit_logger = logging.getLogger('audit')

@mcp.tool()
async def get_config(request: ConfigRequest) -> dict:
    # Log the operation
    audit_logger.info(
        f"CONFIG_ACCESS - User requested config from {request.devices} "
        f"at {datetime.utcnow().isoformat()}"
    )

    # ... rest of implementation
```

## Monitoring and Logging

### FastMCP Logging

FastMCP provides built-in logging:

```python
# src/nornir_mcp/server.py
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nornir-mcp.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('nornir-mcp')

@mcp.tool()
async def get_facts(request: NapalmGetterRequest) -> dict:
    logger.info(f"get_facts called for devices: {request.devices}")

    try:
        result = # ... implementation
        logger.info(f"get_facts completed successfully for {len(result)} devices")
        return result
    except Exception as e:
        logger.error(f"get_facts failed: {str(e)}", exc_info=True)
        raise
```

### Metrics to Track

```python
# src/nornir_mcp/utils/metrics.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
import time

@dataclass
class ToolMetrics:
    tool_name: str
    start_time: float
    end_time: float
    success_count: int
    failure_count: int
    devices_processed: int

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0

# Track metrics
metrics_store: Dict[str, list] = {}

def track_metrics(tool_name: str):
    """Decorator to track tool metrics."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Count successes/failures
                success = sum(1 for r in result.values() if r.get("success"))
                failure = len(result) - success

                metrics = ToolMetrics(
                    tool_name=tool_name,
                    start_time=start_time,
                    end_time=time.time(),
                    success_count=success,
                    failure_count=failure,
                    devices_processed=len(result)
                )

                if tool_name not in metrics_store:
                    metrics_store[tool_name] = []
                metrics_store[tool_name].append(metrics)

                logger.info(
                    f"{tool_name} - Duration: {metrics.duration:.2f}s, "
                    f"Success: {success}/{len(result)}, "
                    f"Rate: {metrics.success_rate:.1f}%"
                )

                return result
            except Exception as e:
                logger.error(f"{tool_name} failed: {str(e)}")
                raise

        return wrapper
    return decorator

# Usage
@mcp.tool()
@track_metrics("get_facts")
async def get_facts(request: NapalmGetterRequest) -> dict:
    # ... implementation
```

### Performance Optimization

### Parallel Execution with Nornir

```python
# Adjust worker count based on infrastructure
runner:
  plugin: threaded
  options:
    num_workers: 50  # Increase for large environments
```

### Connection Pooling

```python
# src/nornir_mcp/utils/connection_pool.py
from typing import Dict
from nornir.core.inventory import Host
from netmiko import ConnectHandler

class ConnectionPool:
    """Reuse SSH connections across tool calls."""

    def __init__(self, max_age: int = 300):
        self._connections: Dict[str, tuple] = {}
        self.max_age = max_age

    def get_connection(self, host: Host):
        """Get or create connection for host."""
        key = f"{host.hostname}:{host.platform}"

        if key in self._connections:
            conn, timestamp = self._connections[key]
            if time.time() - timestamp < self.max_age:
                return conn
            else:
                conn.disconnect()

        # Create new connection
        conn = ConnectHandler(
            device_type=host.platform,
            host=host.hostname,
            username=host.username,
            password=host.password
        )

        self._connections[key] = (conn, time.time())
        return conn

    def cleanup(self):
        """Close all connections."""
        for conn, _ in self._connections.values():
            try:
                conn.disconnect()
            except:
                pass
        self._connections.clear()

# Global pool
conn_pool = ConnectionPool()
```

### Caching Strategy

```python
# src/nornir_mcp/utils/cache.py
from functools import lru_cache
import time
from typing import Any, Callable

class TTLCache:
    """Time-based cache for slow-changing data."""

    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._cache = {}

    def get(self, key: str) -> Any:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time())

    def clear(self):
        self._cache.clear()

# Cache for facts (change infrequently)
facts_cache = TTLCache(ttl=600)  # 10 minutes

@mcp.tool()
async def get_facts(request: NapalmGetterRequest) -> dict:
    # Check cache
    cache_key = f"facts:{request.devices}"
    cached = facts_cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for {cache_key}")
        return cached

    # Fetch from devices
    result = # ... implementation

    # Store in cache
    facts_cache.set(cache_key, result)
    return result
```

### Batch Operations

```python
# Process devices in batches for very large environments
async def batch_process(devices: list, batch_size: int = 50):
    """Process devices in batches to avoid overwhelming network."""
    results = {}

    for i in range(0, len(devices), batch_size):
        batch = devices[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}")

        batch_result = await process_batch(batch)
        results.update(batch_result)

        # Small delay between batches
        await asyncio.sleep(1)

    return results
```

## Extending the Server

### Adding Custom Tools

```python
# src/nornir_mcp/tools/custom.py
from fastmcp import Context
from ..server import mcp, nr
from ..models import DeviceFilter
from ..utils.filters import filter_devices

@mcp.tool()
async def custom_health_check(request: DeviceFilter) -> dict:
    """
    Custom health check combining multiple metrics.

    Checks: CPU, memory, interface errors, BGP status
    """
    filtered_nr = filter_devices(nr, request.devices)

    results = {}
    for host in filtered_nr.inventory.hosts.values():
        health_data = {
            "cpu": await check_cpu(host),
            "memory": await check_memory(host),
            "interfaces": await check_interface_errors(host),
            "bgp": await check_bgp_status(host)
        }

        # Calculate overall health score
        health_data["score"] = calculate_health_score(health_data)
        health_data["status"] = "healthy" if health_data["score"] > 80 else "degraded"

        results[host.name] = {
            "success": True,
            "result": health_data
        }

    return results
```

### Adding Custom Parsers

```python
# src/nornir_mcp/utils/parsers.py
import re
from typing import Dict, List

def parse_custom_output(output: str) -> List[Dict]:
    """Custom parser for vendor-specific output."""
    results = []

    # Your parsing logic
    pattern = r'Interface: (\S+)\s+Status: (\S+)'
    for match in re.finditer(pattern, output):
        results.append({
            "interface": match.group(1),
            "status": match.group(2)
        })

    return results

# Use in tool
@mcp.tool()
async def custom_interface_check(request: NetmikoCommandRequest) -> dict:
    result = await run_commands(request)

    # Apply custom parser
    for device, data in result.items():
        if data["success"]:
            data["parsed"] = parse_custom_output(data["output"])

    return result
```

### Integration with External Systems

```python
# src/nornir_mcp/integrations/netbox.py
import pynetbox

@mcp.tool()
async def sync_with_netbox(netbox_url: str, token: str) -> dict:
    """Sync device facts with NetBox DCIM."""
    nb = pynetbox.api(netbox_url, token=token)

    # Get facts from devices
    facts = await get_facts({"devices": "all"})

    # Update NetBox
    updated = []
    for device_name, data in facts.items():
        if data["success"]:
            device = nb.dcim.devices.get(name=device_name)
            if device:
                device.serial = data["result"]["serial_number"]
                device.save()
                updated.append(device_name)

    return {
        "updated_devices": updated,
        "count": len(updated)
    }
```

## Troubleshooting

### Common Issues

**Issue: "FastMCP module not found"**

```bash
# Solution: Install FastMCP
pip install fastmcp

# Or reinstall the package
uv tool install --force git+https://github.com/sydasif/nornir-stack.git
```

**Issue: "No tools registered"**

```python
# Solution: Ensure tool modules are imported in server.py
from .tools import napalm, netmiko, inventory, config_mgmt

# Tools must be imported for @mcp.tool() decorator to register them
```

**Issue: "Pydantic validation error"**

```python
# Solution: Check parameter types match model
# BAD:
{"devices": ["router-01", "router-02"]}  # List instead of string

# GOOD:
{"devices": "router-01,router-02"}  # Comma-separated string
```

**Issue: "Hot reload not working"**

```bash
# Solution: Use correct FastMCP dev command
fastmcp dev src/nornir_mcp/server.py

# Not: python src/nornir_mcp/server.py
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG
```

### Verbose Output

```bash
# Run with verbose FastMCP output
fastmcp run --verbose nornir-mcp --tool get_facts --params '{"devices": "router-01"}'
```

## Best Practices

### Tool Design

1. **Keep tools focused** - Each tool should do one thing well
2. **Use Pydantic models** - Define clear request/response schemas
3. **Handle partial failures** - Return both successes and failures
4. **Add docstrings** - Tools are self-documenting via docstrings
5. **Log operations** - Track what's being executed

### Security

1. **Read-only by default** - No configuration changes
2. **Use SSH keys** - Avoid password authentication
3. **Audit logging** - Track all device access
4. **Least privilege** - Use read-only accounts
5. **Network segmentation** - Isolate management traffic

### Performance

1. **Use connection pooling** - Reuse SSH sessions
2. **Cache slow data** - Facts, LLDP don't change often
3. **Parallel execution** - Leverage Nornir's threading
4. **Batch large operations** - Don't overwhelm devices
5. **Set appropriate timeouts** - Balance speed vs reliability

### Error Handling

1. **Fail gracefully** - Return errors, don't crash
2. **Provide context** - Include device, platform, error type
3. **Partial success** - Some devices failing is normal
4. **Retry logic** - For transient network issues
5. **Helpful messages** - Guide users to solutions

## Changelog

### Version 1.0.0 (2025-01-10)

**Initial Release**

- FastMCP-based server implementation
- 13 MCP tools for network automation
- NAPALM tools: facts, interfaces, config, BGP, LLDP
- Netmiko tools: show commands, connectivity testing
- Inventory tools: device listing, group management
- Configuration management: backup, compare
- Comprehensive error handling
- Pydantic validation for all inputs
- Hot reload development mode
- Docker deployment support
- Extensive documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support and Community

### Getting Help

- **GitHub Issues**: <https://github.com/sydasif/nornir-stack/issues>
- **Discussions**: <https://github.com/sydasif/nornir-stack/discussions>
- **Documentation**: <https://github.com/sydasif/nornir-stack/wiki>

### Reporting Bugs

When reporting bugs, please include:

1. FastMCP and Python version
2. Nornir configuration (sanitized)
3. Complete error message and stack trace
4. Steps to reproduce
5. Expected vs actual behavior

### Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Describe the use case
3. Explain expected behavior
4. Provide examples if possible

## Acknowledgments

This project is built on top of these excellent libraries:

- **FastMCP** - Modern MCP server framework
- **Nornir** - Network automation framework
- **NAPALM** - Multi-vendor network abstraction
- **Netmiko** - SSH connection handling
- **Pydantic** - Data validation
- **TextFSM** - Output parsing

Special thanks to the network automation community!

## Roadmap

### Planned Features

**v1.1.0**

- Advanced filtering with boolean operators (AND/OR)
- Compliance checking tools
- Configuration templating with Jinja2
- Scheduled backup automation
- Web dashboard for monitoring

**v1.2.0**

- NetBox integration for dynamic inventory
- Ansible playbook execution
- YANG/NETCONF support
- Configuration rollback capability
- Multi-threading optimization

**v2.0.0**

- Write operations (with safety checks)
- Change management workflow
- Approval system for config changes
- Diff preview before applying
- Automatic rollback on errors

### Community Requested

Vote on features in GitHub Discussions!

## FAQ

**Q: Can this make configuration changes to devices?**
A: Currently, no. Version 1.0 is read-only by design for safety. Write operations are planned for v2.0 with extensive safety checks.

**Q: What platforms are supported?**
A: All NAPALM-supported platforms (Cisco IOS/NX-OS/XR, Arista, Juniper) and 100+ Netmiko platforms. See Configuration section for details.

**Q: How do I add support for a new vendor?**
A: If the vendor is supported by NAPALM or Netmiko, just set the correct platform string in your inventory. For unsupported vendors, you can create custom parsers.

**Q: Can I use this in production?**
A: Yes, with proper security measures. Use read-only accounts, SSH keys, audit logging, and network segmentation. Test thoroughly in lab first.

**Q: How do I handle credentials securely?**
A: Use SSH keys (preferred), environment variables, or integrate with secret management systems like HashiCorp Vault. Never hardcode credentials.

**Q: What's the performance like with hundreds of devices?**
A: Nornir's threaded runner handles parallel execution well. Adjust `num_workers` based on your environment. Use caching and connection pooling for best performance.

**Q: Can I integrate this with other tools?**
A: Yes! The FastMCP framework makes it easy to add integrations. Examples include NetBox, monitoring systems, ticketing platforms, etc.

**Q: How do I update to newer versions?**
A:

```bash
uv tool upgrade nornir-mcp
# or
pip install --upgrade git+https://github.com/sydasif/nornir-stack.git
```

**Q: Where are the logs stored?**
A: By default in `nornir.log` in the working directory. Configure via Nornir's logging settings or environment variables.

**Q: Can Claude make configuration changes?**
A: Not in v1.0. The server is read-only for safety. Configuration change capabilities with approval workflows are planned for v2.0.

---

**Version:** 1.0.0
**Last Updated:** 2025-01-10
**Author:** Syed Asif
**Repository:** <https://github.com/sydasif/nornir-stack>
**License:** MIT
