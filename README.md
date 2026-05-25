# PG Super Memory MCP

A Model Context Protocol (MCP) server that provides AI assistants with a robust "super memory", task tracker, and dynamic PostgreSQL database management capabilities.

## ⚡ Quick Start

1. **Install the package:**
   ```bash
   pip install pg-super-memory-mcp
   ```

2. **Auto-configure all your AI agents (Claude, Gemini, Qwen, Cursor, etc.) at once:**
   ```bash
   pg-super-memory init --dsn "postgresql://user:password@localhost:5432/postgres"
   ```

3. **Restart your AI agents.** You're done!

---

## Features
- **High-Performance**: Uses `asyncpg` for fast asynchronous database operations.
- **Dynamic Projects**: The AI can create new databases for different projects on the fly.
- **Dynamic Schema**: The AI can modify table schemas (e.g., adding columns) dynamically to adapt to changing memory needs.
- **Standard Memory Tracker**: Built-in support for tracking `todo`, `error`, `feature`, and generic `memory` items with tags.
- **Raw SQL Execution**: Gives AI ultimate flexibility for complex queries and DDL operations.

## Installation

```bash
pip install pg-super-memory-mcp
```

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
  gemini mcp add pg-super-memory "/path/to/pg-super-memory" -e PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -s user
  # OR
  qwen mcp add pg-super-memory "/path/to/pg-super-memory" -e PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -s user
  ```

**For Claude Code CLI:**
- The easiest way is to add it via the CLI:
  ```bash
  claude mcp add pg-super-memory "/path/to/pg-super-memory" -e PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -s user
  ```
- Manually, it lives in your global config at `~/.claude.json`.

**For Codex CLI:**
- The easiest way is to add it via the CLI:
  ```bash
  codex mcp add pg-super-memory --env PG_BASE_DSN="postgresql://user:pass@localhost:5432/postgres" -- pg-super-memory
  ```
- Manually, it lives in your global config at `~/.codex/config.toml` (TOML format).

**For Windsurf IDE:**
- Edit your global config at `~/.codeium/windsurf/mcp_config.json`.
- Alternatively, click the **Hammer (MCP) icon** in the Cascade panel and select **Configure**.

**Configuration Template (Claude Desktop, Cursor, Roo Code, Gemini CLI, Claude Code, Antigravity, Windsurf):**

```json
{
  "mcpServers": {
    "pg-super-memory": {
      "command": "pg-super-memory",
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
    "pg-super-memory": {
      "type": "local",
      "command": ["pg-super-memory"],
      "environment": {
        "PG_BASE_DSN": "postgresql://postgres:my_password@localhost:5432/postgres"
      }
    }
  }
}
```

## Running the Server (Standalone)

```bash
pg-super-memory run
```

This starts the MCP server using standard input/output.

## CLI Usage

The `pg-super-memory` command also acts as a standalone CLI for managing your data and configuring agents.

### Auto-Initialization
You can automatically configure all supported AI agents (Claude, Gemini, Qwen, Cursor, etc.) with a single command:
```bash
pg-super-memory init --dsn "postgresql://user:pass@localhost:5432/postgres"
```

### Manual Record Management
You can add and list records directly from your terminal:
```bash
# Add a record
pg-super-memory add my_project_db todo "Finish the documentation"

# List records
pg-super-memory list my_project_db --type todo
```

## Available MCP Tools

- `create_project_db(db_name: str)`: Creates a new isolated PostgreSQL database.
- `init_schema(db_name: str)`: Initializes the base `records` table in the given database.
- `add_column(db_name: str, table: str, column_name: str, data_type: str)`: Dynamically adds a column.
- `add_record(db_name: str, type: str, content: str, tags: list[str])`: Adds a memory/todo record.
- `get_records(db_name: str, type: str = None, limit: int = 50)`: Retrieves recent records.
- `run_sql(db_name: str, query: str)`: Runs arbitrary SQL (SELECT, INSERT, DDL, etc.).
