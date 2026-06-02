# Repository Guidelines

## Core Architecture

- **Tooling Engine**: `src/nornir_mcp/services/runner.py:execute()` is mandatory for all network tasks. Accepts filter kwargs (`name`, `hostname`, `group`, `platform`).
- **Inventory/Filter**: Use `src/nornir_mcp/services/inventory.py:get_filtered_nornir()` for inventory access. Reloads `config.yaml` from disk on EVERY tool call; do not cache `Nornir` instances. Accepts filter kwargs directly.
- **NAPALM**: Route getter requests through `src/nornir_mcp/services/napalm.py:run_napalm_get()`. Accepts filter kwargs directly.
- **CLI Security**: All shell commands must pass `src/nornir_mcp/utils/security.py:validate_command()`.

## Development & Workflow

- **Dependency/Env**: `uv` is the primary manager. Use `uv sync` to init.
- **Verification**: Run `uv run ruff check . --fix && uv run ruff format .` then `uv run pytest`.
- **If `uv` fails**: Fallback to `.venv/bin/` direct execution (e.g., `.venv/bin/pytest`).
- **Entrypoint**: `nornir-mcp` (requires `config.yaml` in current working directory).

## Conventions

- **Naming**: `snake_case` tools, `@mcp.tool()` decoration.
- **Errors**: Return standardized dict via `src/nornir_mcp/utils/common.py:error_response()`.
- **Filters**: Pass individual kwargs (`name`, `hostname`, `group`, `platform`) to services. No `DeviceFilters` wrapper.
- **Commit**: Short, imperative messages.

## Operational Gotchas

- **Config**: `config.yaml` is NOT bundled; user must provide it in the run directory.
- **Timeout**: Adjust via `NORNIR_MCP_TIMEOUT` (default: 300s).
- **Security**: Hardcoded denylist in `utils/security.py` prevents destructive commands (`erase`, `format`, `delete`, etc.).
