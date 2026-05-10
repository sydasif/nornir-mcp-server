# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Testing
- Run all tests: `uv run pytest`
- Run specific test file: `uv run pytest tests/test_inventory.py`
- Run with coverage: `uv run pytest --cov=src --cov-branch --cov-fail-under=90`

### Linting & Formatting
- Lint and auto-fix: `uv run ruff check --fix .`
- Format code: `uv run ruff format .`

## Architecture

This is a Python-based Model Context Protocol (MCP) server for integrating Nornir/Network Automation into LLMs.

- **Entry Point:** `src/nornir_mcp/server.py` defines the MCP server and registers tools.
- **Tools (`src/nornir_mcp/tools/`)**: MCP tool definitions that wrap backend services.
- **Services (`src/nornir_mcp/services/`)**: Core automation logic utilizing `Nornir` for task execution, `Napalm` for data retrieval, and `Netmiko` for command execution.
- **Models (`src/nornir_mcp/models.py`)**: Pydantic models for request/response validation.
- **Utils (`src/nornir_mcp/utils/`)**: Helpers for Nornir filtering, security validation, and common automation tasks.
