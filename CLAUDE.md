# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Nornir MCP (Model Context Protocol) Server - a network automation server that exposes Nornir capabilities to Claude for natural language interaction with network infrastructure. It combines NAPALM's standardized getters with Netmiko's flexible command execution for comprehensive network management.

The server provides **11 tools** organized by technology: 6 NAPALM tools (structured data), 4 Netmiko tools (CLI operations), and 1 inventory tool.

## Functional Requirements

### Architectural Standards (MANDATORY)

All code contributions MUST follow these established architectural patterns:

#### Import Management (REQUIRED)
- **Centralized Imports**: All Nornir task imports MUST be sourced from `utils/tasks.py`
- **No Direct Imports**: Direct imports from `nornir_napalm` or `nornir_netmiko` are PROHIBITED in tool modules
- **Single Source of Truth**: `utils/tasks.py` is the authoritative location for all task imports

#### Execution Patterns (REQUIRED)  
- **NAPALM Operations**: MUST use `napalm_getter()` helper for all NAPALM data retrieval
- **Netmiko Operations**: MUST use direct `runner.execute()` for command execution
- **Inventory Operations**: MUST use `get_nr() + apply_filters()` for metadata queries
- **Domain Appropriateness**: Each operation type MUST use its designated pattern

#### Helper Functions (REQUIRED)
- **Parameter Normalization**: All tools MUST use `normalize_device_filters()` for device filtering
- **Consistent Signatures**: Helper functions MUST maintain consistent parameter patterns
- **No Code Duplication**: Common patterns MUST be abstracted into reusable helpers

#### Code Quality Standards (REQUIRED)
- **Linting Compliance**: All code MUST pass `ruff check` and `ruff format`
- **Import Sorting**: All imports MUST be auto-sorted by ruff
- **Type Safety**: Full type hints MUST be maintained where possible

## Architecture

The server follows a Service-Intent Pattern with the following structure:

- **Application Layer** (`application.py`): Initializes FastMCP and manages Nornir configuration
- **Server Entry Point** (`server.py`): Main entry point that registers tools, prompts, and resources
- **Service Layer** (`services/runner.py`): `NornirRunner` handles standardized execution, filtering, and result formatting
- **Tool Categories** (`tools/`): Organized by intent
  - `monitoring.py`: Read-only commands (facts, interfaces, BGP, LLDP, configs, ARP/MAC tables, routing tables, users, VLANs, BGP configuration, network instances)
  
  - `management.py`: State-modifying commands (config commands, backups, file transfers)
  - `inventory.py`: Inventory-related operations
- **Validation Layer** (`utils/validation_helpers.py`): Comprehensive input validation with helpful error messages
- **Security Layer** (`utils/security.py`): Command validation with configurable blacklists
- **MCP Ecosystem** (`prompts.py`, `resources.py`): Enhanced Claude integration with troubleshooting workflows and topology data
- **Utility Modules** (`utils/`): Filtering, formatting, security, and configuration utilities
- **Data Models** (`models.py`): Pydantic models for request/response handling

## Key Components

- **FastMCP**: Framework for MCP server implementation
- **Nornir**: Network automation framework
- **NAPALM**: Provides standardized network device getters across multiple vendors
- **Netmiko**: Provides SSH-based network device interaction
- **Pydantic**: Data validation and settings management
- **Command Validation**: Configurable security blacklists for dangerous commands

## Common Development Commands

