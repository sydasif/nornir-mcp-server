# Repository Guidelines

## Project Structure & Module Organization

- `src/nornir_mcp/`: application code.
- `src/nornir_mcp/tools/`: MCP tools grouped by intent (`inventory.py`, `monitoring.py`, `management.py`).
- `src/nornir_mcp/services/`: shared execution, inventory-loading, and NAPALM helpers (`runner.py`, `inventory.py`, `napalm.py`).
- `src/nornir_mcp/utils/`: shared helpers (`common.py`), filters, and command security.
- `config.yaml`: Nornir config (User provided; expected in directory when running).

## Build, Test, and Development Commands

- `uv sync`: install dependencies into the local venv.
- `nornir-mcp`: run the server using `config.yaml` in the current directory.
- `LOG_LEVEL=DEBUG nornir-mcp`: run with verbose logging.
- `fastmcp dev src/nornir_mcp/server.py`: dev server (may fail due to relative-import loading); prefer `nornir-mcp` if you hit import errors.
- `uv run ruff check . --fix` and `uv run ruff format .`: lint and format.
- `uv run pytest`: run the test suite.
- If `uv run` is unstable due to local environment state, use `.venv/bin/pytest` and `.venv/bin/ruff` directly.

## Coding Style & Naming Conventions

- Python 3.10+ with type hints.
- Format and lint with Ruff; keep imports sorted.
- Tool functions are `snake_case` and decorated with `@mcp.tool()`.
- Architectural rules (from current codebase):
  - Network task execution must go through `src/nornir_mcp/services/runner.py:runner.execute()`.
  - NAPALM getter execution should use `src/nornir_mcp/services/napalm.py:run_napalm_get()` when applicable.
  - Inventory loading and filtering should go through `src/nornir_mcp/services/inventory.py:get_filtered_nornir()`.
  - Standardized errors should use `src/nornir_mcp/utils/common.py:error_response()`.
  - CLI tools must validate commands with `src/nornir_mcp/utils/security.py:validate_command()` (or `_validate_commands()` in `management.py`).
  - Nornir initialization should come from `src/nornir_mcp/application.py:get_nornir()`.
  - Each MCP tool invocation must reload `config.yaml` and inventory from disk; do not introduce a cached shared `Nornir` instance.

## Testing Guidelines

- The repository now includes a pytest suite under `tests/`.
- Add tests with `pytest` and name files `test_*.py`.
- Keep tests focused on tool contracts, error payloads, inventory loading behavior, filtering, NAPALM helper behavior, and security validation.
- Run tests with `uv run pytest` or `.venv/bin/pytest` if `uv run` is not behaving correctly.

## Commit & Pull Request Guidelines

- Commit messages are short, imperative sentences (e.g., “Fix ruff lint issues”).
- PRs should include a concise summary, rationale, and any operational impact (e.g., config changes or new dependencies).

## Security & Configuration Tips

- Keep `config.yaml` in the repo root when running locally.
- Command validation is hardcoded in `utils/security.py` with a simple denylist for dangerous commands.
- Tool errors follow a standard shape: `{"error": true, "code": "...", "message": "...", "details": {...}}`.
- Use `NORNIR_MCP_TIMEOUT` environment variable to configure task timeout (default: 300 seconds).
- Backup output paths are restricted to the current working directory (`utils/common.py:ensure_backup_directory`).
