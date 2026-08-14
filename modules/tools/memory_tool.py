import os
import sqlite3
from typing import Dict, Any
from modules.tools.base import Tool

class MemoryTool(Tool):
    name = "MemoryTool"
    description = (
        "Retrieve, set, or update persistent workflow memory records and "
        "historical task context from the SQLite database."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 80

    def execute(self, params: Dict[str, Any]) -> str:
        operation = params.get("operation")
        if not operation:
            return "Error: 'operation' is required ('get', 'set')."

        key = params.get("key")
        if not key:
            return "Error: 'key' is required."

        db_path = os.environ.get("AARKAAI_DB_PATH", "aarkaai.db")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Simple metadata table mapping key-values
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, val TEXT)"
            )
            conn.commit()

            if operation == "get":
                cursor.execute("SELECT val FROM metadata WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row[0] if row else f"No record found for key: {key}"

            elif operation == "set":
                val = params.get("val")
                if val is None:
                    return "Error: 'val' is required for set operations."
                cursor.execute(
                    "INSERT INTO metadata (key, val) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET val = excluded.val",
                    (key, str(val))
                )
                conn.commit()
                return f"Successfully set memory key '{key}'."

            else:
                return f"Unsupported memory operation: {operation}"
        except Exception as e:
            return f"Database error: {e}"
        finally:
            conn.close()
