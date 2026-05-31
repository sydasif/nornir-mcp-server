# Nornir MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-orange.svg)](https://modelcontextprotocol.io)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

An enterprise-ready **Model Context Protocol (MCP)** server that brings the power of [Nornir](https://nornir.tech/) to LLMs like Claude. It seamlessly integrates [NAPALM](https://github.com/napalm-automation/napalm) for structured data retrieval and [Netmiko](https://github.com/ktbyers/netmiko) for flexible CLI execution, enabling natural language orchestration of complex network infrastructure.

---

## 🚀 Overview

The Nornir MCP Server provides a specialized set of tools for network engineers and AI agents to interact with multi-vendor environments safely and efficiently.

- **Multi-Vendor Support**: Standardized interaction for Cisco (IOS, NX-OS, XR), Arista (EOS), Juniper (Junos), and 100+ others.
- **Dual-Engine Architecture**: Combines NAPALM's normalized getters with Netmiko's robust SSH command execution.
- **Intelligent Filtering**: Schema-agnostic device selection by hostname, group, or platform.
- **Security First**: Built-in command blacklisting, input validation (Pydantic), and backup path restrictions.
- **Per-Call Inventory Reloading**: Every MCP tool invocation reloads `config.yaml` and inventory data from disk.
- **Production Ready**: Comprehensive logging and asynchronous execution.

---

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Available Tools](#-available-tools)
- [Configuration](#-configuration)
- [Claude Integration](#-claude-integration)
- [Security](#-security)
- [Development](#-development)
- [Testing](#-testing)

---

## 🛠 Installation

### Using `uv` (Recommended)

```bash
# Install as a global tool
uv tool install git+https://github.com/sydasif/nornir-mcp-server.git

# Upgrade to latest
uv tool upgrade nornir-mcp-server
```

### Using `pip`

```bash
pip install git+https://github.com/sydasif/nornir-mcp-server.git
```

---

## ⚡ Quick Start

1.  **Initialize Configuration**:

    Create a `config.yaml` and basic inventory files in your working directory. See [Minimal Inventory Example](#-minimal-inventory-example) below.

2.  **Launch the Server**:

    ```bash

    nornir-mcp

    ```

3.  **Verify Inventory**:

    The server will look for `config.yaml` in the current directory to load your Nornir inventory.

---

## 📦 Minimal Inventory Example

To get started quickly, create these three files in your project root:

**`hosts.yaml`**

```yaml
R1:
  hostname: 192.168.1.1
  platform: ios
  groups:
    - cisco_ios
```

**`groups.yaml`**

```yaml
cisco_ios:
  platform: ios
  username: admin
  password: password
```

**`defaults.yaml`**

```yaml
# Global defaults
data:
  site: NYC
```

**`config.yaml`**

```yaml
inventory:
  plugin: SimpleInventory
  options:
    host_file: "hosts.yaml"
    group_file: "groups.yaml"
    defaults_file: "defaults.yaml"
```

---

## 🧰 Available Tools

The server exposes 5 tools categorized by operational intent. All tools support individual filter parameters for device selection.

**Filter Parameters:**

- `filter_name`: Filter by device name in inventory
- `filter_hostname`: Filter by specific hostname or IP address
- `filter_group`: Filter by group membership (e.g., "cisco", "arista")
- `filter_platform`: Filter by platform (e.g., "eos", "ios", "junos")

All filter parameters are optional. When multiple filters are provided, they are combined with AND logic.

| Category       | Tool                    | Description                                            |
| :------------- | :---------------------- | :----------------------------------------------------- |
| **Inventory**  | `list_network_devices`  | List hosts, groups, and metadata.                      |
| **Monitoring** | `get_structured_data`   | Generic access to any NAPALM getter (ARP, VLAN, etc.). |
| **Management** | `run_show_commands`     | Execute arbitrary show commands safely.                |
|                | `send_config_commands`  | Deploy configuration changes with validation.          |
|                | `backup_device_configs` | Securely save configurations to local disk.            |

---

## ⚙️ Configuration

Every MCP tool call reloads `config.yaml` from the current working directory. The server does not cache a long-lived `Nornir` instance between requests.

### Nornir Setup (`config.yaml`)

```yaml
inventory:
  plugin: SimpleInventory
  options:
    host_file: "hosts.yaml"
    group_file: "groups.yaml"
    defaults_file: "defaults.yaml"

runner:
  plugin: threaded
  options:
    num_workers: 100

logging:
  enabled: true
  level: INFO
```

### Command Security

The server includes a built-in security engine that validates all CLI commands against a multi-stage validation system before execution. This prevents accidental or malicious use of destructive commands while minimizing false positives for read-only operations.

**Security Features:**

- **Read-Only Enforcement**: Tools like `run_show_commands` enforce an **allowlist prefix** (e.g., `show`, `display`, `get`, `ping`, `traceroute`).
- **Smart Denylist**: Destructive keywords (`erase`, `format`, `delete`, `reload`) are blocked only when they appear as the **first token** of a command. This allows legitimate commands like `show reload history` while blocking a bare `reload`.
- **Chaining & Redirection Protection**: Prevents the use of `;`, `&&`, `>`, and `<` to ensure single-command integrity.
- **Path Sandboxing**: Configuration backups are protected against directory traversal attacks (`..`).

---

## 🤖 CLI Integration

Add the following to your claude config:

```json
{
  "mcpServers": {
    "nornir": {
      "command": "nornir-mcp"
    }
  }
}
```

Add the following to your opencode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "nornir": {
      "type": "local",
      "command": ["nornir-mcp"]
    }
  }
}
```

**Try these prompts:**

- _"Show me all core routers in the US-West region."_
- _"Are there any BGP neighbors down on R1?"_
- _"Backup the running configuration of all Arista switches."_
- _"Check if there are any errors on the interfaces of the edge-group."_

---

## 🔒 Security

- **Command Validation**: All CLI inputs pass through a multi-stage built-in denylist filter (Keywords and Patterns).
- **Credential Management**: Supports environment variables and Nornir's native secure handling.
- **Path Sandboxing**: Configuration backups are restricted to the defined root directory to prevent traversal.

---

## 👨‍💻 Development

```bash
# Clone and setup
git clone https://github.com/sydasif/nornir-mcp-server.git
cd nornir-mcp-server
uv sync

# Run tests
uv run pytest

# Lint and Format
uv run ruff check . --fix
uv run ruff format .
```

If `uv run` is unstable in the local environment, use `.venv/bin/pytest` and `.venv/bin/ruff` directly.

Relevant internal paths:

- `src/nornir_mcp/services/runner.py`: shared task execution.
- `src/nornir_mcp/services/inventory.py`: shared inventory loading and filtering helper. This helper still reloads inventory from disk on every call.
- `src/nornir_mcp/services/napalm.py`: shared NAPALM getter execution helper used by monitoring and backup tools.
- `src/nornir_mcp/tools/monitoring.py`: monitoring tools for generic getters.

---

## ✅ Testing

The repository includes a pytest suite under `tests/` covering filters, inventory loading, inventory tools, monitoring tools, NAPALM helper behavior, security validation, runner error handling, and backup behavior.

```bash
# Run the full test suite
uv run pytest

# Fallback if uv run is unstable
.venv/bin/pytest
```

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<p align="center">Built with ❤️ for Network Automation</p>
