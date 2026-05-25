import os
import json
import logging
import asyncio
import argparse
import sys
import asyncpg
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
    try:
        conn = await asyncpg.connect(get_db_dsn(db_name))
        try:
            if type:
                records = await conn.fetch('SELECT * FROM records WHERE type = $1 ORDER BY created_at DESC LIMIT $2', type, limit)
            else:
                records = await conn.fetch('SELECT * FROM records ORDER BY created_at DESC LIMIT $1', limit)
            
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
        return f"Error retrieving records: {e}"

# --- CLI Command Implementations ---

def cmd_run():
    """Starts the MCP server."""
    mcp.run(transport='stdio')

async def cmd_init(dsn: str):
    """Automatically configures all supported AI agents."""
    import shutil
    
    home = os.path.expanduser("~")
    executable = shutil.which("pg-mnemosyne") or sys.executable + " -m pg-mnemosyne.server"
    
    # Config definitions
    configs = {
        "Gemini CLI": {
            "path": os.path.join(home, ".gemini", "settings.json"),
            "key": "mcpServers"
        },
        "Qwen CLI": {
            "path": os.path.join(home, ".qwen", "settings.json"),
            "key": "mcpServers"
        },
        "Claude Code": {
            "path": os.path.join(home, ".claude.json"),
            "key": "mcpServers"
        },
        "Windsurf": {
            "path": os.path.join(home, ".codeium", "windsurf", "mcp_config.json"),
            "key": "mcpServers"
        },
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

    # Process standard JSON configs
    for name, info in configs.items():
        path = info["path"]
        if os.path.exists(os.path.dirname(path)):
            try:
                data = {}
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        content = f.read()
                        if content.strip():
                            # Attempt to strip comments if json.loads fails
                            try:
                                data = json.loads(content)
                            except json.JSONDecodeError:
                                import re
                                # Simple regex to remove // comments
                                clean_content = re.sub(r'//.*', '', content)
                                data = json.loads(clean_content)
                
                mcp_key = info["key"]
                if mcp_key not in data: data[mcp_key] = {}
                
                # Only update if it changed or doesn't exist to minimize writes
                new_entry = {
                    "command": executable,
                    "args": [],
                    "env": {"PG_BASE_DSN": dsn}
                }
                
                if data[mcp_key].get("pg-mnemosyne") != new_entry:
                    data[mcp_key]["pg-mnemosyne"] = new_entry
                    with open(path, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"✅ Configured {name} at {path}")
                else:
                    print(f"ℹ️  {name} already configured, skipping.")
            except Exception as e:
                print(f"⚠️  Skipped {name}: {e} (Manual setup might be needed)")

    # Process OpenCode (Special format)
    opencode_path = os.path.join(home, ".config", "opencode", "opencode.jsonc")
    if os.path.exists(os.path.dirname(opencode_path)):
        try:
            data = {"$schema": "https://opencode.ai/config.json"}
            if os.path.exists(opencode_path):
                with open(opencode_path, 'r') as f:
                    content = f.read()
                    if content.strip(): 
                        import re
                        clean_content = re.sub(r'//.*', '', content)
                        try: data = json.loads(clean_content)
                        except: pass
            
            if "mcp" not in data: data["mcp"] = {}
            new_entry = {
                "type": "local",
                "command": [executable],
                "environment": {"PG_BASE_DSN": dsn}
            }
            if data["mcp"].get("pg-mnemosyne") != new_entry:
                data["mcp"]["pg-mnemosyne"] = new_entry
                with open(opencode_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"✅ Configured OpenCode at {opencode_path}")
            else:
                print(f"ℹ️  OpenCode already configured, skipping.")
        except Exception as e:
            print(f"⚠️  Skipped OpenCode: {e}")

    # Process Codex (TOML)
    codex_path = os.path.join(home, ".codex", "config.toml")
    if os.path.exists(os.path.dirname(codex_path)):
        try:
            content = ""
            if os.path.exists(codex_path):
                with open(codex_path, 'r') as f: content = f.read()
            
            if "[mcp_servers.pg-mnemosyne]" not in content:
                entry = f'\n[mcp_servers.pg-mnemosyne]\ncommand = "{executable}"\n\n[mcp_servers.pg-mnemosyne.env]\nPG_BASE_DSN = "{dsn}"\n'
                with open(codex_path, 'a') as f:
                    f.write(entry)
                print(f"✅ Configured Codex at {codex_path}")
            else:
                print(f"ℹ️  Codex already configured, skipping.")
        except Exception as e:
            print(f"⚠️  Skipped Codex: {e}")

    # Process Antigravity (Plugin)
    agy_dir = os.path.join(home, ".gemini", "config", "plugins", "pg-mnemosyne")
    manifest_path = os.path.join(home, ".gemini", "config", "import_manifest.json")
    if os.path.exists(os.path.dirname(manifest_path)):
        try:
            os.makedirs(agy_dir, exist_ok=True)
            with open(os.path.join(agy_dir, "plugin.json"), 'w') as f:
                json.dump({"name": "pg-mnemosyne"}, f)
            with open(os.path.join(agy_dir, "mcp_config.json"), 'w') as f:
                json.dump({"mcpServers": {"pg-mnemosyne": {"command": executable, "args": [], "env": {"PG_BASE_DSN": dsn}}}}, f, indent=2)
            
            # Update manifest
            manifest = {"imports": []}
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f: manifest = json.load(f)
            
            if not any(i.get("name") == "pg-mnemosyne" for i in manifest["imports"]):
                manifest["imports"].append({"name": "pg-mnemosyne", "source": "manual", "components": ["mcpServers"]})
                with open(manifest_path, 'w') as f: json.dump(manifest, f, indent=2)
            print(f"✅ Configured Antigravity (agy) plugin")
        except Exception as e:
            print(f"❌ Failed to configure Antigravity: {e}")

    print(f"\n✨ Initialization complete! Restart your AI agents to see the new tools.")

async def cmd_add(db: str, type: str, content: str):
    """CLI shortcut to add a record."""
    print(await add_record(db, type, content))

async def cmd_list(db: str, type: str = None):
    """CLI shortcut to list records."""
    print(await get_records(db, type))

def main():
    parser = argparse.ArgumentParser(description="PG Super Memory CLI & MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run (Server)
    subparsers.add_parser("run", help="Start the MCP server (default)")

    # Init
    init_parser = subparsers.add_parser("init", help="Auto-configure all supported AI agents")
    init_parser.add_argument("--dsn", default=get_base_dsn(), help="PostgreSQL DSN (connection string)")

    # Add
    add_parser = subparsers.add_parser("add", help="Add a record to the memory")
    add_parser.add_argument("db", help="Database name")
    add_parser.add_argument("type", help="Record type (todo, error, feature, etc.)")
    add_parser.add_argument("content", help="Content of the record")

    # List
    list_parser = subparsers.add_parser("list", help="List records")
    list_parser.add_argument("db", help="Database name")
    list_parser.add_argument("--type", help="Filter by type")

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(cmd_init(args.dsn))
    elif args.command == "add":
        asyncio.run(cmd_add(args.db, args.type, args.content))
    elif args.command == "list":
        asyncio.run(cmd_list(args.db, args.type))
    else:
        # Default behavior: run the server
        cmd_run()

if __name__ == "__main__":
    main()