```bash
# Install dependencies using uv
uv sync

# Run the server in development mode with hot reload
fastmcp dev src/nornir_mcp/server.py

# Run the server (config.yaml must be in current directory)
nornir-mcp

# Run with Docker
docker-compose up --build

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

### Adding New Tools (MUST Follow Architectural Standards)

1. Create a new function in appropriate module (`monitoring.py`, `management.py`, or `inventory.py`)
2. **MANDATORY**: Import tasks from `utils/tasks.py` (not direct Nornir imports)
3. **MANDATORY**: Use the `@mcp.tool()` decorator with standard `filters: DeviceFilters | None = None` parameter
4. **MANDATORY**: Follow domain-appropriate execution patterns:
   
   **For NAPALM operations:**
   ```python
   from ..utils.helpers import napalm_getter
   
   @mcp.tool()
   async def new_napalm_tool(filters: DeviceFilters | None = None) -> dict:
       return await napalm_getter(getters=["some_data"], filters=filters)
   ```
   
   **For Netmiko operations:**
   ```python
   from ..utils.tasks import netmiko_send_command
   from ..services.runner import runner
   
   @mcp.tool()
   async def new_netmiko_tool(filters: DeviceFilters | None = None) -> dict:
       return await runner.execute(task=netmiko_send_command, filters=filters, command_string="show something")
   ```
   
   **For Inventory operations:**
   ```python
   from ..application import get_nr
   from ..utils.filters import apply_filters
   
   @mcp.tool()
   async def new_inventory_tool(filters: DeviceFilters | None = None) -> dict:
       nr = get_nr()
       if filters:
           nr = apply_filters(nr, filters)
       # process inventory data
   ```

5. **MANDATORY**: Add tests and ensure `ruff check` + `ruff format` compliance

### Adding Validation Models

1. Add Pydantic models to `src/nornir_mcp/models.py`
2. Register models in `MODEL_MAP` in `utils/validation_helpers.py`
3. Models are automatically available through the `validate_params` tool

### Adding Prompts

1. Add prompt functions to `src/nornir_mcp/prompts.py` with names starting with `prompt_`
2. Prompts are automatically registered when the server starts

### Adding Resources

1. Add resource functions to `src/nornir_mcp/resources.py` with names starting with `resource_`
2. Resources are automatically registered when the server starts

### Filtering

All tools support device filtering via the `DeviceFilters` model with fields:

- `hostname`: Filter by specific hostname or IP
- `group`: Filter by group membership
- `platform`: Filter by platform (e.g., cisco_ios)

### Configuration

The server looks for a `config.yaml` file in the current working directory. No environment variables are required.

Example configuration files are available in `examples/conf/` for quick setup.

Additional environment variables:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Security Considerations

- Configuration backups are sandboxed to prevent path traversal
- Store network credentials securely in the inventory files (hosts.yaml, groups.yaml)
- Use read-only accounts when possible for read operations
- SSH keys preferred over passwords
- Command validation with configurable blacklists prevents dangerous operations
- Input validation ensures all parameters are properly validated before execution
- Sensitive data sanitization removes passwords and secrets from resource outputs

## Architecture Improvements (MANDATORY PATTERNS)

### Import Centralization (REQUIRED)
- ✅ **IMPLEMENTED**: Centralized Nornir task imports in `utils/tasks.py`
- ✅ **ENFORCED**: All tool modules MUST import from this centralized location
- ✅ **MAINTAINED**: Direct Nornir imports are PROHIBITED in tool modules
- **BENEFIT**: Simplifies Nornir version upgrades and reduces import scattering

### Helper Functions (REQUIRED)
- ✅ **IMPLEMENTED**: Reusable helper functions in `utils/helpers.py`:
  - `normalize_device_filters()`: **MANDATORY** for device filter normalization
  - `napalm_getter()`: **MANDATORY** for NAPALM getter execution
- ✅ **ENFORCED**: These helpers MUST be used for their respective domains
- **BENEFIT**: Consistent patterns without unnecessary abstraction layers

### Tool Design Patterns (MANDATORY)
- **NAPALM operations**: **MUST** use `napalm_getter()` helper for structured data retrieval
- **Netmiko operations**: **MUST** use direct `runner.execute()` for command execution (appropriate for the domain)
- **Inventory operations**: **MUST** use direct `get_nr() + apply_filters()` (appropriate for metadata queries)
- **ENFORCEMENT**: New tools MUST follow these established patterns
