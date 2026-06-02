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
- **Tools (`src/nornir_mcp/tools/`)**: MCP tool definitions that wrap backend services. Tools call `runner.execute()` directly with Nornir task functions and pass filter kwargs (`name`, `hostname`, `group`, `platform`).
- **Services (`src/nornir_mcp/services/`)**: Core automation logic.
  - `runner.py`: shared async task execution with timeout handling. Mandatory entry point for all network tasks.
  - `inventory.py`: loads Nornir from `config.yaml` on every call and applies optional filter kwargs.
  - `napalm.py`: thin wrapper that calls `execute()` with `napalm_get` task and forwards filter kwargs.
- **Models (`src/nornir_mcp/models.py`)**: Minimal Pydantic models for response standardization (`ErrorResponse`, `HostTaskResult`, `TaskResult`).
- **Utils (`src/nornir_mcp/utils/`)**: Helpers for Nornir filtering, security validation, error responses, and file backup operations.
