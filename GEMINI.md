# Gemini Context: Nornir MCP Server

This file provides architectural context, development guidelines, and operational instructions for the Nornir MCP Server project.

## Project Overview

The Nornir MCP Server is an enterprise-ready **Model Context Protocol (MCP)** server that exposes network automation capabilities to LLMs. It acts as a bridge between AI agents and network infrastructure, utilizing **Nornir** as the orchestration engine.

- **Main Technologies**: Python 3.10+, [FastMCP](https://github.com/jlowin/fastmcp), [Nornir](https://nornir.tech/), [NAPALM](https://github.com/napalm-automation/napalm), [Netmiko](https://github.com/ktbyers/netmiko), [Pydantic](https://docs.pydantic.dev/).
- **Architecture**:
  - **Application Layer**: `application.py` initializes the `FastMCP` instance and Nornir (from a local `config.yaml`).
  - **Tool Layer**: Tools in `src/nornir_mcp/tools/` are grouped by intent (Inventory, Monitoring, Management).
  - **Service Layer**: `services/runner.py` provides a centralized `NornirRunner` to execute tasks asynchronously with filtering and timeouts.
  - **Security Layer**: `utils/security.py` enforces a built-in command denylist for CLI operations.
  - **Data Models**: `models.py` defines Pydantic models for filters and inputs.

## Building and Running

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Recommended package manager)

### Installation

```bash
# Sync dependencies
uv sync
```

### Running the Server

The server requires a valid Nornir configuration (`config.yaml`) and inventory files in the working directory.

```bash
# Start the server
nornir-mcp

# Start with debug logging
LOG_LEVEL=DEBUG nornir-mcp
```

### Testing

There is currently no automated test suite. If adding tests, use `pytest`.

```bash
# Placeholder for testing
# uv run pytest
```

### Linting and Formatting

```bash
# Check for linting issues
uv run ruff check .

# Fix linting issues and format
uv run ruff check . --fix
uv run ruff format .
```

## Development Conventions

### Code Style

- **Naming**: Tool functions must be `snake_case` and decorated with `@mcp.tool()`.
- **Typing**: Strict type hints are required for all tool inputs (for Pydantic validation and MCP schema generation).
- **Formatting**: Adhere to `ruff`'s default configuration.

### Architectural Rules

- **Task Execution**: Always use `runner.execute()` from `src/nornir_mcp/services/runner.py` for network operations.
- **Filtering**: Use `apply_filters()` from `src/nornir_mcp/utils/filters.py` to target specific devices.
- **Error Handling**: Use `error_response()` from `src/nornir_mcp/utils/common.py` for standardized tool errors.
- **Command Security**: All CLI-based tools MUST call `validate_command` (or use the internal `_validate_commands` helper in `management.py`) before execution.

### Security

- **Built-in Denylist**: Command security is hardcoded in `src/nornir_mcp/utils/security.py`. It blocks destructive commands (`reload`, `erase`), keywords (`format`, `delete`), and chaining patterns (`&&`, `;`).
- **Path Sandboxing**: Backups are restricted to the current working directory to prevent directory traversal.

## Key Files

- `src/nornir_mcp/server.py`: Server entry point.
- `src/nornir_mcp/application.py`: FastMCP and Nornir initialization.
- `src/nornir_mcp/services/runner.py`: The core execution engine.
- `src/nornir_mcp/tools/`: Directory containing the MCP tools.
- `src/nornir_mcp/utils/security.py`: Command validation logic.
- `README.md`: High-level user documentation.
- `AGENTS.md`: Technical guidelines for AI development on this repo.
