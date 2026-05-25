import os
import json
import logging
import asyncio
import argparse
import sys
import asyncpg
import re
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("pg-mnemosyne")

# Create the MCP server instance
mcp = FastMCP("Pg-Mnemosyne")

def get_base_dsn() -> str:
    """Returns the base PostgreSQL connection string from environment."""
    return os.environ.get("PG_BASE_DSN", "postgresql://postgres:postgres@localhost:5432/postgres")

def get_db_dsn(db_name: str) -> str:
    """Returns the connection string for a specific database."""
    base = get_base_dsn()
    parts = base.rsplit("/", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{db_name}"
    return base

# --- Helper Functions ---

async def fetch_json(dsn: str, query: str, *args):
    """Executes a query and returns results as a formatted JSON string."""
    try:
        conn = await asyncpg.connect(dsn)
        try:
            records = await conn.fetch(query, *args)
            result_list = []
            for r in records:
                d = dict(r)
                for k, v in d.items():
                    if hasattr(v, 'isoformat'): d[k] = v.isoformat()
                result_list.append(d)
            return json.dumps(result_list, indent=2)
        finally:
            await conn.close()
    except Exception as e:
        return f"Error: {e}"

# --- MCP Tool Definitions ---

@mcp.tool()
async def create_project_db(db_name: str) -> str:
    """Creates a new PostgreSQL database for a project."""
    try:
        conn = await asyncpg.connect(get_base_dsn())
        try:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            return f"Database '{db_name}' created successfully."
        except asyncpg.exceptions.DuplicateDatabaseError:
            return f"Database '{db_name}' already exists."
        finally:
            await conn.close()
    except Exception as e:
        return f"Error creating database: {e}"

@mcp.tool()
async def init_schema(db_name: str) -> str:
    """Initializes the base 'records' table in the specified database."""
    try:
        conn = await asyncpg.connect(get_db_dsn(db_name))
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id SERIAL PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT[] DEFAULT '{}',
                    status VARCHAR(50) DEFAULT 'open',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            return f"Base schema initialized in database '{db_name}'."
        finally:
            await conn.close()
    except Exception as e:
        return f"Error initializing schema: {e}"

@mcp.tool()
async def add_column(db_name: str, table: str, column_name: str, data_type: str) -> str:
    """Adds a new column to a table dynamically."""
    try:
        conn = await asyncpg.connect(get_db_dsn(db_name))
        try:
            await conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column_name}" {data_type}')
            return f"Column '{column_name}' added to table '{table}'."
        finally:
            await conn.close()
    except Exception as e:
        return f"Error adding column: {e}"

@mcp.tool()
async def run_sql(db_name: str, query: str) -> str:
    """Executes arbitrary SQL queries and returns results as JSON."""
    try:
        conn = await asyncpg.connect(get_db_dsn(db_name))
        try:
            q_upper = query.strip().upper()
            if q_upper.startswith("SELECT") or "RETURNING" in q_upper:
                records = await conn.fetch(query)
                result_list = []
                for r in records:
                    d = dict(r)
                    for k, v in d.items():
                        if hasattr(v, 'isoformat'): d[k] = v.isoformat()
                    result_list.append(d)
                return json.dumps(result_list, indent=2)
            else:
                status = await conn.execute(query)
                return f"Query executed. Status: {status}"
        finally:
            await conn.close()
    except Exception as e:
        return f"Error executing SQL: {e}"

@mcp.tool()
async def add_record(db_name: str, type: str, content: str, tags: List[str] = []) -> str:
    """Adds a new memory/task record."""
    try:
        conn = await asyncpg.connect(get_db_dsn(db_name))
        try:
            row_id = await conn.fetchval('''
                INSERT INTO records (type, content, tags)
                VALUES ($1, $2, $3)
                RETURNING id
            ''', type, content, tags)
            return f"Record added with ID: {row_id}"
        finally:
            await conn.close()
    except Exception as e:
        return f"Error adding record: {e}"

@mcp.tool()
async def get_records(db_name: str, type: Optional[str] = None, limit: int = 50) -> str:
    """Retrieves recent records from the database."""
    query = 'SELECT * FROM records ORDER BY created_at DESC LIMIT $1'
    args = [limit]
    if type:
        query = 'SELECT * FROM records WHERE type = $1 ORDER BY created_at DESC LIMIT $2'
        args = [type, limit]
    return await fetch_json(get_db_dsn(db_name), query, *args)

# --- CLI Command Implementations ---

def cmd_run():
    """Starts the MCP server."""
    mcp.run(transport='stdio')

