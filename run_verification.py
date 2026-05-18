#!/usr/bin/env python3
"""Run verification commands and report results."""

import subprocess


def run_cmd(cmd, desc):
    print(f"\n{'=' * 60}")
    print(f"{desc}")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/home/zulu/Documents/nornir-mcp-server",
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print(f"Return code: {result.returncode}")
    return result.returncode == 0


# Run ruff check and format
run_cmd(["uv", "run", "ruff", "check", ".", "--fix"], "Ruff lint check (fix)")
run_cmd(["uv", "run", "ruff", "format", "."], "Ruff format")

# Run tests with coverage
run_cmd(
    ["uv", "run", "pytest", "--cov=src", "--cov-branch", "-v"], "Pytest with coverage"
)

# Show git diff
print("\n" + "=" * 60)
print("Git Diff")
print("=" * 60)
result = subprocess.run(
    ["git", "diff"],
    capture_output=True,
    text=True,
    cwd="/home/zulu/Documents/nornir-mcp-server",
)
print(result.stdout)
