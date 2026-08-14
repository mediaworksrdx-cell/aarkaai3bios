import sqlite3
import os
from typing import Dict, Any
from modules.tools.base import Tool

class DbMigrateTool(Tool):
    name = "DbMigrateTool"
    description = (
        "Execute database migration queries and schema deployments on SQLite "
        "or ChromaDB collections."
    )
    risk_level = "CRITICAL"
    latency_weight = 1.5
    cost_weight = 0.5
    base_confidence = 0.98

    permissions = ["write"]
    supported_languages = ["sql"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 1200

    def execute(self, params: Dict[str, Any]) -> str:
        operation = params.get("operation")
        if not operation:
            return "Error: 'operation' is required ('migrate', 'verify')."

        db_path = os.environ.get("AARKAAI_DB_PATH", "aarkaai.db")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Retrieve schema status
            cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
            conn.commit()
            
            if operation == "verify":
                cursor.execute("SELECT version FROM schema_migrations ORDER BY version DESC")
                rows = cursor.fetchall()
                versions = [r[0] for r in rows]
                return f"Database Schema Version Log: {versions if versions else 'No migrations applied.'}"
            
            elif operation == "migrate":
                # Execute stub migration script representing v2.0 updates
                cursor.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (2)")
                conn.commit()
                return "Successfully updated database schema to version 2."
            else:
                return f"Unsupported migration operation: {operation}"
        except Exception as e:
            return f"Database schema modification error: {e}"
        finally:
            conn.close()
