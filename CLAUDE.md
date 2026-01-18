# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Nornir MCP (Model Context Protocol) Server - a network automation server that exposes Nornir capabilities to Claude for natural language interaction with network infrastructure. It combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

## Architecture

The server follows a Service-Intent Pattern with the following structure:

- **Application Layer** (`application.py`): Initializes FastMCP and manages Nornir configuration
- **Server Entry Point** (`server.py`): Main entry point that registers tools and runs the server
- **Service Layer** (`services/runner.py`): `NornirRunner` handles standardized execution, filtering, and result formatting
- **Tool Categories** (`tools/`): Organized by intent
  - `monitoring.py`: Read-only commands (facts, interfaces, BGP, LLDP, configs, ARP/MAC tables)
  - `management.py`: State-modifying commands (config commands, backups)
  - `inventory.py`: Inventory-related operations
- **Utility Modules** (`utils/`): Filtering, formatting, and configuration utilities
- **Data Models** (`models.py`): Pydantic models for request/response handling

## Key Components

- **FastMCP**: Framework for MCP server implementation
- **Nornir**: Network automation framework
- **NAPALM**: Provides standardized network device getters across multiple vendors
- **Netmiko**: Provides SSH-based network device interaction
- **Pydantic**: Data validation and settings management

## Common Development Commands

```bash
# Install dependencies using uv
uv sync

# Run the server in development mode with hot reload
fastmcp dev src/nornir_mcp/server.py

# Run the server (config.yaml must be in current directory)
nornir-mcp

# Run linter (ruff)
uv run ruff check .
uv run ruff format .

# Run tests (if available)
uv run pytest
uv run pytest --cov=nornir_mcp

# Install as a tool
uv tool install git+https://github.com/sydasif/nornir-stack.git
```

## Development Workflow

### Adding New Tools

1. Create a new function in appropriate module (`monitoring.py`, `management.py`, or `inventory.py`)
2. Use the `@mcp.tool()` decorator
3. Include a `filters: DeviceFilters | None = None` parameter for device selection
4. Leverage the `NornirRunner` service for standardized execution:

   ```python
   from .services.runner import runner

   @mcp.tool()
   async def new_tool(filters: DeviceFilters | None = None) -> dict:
       return await runner.execute(
           task=your_nornir_task,
           filters=filters,
           # Additional parameters as needed
       )
   ```

### Filtering

All tools support device filtering via the `DeviceFilters` model with fields:

- `hostname`: Filter by specific hostname or IP
- `group`: Filter by group membership
- `platform`: Filter by platform (e.g., cisco_ios)

### Configuration

The server looks for a `config.yaml` file in the current working directory. No environment variables are required.

Additional environment variables:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Security Considerations

- Configuration backups are sandboxed to prevent path traversal
- Store network credentials securely in the inventory files (hosts.yaml, groups.yaml)
- Use read-only accounts when possible for read operations
- SSH keys preferred over passwords