async def cmd_init(dsn: str):
    """Automatically configures all supported AI agents."""
    import shutil
    
    home = os.path.expanduser("~")
    executable = shutil.which("pg-mnemosyne") or sys.executable + " -m pg_mnemosyne.server"
    
    # Config definitions
    configs = {
        "Gemini CLI": { "path": os.path.join(home, ".gemini", "settings.json"), "key": "mcpServers" },
        "Qwen CLI": { "path": os.path.join(home, ".qwen", "settings.json"), "key": "mcpServers" },
        "Claude Code": { "path": os.path.join(home, ".claude.json"), "key": "mcpServers" },
        "Windsurf": { "path": os.path.join(home, ".codeium", "windsurf", "mcp_config.json"), "key": "mcpServers" },
        "Roo Code / Cline": {
            "path": os.path.expandvars(os.path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json")) if sys.platform == "darwin" else os.path.expandvars(os.path.join(os.environ.get("APPDATA", home), "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json")),
            "key": "mcpServers"
        },
        "Claude Desktop": {
            "path": os.path.expandvars(os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")) if sys.platform == "darwin" else os.path.expandvars(os.path.join(os.environ.get("APPDATA", home), "Claude", "claude_desktop_config.json")),
            "key": "mcpServers"
        }
    }

    print(f"🚀 Initializing pg-mnemosyne for supported agents...")
    print(f"🔗 Using DSN: {dsn}")

    for name, info in configs.items():
        path = info["path"]
        if os.path.exists(os.path.dirname(path)):
            try:
                data = {}
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        content = f.read()
                        if content.strip():
                            try:
                                data = json.loads(content)
                            except json.JSONDecodeError:
                                clean_content = re.sub(r'//.*', '', content)
                                data = json.loads(clean_content)
                
                mcp_key = info["key"]
                if mcp_key not in data: data[mcp_key] = {}
                
                new_entry = { "command": executable, "args": [], "env": {"PG_BASE_DSN": dsn} }
                
                if data[mcp_key].get("pg-mnemosyne") != new_entry:
                    data[mcp_key]["pg-mnemosyne"] = new_entry
                    with open(path, 'w') as f: json.dump(data, f, indent=2)
                    print(f"✅ Configured {name} at {path}")
                else:
                    print(f"ℹ️  {name} already configured, skipping.")
            except Exception as e:
                print(f"⚠️  Skipped {name}: {e}")

    # OpenCode
    opencode_path = os.path.join(home, ".config", "opencode", "opencode.jsonc")
    if os.path.exists(os.path.dirname(opencode_path)):
        try:
            data = {"$schema": "https://opencode.ai/config.json"}
            if os.path.exists(opencode_path):
                with open(opencode_path, 'r') as f:
                    content = f.read()
                    if content.strip(): 
                        clean_content = re.sub(r'//.*', '', content)
                        try: data = json.loads(clean_content)
                        except: pass
            if "mcp" not in data: data["mcp"] = {}
            new_entry = { "type": "local", "command": [executable], "environment": {"PG_BASE_DSN": dsn} }
            if data["mcp"].get("pg-mnemosyne") != new_entry:
                data["mcp"]["pg-mnemosyne"] = new_entry
                with open(opencode_path, 'w') as f: json.dump(data, f, indent=2)
                print(f"✅ Configured OpenCode at {opencode_path}")
            else:
                print(f"ℹ️  OpenCode already configured, skipping.")
        except Exception as e: print(f"⚠️  Skipped OpenCode: {e}")

    # Codex (TOML)
    codex_path = os.path.join(home, ".codex", "config.toml")
    if os.path.exists(os.path.dirname(codex_path)):
        try:
            content = ""
            if os.path.exists(codex_path):
                with open(codex_path, 'r') as f: content = f.read()
            if "[mcp_servers.pg-mnemosyne]" not in content:
                entry = f'\n[mcp_servers.pg-mnemosyne]\ncommand = "{executable}"\n\n[mcp_servers.pg-mnemosyne.env]\nPG_BASE_DSN = "{dsn}"\n'
                with open(codex_path, 'a') as f: f.write(entry)
                print(f"✅ Configured Codex at {codex_path}")
            else: print(f"ℹ️  Codex already configured, skipping.")
        except Exception as e: print(f"⚠️  Skipped Codex: {e}")

    # Antigravity (Plugin)
    agy_dir = os.path.join(home, ".gemini", "config", "plugins", "pg-mnemosyne")
    manifest_path = os.path.join(home, ".gemini", "config", "import_manifest.json")
    if os.path.exists(os.path.dirname(manifest_path)):
        try:
            os.makedirs(agy_dir, exist_ok=True)
            with open(os.path.join(agy_dir, "plugin.json"), 'w') as f: json.dump({"name": "pg-mnemosyne"}, f)
            with open(os.path.join(agy_dir, "mcp_config.json"), 'w') as f: json.dump({"mcpServers": {"pg-mnemosyne": {"command": executable, "args": [], "env": {"PG_BASE_DSN": dsn}}}}, f, indent=2)
            manifest = {"imports": []}
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f: manifest = json.load(f)
            if not any(i.get("name") == "pg-mnemosyne" for i in manifest["imports"]):
                manifest["imports"].append({"name": "pg-mnemosyne", "source": "manual", "components": ["mcpServers"]})
                with open(manifest_path, 'w') as f: json.dump(manifest, f, indent=2)
            print(f"✅ Configured Antigravity (agy) plugin")
        except Exception as e: print(f"❌ Failed to configure Antigravity: {e}")

    print(f"\n✨ Initialization complete! Restart your AI agents to see the new tools.")

async def cmd_list_dbs():
    """Lists all databases in the PostgreSQL instance."""
    print(await fetch_json(get_base_dsn(), "SELECT datname FROM pg_database WHERE datistemplate = false;"))

async def cmd_list_tables(db: str):
    """Lists all tables in the specified database."""
    print(await fetch_json(get_db_dsn(db), "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))

async def cmd_search(db: str, query: str):
    """Searches for records containing the query string."""
    sql = "SELECT * FROM records WHERE content ILIKE $1 OR type ILIKE $1 ORDER BY created_at DESC"
    print(await fetch_json(get_db_dsn(db), sql, f"%{query}%"))

async def cmd_delete(db: str, record_id: int):
    """Deletes a record by its ID."""
    try:
        conn = await asyncpg.connect(get_db_dsn(db))
        try:
            status = await conn.execute("DELETE FROM records WHERE id = $1", record_id)
            print(f"Record {record_id} deleted. Status: {status}")
        finally:
            await conn.close()
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Pg-Mnemosyne CLI & MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run
    subparsers.add_parser("run", help="Start the MCP server (default behavior)")

    # init
    init_parser = subparsers.add_parser("init", help="Auto-configure all supported AI agents")
    init_parser.add_argument("--dsn", default=get_base_dsn(), help="PostgreSQL DSN (connection string)")

    # list-dbs
    subparsers.add_parser("list-dbs", help="List all databases")

    # list-tables
    lt_parser = subparsers.add_parser("list-tables", help="List all tables in a database")
    lt_parser.add_argument("db", help="Database name")

    # add
    add_parser = subparsers.add_parser("add", help="Add a record (todo, error, feature, etc.)")
    add_parser.add_argument("db", help="Database name")
    add_parser.add_argument("type", help="Record type")
    add_parser.add_argument("content", help="Record content")

    # list
    list_parser = subparsers.add_parser("list", help="List records in a database")
    list_parser.add_argument("db", help="Database name")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.add_argument("--limit", type=int, default=50, help="Max records to show")

    # search
    search_parser = subparsers.add_parser("search", help="Search records by content or type")
    search_parser.add_argument("db", help="Database name")
    search_parser.add_argument("query", help="Search term")

    # delete
    del_parser = subparsers.add_parser("delete", help="Delete a record by ID")
    del_parser.add_argument("db", help="Database name")
    del_parser.add_argument("id", type=int, help="Record ID to delete")

    # init-schema
    is_parser = subparsers.add_parser("init-schema", help="Initialize the records table in a database")
    is_parser.add_argument("db", help="Database name")

    # sql
    sql_parser = subparsers.add_parser("sql", help="Run arbitrary SQL on a database")
    sql_parser.add_argument("db", help="Database name")
    sql_parser.add_argument("query", help="SQL query")

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(cmd_init(args.dsn))
    elif args.command == "init-schema":
        print(asyncio.run(init_schema(args.db)))
    elif args.command == "sql":
        print(asyncio.run(run_sql(args.db, args.query)))
    elif args.command == "list-dbs":
        asyncio.run(cmd_list_dbs())
    elif args.command == "list-tables":
        asyncio.run(cmd_list_tables(args.db))
    elif args.command == "add":
        print(asyncio.run(add_record(args.db, args.type, args.content)))
    elif args.command == "list":
        asyncio.run(cmd_list(args.db, args.type)) # Note: cmd_list was defined in previous version, I should ensure it exists or use get_records
    elif args.command == "search":
        asyncio.run(cmd_search(args.db, args.query))
    elif args.command == "delete":
        asyncio.run(cmd_delete(args.db, args.id))
    else:
        # If no command, default to running the server
        cmd_run()

async def cmd_list(db: str, type: str = None):
    """CLI shortcut to list records."""
    print(await get_records(db, type))

if __name__ == "__main__":
    main()
