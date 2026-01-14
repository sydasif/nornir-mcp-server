This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.claude/
  settings.local.json
examples/
  inventory/
    defaults.yaml
    groups.yaml
    hosts.yaml
  config.yaml
src/
  nornir_mcp/
    services/
      runner.py
    tools/
      __init__.py
      configuration.py
      inventory.py
      operational.py
    utils/
      __init__.py
      config.py
      filters.py
      formatters.py
    __init__.py
    application.py
    models.py
    server.py
.gitignore
.python-version
pyproject.toml
README.md
```

# Files

## File: .claude/settings.local.json
````json
{
  "permissions": {
    "allow": [
      "mcp__context7__resolve-library-id",
      "mcp__context7__query-docs"
    ]
  }
}
````

## File: examples/inventory/defaults.yaml
````yaml
---
username: ${NETWORK_USER}
password: ${NETWORK_PASS}

connection_options:
  napalm:
    extras:
      timeout: 30
  netmiko:
    extras:
      timeout: 30
      session_timeout: 60
      auth_timeout: 30
````

## File: examples/inventory/groups.yaml
````yaml
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
````

## File: examples/inventory/hosts.yaml
````yaml
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
````

## File: examples/config.yaml
````yaml
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
````

## File: .gitignore
````
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# Log files
*.log

# Environment files
.env

# IDE-specific files
.vscode/
.idea/

# Dependency directories
node_modules/

# Coverage reports
htmlcov/
.coverage
````

## File: .python-version
````
3.11
````

## File: src/nornir_mcp/services/runner.py
````python
"""Nornir Execution Service."""

import asyncio
from collections.abc import Callable
from typing import Any

from nornir.core.task import Result

from ..application import get_nr
from ..models import DeviceFilters
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


class NornirRunner:
    """Orchestrates Nornir task execution."""

    async def execute(
        self,
        task: Callable[..., Result],
        filters: DeviceFilters | None = None,
        **task_kwargs: Any,
    ) -> dict:
        """
        Execute a Nornir task and return raw results.

        1. Gets fresh Nornir instance
        2. Applies Filters
        3. Offloads blocking task to thread
        4. Returns raw results dictionary
        """
        # 1. Setup & Filter
        nr = get_nr()
        if filters is None:
            filters = DeviceFilters()

        try:
            nr = apply_filters(nr, filters)
        except ValueError as e:
            return {"error": str(e)}

        # 2. Execute in Thread (Non-blocking)
        result = await asyncio.to_thread(nr.run, task=task, **task_kwargs)

        # 3. Standardize Output (Simple extraction)
        return format_results(result)


# Singleton instance for easy import
runner = NornirRunner()
````

## File: src/nornir_mcp/application.py
````python
"""Nornir MCP Application Context - Shared application components."""

import logging
import os
from pathlib import Path

from fastmcp import FastMCP
from nornir import InitNornir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(".mcp.log"), logging.StreamHandler()],
)

logger = logging.getLogger("nornir-mcp")

# Initialize FastMCP with metadata
mcp = FastMCP("Nornir Network Automation")


# Initialize Nornir from config
def get_nornir():
    """Initialize and return a Nornir instance from configuration file.

    Returns:
        Nornir: A configured Nornir instance.

    Raises:
        ValueError: If no configuration file is found.
    """
    config_file = os.getenv("NORNIR_CONFIG_FILE")
    if not config_file:
        # Try local config.yaml
        config_file = Path.cwd() / "config.yaml"
        if not config_file.exists():
            raise ValueError(
                "No Nornir config found. Set NORNIR_CONFIG_FILE or create config.yaml in current directory",
            )

    return InitNornir(config_file=str(config_file))


def get_nr():
    """Get a fresh Nornir instance for each request.

    Returns:
        Nornir: A fresh Nornir instance for each call.

    This function creates a new Nornir instance for each request,
    ensuring complete state isolation between tool calls.
    """
    return get_nornir()
````

## File: src/nornir_mcp/utils/__init__.py
````python
"""Nornir MCP Server utilities package.

This module contains utility functions for:
- Configuration processing and backup functionality
- Data formatting and result processing
- Device filtering and inventory management
"""
````

## File: src/nornir_mcp/__init__.py
````python
"""Nornir MCP Server - Network Automation Server.

This package provides a Model Context Protocol (MCP) server that exposes Nornir automation
capabilities to Claude, enabling natural language interaction with network infrastructure.
The server combines NAPALM's standardized getters with Netmiko's flexible command execution
for comprehensive network management.
"""
````

## File: pyproject.toml
````toml
[project]
name = "nornir-mcp-server"
version = "0.1.0"
description = "Nornir MCP Server for Network Engineering"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.2.0",
    "nornir>=3.4.0",
    "nornir-napalm>=0.4.0",
    "nornir-netmiko>=1.0.0",
    "napalm>=4.1.0",
    "netmiko>=4.3.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]

[project.scripts]
nornir-mcp = "nornir_mcp.server:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[dependency-groups]
dev = ["ruff>=0.14.11"]
````

## File: src/nornir_mcp/tools/__init__.py
````python
"""Nornir MCP Server tools package.

This module contains the core MCP tools for network automation:
- Inventory tools: Device listing and group management
- Operational tools: Read-only commands for network devices
- Configuration tools: Tools that modify device state
"""
````

## File: src/nornir_mcp/tools/configuration.py
````python
"""Configuration Tools - Tools that modify device state."""

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_config

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.config import ensure_backup_directory, write_config_to_file


@mcp.tool()
async def send_config_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Send configuration commands to network devices.

    Args:
        commands: List of configuration commands
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw output from the configuration execution per host.
    """
    if not commands:
        raise ValueError("Command list cannot be empty")

    return await runner.execute(
        task=netmiko_send_config,
        filters=filters,
        config_commands=commands,
    )


@mcp.tool()
async def backup_device_configs(
    filters: DeviceFilters | None = None,
    path: str = "./backups",
) -> dict:
    """Save device configuration to the local disk.

    Args:
        filters: DeviceFilters object containing filter criteria
        path: Directory path to save backup files

    Returns:
        Summary of saved file paths.
    """
    # 1. Get configurations (Raw NAPALM structure: {'config': {'running': '...'}})
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": "running"}},
    )

    backup_path = ensure_backup_directory(path)
    backup_results = {}

    for hostname, data in result.items():
        # Check if the host execution failed (data would be an error dict or missing keys)
        if isinstance(data, dict) and "config" in data:
            # Extract config content from raw NAPALM structure
            config_content = data["config"].get("running", "")

            if config_content:
                file_path = write_config_to_file(hostname, config_content, backup_path)
                backup_results[hostname] = {
                    "status": "success",
                    "path": file_path,
                }
            else:
                backup_results[hostname] = {
                    "status": "warning",
                    "message": "Empty configuration content",
                }
        else:
            # Propagate error info found in data
            backup_results[hostname] = {"status": "failed", "details": data}

    return backup_results
````

## File: src/nornir_mcp/utils/config.py
````python
"""Configuration retrieval and backup utilities."""

from datetime import datetime
from pathlib import Path


def ensure_backup_directory(backup_dir: str) -> Path:
    """Create backup directory if it doesn't exist.

    Args:
        backup_dir: Path to the backup directory to create

    Returns:
        Path object pointing to the backup directory

    Raises:
        ValueError: If the backup directory path attempts to traverse outside the safe root
    """
    # 1. Resolve absolute paths
    target_path = Path(backup_dir).resolve()
    # 2. Define strict root (e.g., current directory)
    root_path = Path.cwd().resolve()

    # 3. Check if target is within root
    if not target_path.is_relative_to(root_path):
        raise ValueError(f"Security Error: Backup directory must be within {root_path}")

    target_path.mkdir(parents=True, exist_ok=True)
    return target_path


def write_config_to_file(hostname: str, content: str, folder: Path) -> str:
    """Write configuration content to a file.

    Args:
        hostname: Device hostname for filename
        content: Configuration content to write
        folder: Directory path to write the file to

    Returns:
        Path to the written file as a string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{hostname}_{timestamp}.cfg"
    filepath = folder / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return str(filepath)
````

## File: src/nornir_mcp/utils/formatters.py
````python
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
````

## File: src/nornir_mcp/tools/operational.py
````python
"""Operational Tools - Read-only commands for network devices."""

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner

# --- Tools ---


@mcp.tool()
async def get_device_facts(filters: DeviceFilters | None = None) -> dict:
    """Retrieve basic device information (Vendor, OS, Uptime).

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM facts dictionary per host.
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["facts"],
    )


@mcp.tool()
async def get_interfaces_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve raw interface statistics and IP addresses.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM interface data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["interfaces", "interfaces_ip"],
    )

    # Minimal filtering only to reduce token usage if specific interface requested
    if interface:
        for _host, data in result.items():
            # Skip failed hosts or unexpected structures
            if not isinstance(data, dict):
                continue

            # Filter 'interfaces' key
            if "interfaces" in data and isinstance(data["interfaces"], dict):
                if interface in data["interfaces"]:
                    data["interfaces"] = {interface: data["interfaces"][interface]}
                else:
                    data["interfaces"] = {}

            # Filter 'interfaces_ip' key
            if "interfaces_ip" in data and isinstance(data["interfaces_ip"], dict):
                if interface in data["interfaces_ip"]:
                    data["interfaces_ip"] = {
                        interface: data["interfaces_ip"][interface]
                    }
                else:
                    data["interfaces_ip"] = {}

    return result


@mcp.tool()
async def get_lldp_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return raw LLDP neighbors information.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM LLDP data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["lldp_neighbors", "lldp_neighbors_detail"],
    )

    if interface:
        for _host, data in result.items():
            if not isinstance(data, dict):
                continue

            if "lldp_neighbors" in data and isinstance(data["lldp_neighbors"], dict):
                if interface in data["lldp_neighbors"]:
                    data["lldp_neighbors"] = {
                        interface: data["lldp_neighbors"][interface]
                    }
                else:
                    data["lldp_neighbors"] = {}

            if "lldp_neighbors_detail" in data and isinstance(
                data["lldp_neighbors_detail"], dict
            ):
                if interface in data["lldp_neighbors_detail"]:
                    data["lldp_neighbors_detail"] = {
                        interface: data["lldp_neighbors_detail"][interface]
                    }
                else:
                    data["lldp_neighbors_detail"] = {}

    return result


@mcp.tool()
async def get_device_configs(
    filters: DeviceFilters | None = None,
    source: str = "running",
) -> dict:
    """Retrieve raw device configuration data.

    Args:
        filters: DeviceFilters object containing filter criteria
        source: Configuration source (running, startup, candidate)

    Returns:
        Raw NAPALM config dictionary per host.
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": source}},
    )


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Execute raw CLI show commands via SSH.

    Args:
        commands: List of show commands to execute
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary mapping command -> host -> raw output
    """

    results = {}
    for cmd in commands:
        results[cmd] = await runner.execute(
            task=netmiko_send_command,
            filters=filters,
            command_string=cmd,
        )
    return results


@mcp.tool()
async def get_bgp_detailed(
    neighbor: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return raw BGP neighbor information.

    Args:
        neighbor: Optional specific neighbor IP to filter results
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM BGP data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["bgp_neighbors", "bgp_neighbors_detail"],
    )

    if neighbor:
        for _host, data in result.items():
            if not isinstance(data, dict):
                continue

            if "bgp_neighbors" in data and isinstance(data["bgp_neighbors"], dict):
                if neighbor in data["bgp_neighbors"]:
                    data["bgp_neighbors"] = {neighbor: data["bgp_neighbors"][neighbor]}
                else:
                    data["bgp_neighbors"] = {}

            if "bgp_neighbors_detail" in data and isinstance(
                data["bgp_neighbors_detail"], dict
            ):
                if neighbor in data["bgp_neighbors_detail"]:
                    data["bgp_neighbors_detail"] = {
                        neighbor: data["bgp_neighbors_detail"][neighbor]
                    }
                else:
                    data["bgp_neighbors_detail"] = {}

    return result
````

## File: src/nornir_mcp/models.py
````python
"""Nornir MCP Server data models."""

import json
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DeviceFilters(BaseModel):
    """Filter parameters for device selection."""

    hostname: str | None = Field(None, description="Filter by specific hostname or IP")
    group: str | None = Field(None, description="Filter by group membership")
    platform: str | None = Field(
        None, description="Filter by platform (e.g., cisco_ios)"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value: Any) -> Any:
        """Parse JSON string if provided."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
````

## File: src/nornir_mcp/utils/filters.py
````python
"""Nornir MCP Server device filtering utilities.

Contains functions to apply filters to Nornir inventory using the F object.
"""

from nornir.core import Nornir
from nornir.core.filter import F

from ..models import DeviceFilters


def apply_filters(nr: Nornir, filters: DeviceFilters) -> Nornir:
    """Apply filters to Nornir inventory using the F object.

    If no filters are provided, returns the unfiltered Nornir instance,
    which targets all hosts in the inventory (Nornir's default behavior).

    Args:
        nr: Nornir instance to filter
        filters: DeviceFilters object containing filter criteria

    Returns:
        Filtered Nornir instance (or unfiltered if no filters provided)

    Raises:
        ValueError: If filters result in zero matching hosts
    """
    original_count = len(nr.inventory.hosts)

    # If no filters provided, return unfiltered (all hosts)
    if not any([filters.hostname, filters.group, filters.platform]):
        return nr

    # Apply filters based on the DeviceFilters object
    if filters.hostname:
        nr = nr.filter(F(name=filters.hostname) | F(hostname=filters.hostname))

    if filters.group:
        nr = nr.filter(F(groups__contains=filters.group))

    if filters.platform:
        nr = nr.filter(F(platform=filters.platform))

    # Validate that filters matched at least one host
    if len(nr.inventory.hosts) == 0:
        raise ValueError(
            f"No devices matched the provided filters. "
            f"Original inventory: {original_count} devices. "
            f"Filters applied: {filters.model_dump(exclude_none=True)}"
        )

    return nr
````

## File: src/nornir_mcp/tools/inventory.py
````python
"""Nornir MCP Server inventory tools."""

from ..application import get_nr, mcp
from ..models import DeviceFilters
from ..utils.filters import apply_filters


@mcp.tool()
async def list_devices(
    details: bool = False,
    filters: DeviceFilters | None = None,
) -> dict:
    """Query network inventory with optional filters.

    Returns device names, IPs, platforms, and groups.
    Use 'details=true' for full inventory attributes.

    If no filters are provided, returns all devices in the inventory.

    Args:
        details: Whether to return full inventory attributes
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing device inventory information
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    devices = []
    for host_name, host in nr.inventory.hosts.items():
        device_info = {
            "name": host_name,
            "hostname": host.hostname,
            "platform": host.platform,
            "groups": [g.name for g in host.groups],
        }

        if details:
            device_info["data"] = host.data

        devices.append(device_info)

    return {"total_devices": len(devices), "devices": devices}


@mcp.tool()
async def list_device_groups() -> dict:
    """List all inventory groups and their member counts.

    Useful for discovering available device groupings like roles,
    sites, or device types.

    Returns:
        Dictionary containing all inventory groups and their member counts
    """
    nr = get_nr()
    groups = {name: {"count": 0, "members": []} for name in nr.inventory.groups}

    for host_name, host in nr.inventory.hosts.items():
        for group in host.groups:
            if group.name in groups:
                groups[group.name]["count"] += 1
                groups[group.name]["members"].append(host_name)

    return {"groups": groups}
````

## File: README.md
````markdown
# Nornir MCP Server

An MCP (Model Context Protocol) server built with **FastMCP** that exposes Nornir automation capabilities to Claude, enabling natural language interaction with network infrastructure. This server combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

## Features

- **Network Inventory Tools**: List devices, query groups, filter by attributes
- **Operational Tools**: Read-only commands for network state retrieval (facts, interfaces with IP addresses, BGP, LLDP, configs)
- **Configuration Tools**: State-modifying commands for network device management
- **Service-Intent Architecture**: Clean separation between operational (read) and configuration (write) operations
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

### Configuration Tools (State-Modifying Commands)

- `send_config_commands`: Send configuration commands to network devices via SSH (modifies device configuration)
- `backup_device_configs`: Save device configuration to local disk

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

1. Create a new module in `src/nornir_mcp/tools/` or add to existing modules:
   - `operational.py` for read-only commands
   - `configuration.py` for state-modifying commands
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
````

## File: src/nornir_mcp/server.py
````python
"""Nornir MCP Server - Network Automation Server."""

from .application import mcp

# Import the new intent-based modules
from .tools import configuration, inventory, operational  # noqa: F401


def main():
    """Entry point for FastMCP."""
    mcp.run()


# Entry point for FastMCP
if __name__ == "__main__":
    mcp.run()
````
