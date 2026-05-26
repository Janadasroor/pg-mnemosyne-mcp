# Pg-Mnemosyne MCP

[![PyPI version](https://img.shields.io/pypi/v/pg-mnemosyne-mcp.svg)](https://pypi.org/project/pg-mnemosyne-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](pyproject.toml)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io)
[![Platform Support](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)](#setup)

<p align="center">
  <img src="https://raw.githubusercontent.com/Janadasroor/pg-mnemosyne-mcp/main/assets/mcp_power_banner.png" alt="Pg-Mnemosyne MCP Power Banner" width="100%">
</p>

A Model Context Protocol (MCP) server that provides AI assistants with a robust "super memory", task tracker, and dynamic PostgreSQL database management capabilities.

## ⚡ Quick Start

1. **Install the package globally:**
   * **Windows**:
     ```cmd
     pip install pg-mnemosyne-mcp
     ```
   * **macOS / Linux**:
     ```bash
     pipx install pg-mnemosyne-mcp
     ```
     *(If you prefer standard pip or don't have `pipx`, run: `pip install pg-mnemosyne-mcp --break-system-packages`)*

2. **Auto-configure all your AI agents (Claude, Gemini, Qwen, Cursor, etc.) at once:**
   ```bash
   pg-mnemosyne init --dsn "postgresql://user:password@localhost:5432/postgres"
   ```
   *(Be sure to replace `user` and `password` with your actual PostgreSQL username and database password!)*

3. **Restart your AI agents.** You're done!


---

## Features
- **High-Performance**: Uses cached connection pooling (`asyncpg.create_pool`) for instant sub-millisecond database queries.
- **Dynamic Projects**: The AI can create new databases for different projects on the fly.
- **Dynamic Schema**: The AI can modify table schemas dynamically to adapt to changing memory needs.
- **Standard Memory Tracker**: Built-in support for tracking, updating, and deleting memory items with tags.
- **Advanced Task Management**: Dedicated tasks schema with fields for status transitions, priority, and deadlines.
- **Multi-Agent Coordination**: Centralized session tracking preventing duplicate coding and file-editing conflicts.
- **Raw SQL Execution**: Gives AI ultimate flexibility for complex queries and DDL operations.

## Setup

Users will need to provide their PostgreSQL credentials using the `PG_BASE_DSN` environment variable. This is a standard connection string:
`postgresql://<USERNAME>:<PASSWORD>@<HOST>:<PORT>/<DEFAULT_DB>`

### Where to configure this (Client Setup)

The exact location depends on which AI client you are using. You need to add the server configuration to your client's MCP settings file.

**For Claude Desktop:**
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**For Cursor:**
- Go to `Settings` > `Features` > `MCP` and add a new MCP server, or edit your project's `.cursor/mcp.json`.

**For Roo Code / Cline (VS Code):**
- Edit the MCP settings file located at `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` (Mac) or the equivalent Windows path.

**For Gemini CLI & Qwen CLI:**
- Open your global configuration file (usually located at `~/.gemini/settings.json` or `~/.qwen/settings.json`).
- Alternatively, use the CLI:
  ```bash
  gemini mcp add pg-mnemosyne "/path/to/pg-mnemosyne" -e PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -s user
  # OR
  qwen mcp add pg-mnemosyne "/path/to/pg-mnemosyne" -e PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -s user
  ```

**For Claude Code CLI:**
- The easiest way is to add it via the CLI:
  ```bash
  claude mcp add pg-mnemosyne "/path/to/pg-mnemosyne" -e PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -s user
  ```
- Manually, it lives in your global config at `~/.claude.json`.

**For Codex CLI:**
- The easiest way is to add it via the CLI:
  ```bash
  codex mcp add pg-mnemosyne --env PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -- pg-mnemosyne
  ```
- Manually, it lives in your global config at `~/.codex/config.toml` (TOML format).

**For Windsurf IDE:**
- Edit your global config at `~/.codeium/windsurf/mcp_config.json`.
- Alternatively, click the **Hammer (MCP) icon** in the Cascade panel and select **Configure**.

**For Antigravity CLI (agy):**
Antigravity uses a plugin-based system. To add the server:
1. Create a plugin directory: `mkdir -p ~/.gemini/config/plugins/pg-mnemosyne`
2. Create `~/.gemini/config/plugins/pg-mnemosyne/mcp_config.json` with the **Standard Template** below.
3. Add an entry to your `~/.gemini/config/import_manifest.json` under the `"imports"` array:
   ```json
   {
     "name": "pg-mnemosyne",
     "source": "manual",
     "components": ["mcpServers"]
   }
   ```

**Configuration Template (Claude Desktop, Cursor, Roo Code, Gemini CLI, Claude Code, Antigravity, Windsurf):**

```json
{
  "mcpServers": {
    "pg-mnemosyne": {
      "command": "pg-mnemosyne",
      "env": {
        "PG_BASE_DSN": "postgresql://postgres:my_password@localhost:5432/postgres"
      }
    }
  }
}
```

**For OpenCode:**
- Edit your OpenCode configuration file located at `~/.config/opencode/opencode.jsonc`.

**Configuration Template (OpenCode):**

```jsonc
{
  "mcp": {
    "pg-mnemosyne": {
      "type": "local",
      "command": ["pg-mnemosyne"],
      "environment": {
        "PG_BASE_DSN": "postgresql://postgres:my_password@localhost:5432/postgres"
      }
    }
  }
}
```

## Running the Server (Standalone)

```bash
pg-mnemosyne run
```

This starts the MCP server using standard input/output.

## CLI Usage

The `pg-mnemosyne` command also acts as a standalone CLI for managing your data and configuring agents.

### Auto-Initialization
You can automatically configure all supported AI agents (Claude, Gemini, Qwen, Cursor, etc.) with a single command:
```bash
pg-mnemosyne init --dsn "postgresql://user:pass@localhost:5432/postgres"
```

### Manual Record Management
You can add and list records directly from your terminal:
```bash
# Add a record
pg-mnemosyne add my_project_db todo "Finish the documentation"

# List records
pg-mnemosyne list my_project_db --type todo
```

## 🤝 Multi-Agent Coordination & Advanced Tasks

Pg-Mnemosyne includes specialized schemas to help complex multi-agent setups (e.g. Gemini CLI, Codex CLI, Roo Code, Claude Desktop) coordinate on the same project:

### 📋 Professional Tasks Schema
Spin up a dedicated `tasks` table with fields for statuses (`backlog`, `todo`, `in_progress`, `blocked`, `done`), priority levels (`low`, `medium`, `high`, `critical`), tags, and deadlines:
```bash
pg-mnemosyne init-todo my_project_db
```

### 🛰️ Agent Coordination Hub
Avoid merge conflicts, double-coding, and redundant compiler troubleshooting by initializing the shared `agent_sessions` coordination table:
```bash
pg-mnemosyne init-coordination my_project_db
```
When active, agents use the `update_agent_session` and `get_active_sessions` MCP tools to register their current editing files and active subtasks, creating a real-time bulletin board for mutual visibility!

## Available MCP Tools

- `create_project_db(db_name: str)`: Creates a new isolated PostgreSQL database.
- `init_schema(db_name: str)`: Initializes the base `records` table.
- `init_todo_schema(db_name: str)`: Initializes a professional `tasks` table.
- `init_coordination_schema(db_name: str)`: Initializes the multi-agent `agent_sessions` table.
- `add_column(db_name: str, table: str, column_name: str, data_type: str)`: Dynamically adds a column to any table.
- `add_record(db_name: str, type: str, content: str, tags: list[str])`: Adds a memory/todo record.
- `get_records(db_name: str, type: str = None, limit: int = 50)`: Retrieves recent records.
- `update_record(db_name: str, record_id: int, content: str = None, tags: list[str] = None, status: str = None)`: Partially updates a record.
- `delete_record(db_name: str, record_id: int)`: Deletes a record by ID.
- `update_agent_session(db_name: str, agent_name: str, active_task: str, active_file: str = None, status: str = "active")`: Registers/updates active agent state.
- `get_active_sessions(db_name: str)`: Lists active agent coordination sessions.
- `run_sql(db_name: str, query: str)`: Runs arbitrary SQL (SELECT, INSERT, DDL, etc.).
