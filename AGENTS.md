# Repository Guidelines

## Project Structure & Module Organization

- `src/nornir_mcp/`: application code.
- `src/nornir_mcp/tools/`: MCP tools grouped by intent (`inventory.py`, `monitoring.py`, `management.py`).
- `src/nornir_mcp/utils/`: helpers, validation, filters, security, config, and tasks.
- `examples/conf/`: sample Nornir inventory files.
- `config.yaml`: Nornir config (expected in repo root when running locally).

## Build, Test, and Development Commands

- `uv sync`: install dependencies into the local venv.
- `nornir-mcp`: run the server using `config.yaml` in the current directory.
- `LOG_LEVEL=DEBUG nornir-mcp`: run with verbose logging.
- `fastmcp dev src/nornir_mcp/server.py`: dev server (may fail due to relative-import loading); prefer `nornir-mcp` if you hit import errors.
- `docker compose up --build`: run via Docker.
- `uv run ruff check .` and `uv run ruff format .`: lint and format.

## Coding Style & Naming Conventions

- Python 3.10+ with type hints.
- Format and lint with Ruff; keep imports sorted.
- Tool functions are `snake_case` and decorated with `@mcp.tool()`.
- Architectural rules (from `CLAUDE.md`):
  - NAPALM data retrieval must use `utils/helpers.py:napalm_getter()`.
  - Netmiko operations must use `services/runner.py:runner.execute()`.
  - Inventory operations must use `application.get_nr()` + `utils/filters.apply_filters()`.
  - Task imports must come from `utils/tasks.py` (no direct `nornir_*` task imports in tools).

## Testing Guidelines

- No test suite is currently present. If you add tests, use `pytest` and name files `test_*.py`. Add a `uv run pytest` command to this section when tests exist.

## Commit & Pull Request Guidelines

- Commit messages are short, imperative sentences (e.g., “Fix ruff lint issues”).
- PRs should include a concise summary, rationale, and any operational impact (e.g., config changes or new dependencies).

## Security & Configuration Tips

- Keep `config.yaml` in the repo root when running locally.
- Use `examples/conf/*` as a starting point for inventory.
- `conf/blacklist.yaml` controls command validation for Netmiko tools; keep it restricted for safety.
- Tool errors follow a standard shape: `{"error": true, "code": "...", "message": "...", "details": {...}}`.
