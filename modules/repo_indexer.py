import os
import sys
import shutil
import sqlite3
import ast
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Constants
SAFE_WORK_DIR = os.getcwd()
DB_PATH = os.path.join(SAFE_WORK_DIR, "aarkaai.db")
BACKUP_DIR = os.path.join(SAFE_WORK_DIR, "scratch", "workspace_snapshots")

class WorkspaceSnapshot:
    """Manages transactional state checkpoints and rollbacks of files in the workspace."""
    
    @staticmethod
    def create_snapshot(snapshot_id: str, files: List[str]) -> bool:
        try:
            snap_path = os.path.join(BACKUP_DIR, snapshot_id)
            os.makedirs(snap_path, exist_ok=True)
            
            for file_rel in files:
                src = os.path.join(SAFE_WORK_DIR, file_rel)
                if os.path.exists(src):
                    dest = os.path.join(snap_path, file_rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
            logger.info("WorkspaceSnapshot: Created snapshot '%s' for %d files.", snapshot_id, len(files))
            return True
        except Exception as exc:
            logger.error("Failed to create workspace snapshot: %s", exc)
            return False

    @staticmethod
    def restore_snapshot(snapshot_id: str) -> bool:
        try:
            snap_path = os.path.join(BACKUP_DIR, snapshot_id)
            if not os.path.exists(snap_path):
                logger.warning("WorkspaceSnapshot: Snapshot path '%s' not found.", snap_path)
                return False
                
            for root, _, files in os.walk(snap_path):
                for file in files:
                    src = os.path.join(root, file)
                    rel_path = os.path.relpath(src, snap_path)
                    dest = os.path.join(SAFE_WORK_DIR, rel_path)
                    
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
            logger.info("WorkspaceSnapshot: Restored snapshot '%s' successfully.", snapshot_id)
            return True
        except Exception as exc:
            logger.error("Failed to restore workspace snapshot: %s", exc)
            return False

    @staticmethod
    def discard_snapshot(snapshot_id: str) -> None:
        try:
            snap_path = os.path.join(BACKUP_DIR, snapshot_id)
            if os.path.exists(snap_path):
                shutil.rmtree(snap_path)
                logger.info("WorkspaceSnapshot: Discarded snapshot '%s'.", snapshot_id)
        except Exception as exc:
            logger.error("Failed to discard workspace snapshot: %s", exc)

class RepoGraphStore:
    """SQLite-backed knowledge graph tracking dependencies, callers, definitions, and overrides."""
    
    @staticmethod
    def initialize_db() -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repo_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    type TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repo_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    target TEXT,
                    relation TEXT,
                    UNIQUE(source, target, relation)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error("Failed to initialize RepoGraphStore db: %s", exc)

    @staticmethod
    def add_node(name: str, node_type: str) -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO repo_nodes (name, type) VALUES (?, ?)",
                (name, node_type)
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error("RepoGraphStore: Failed to add node: %s", exc)

    @staticmethod
    def add_edge(source: str, target: str, relation: str) -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO repo_edges (source, target, relation) VALUES (?, ?, ?)",
                (source, target, relation)
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error("RepoGraphStore: Failed to add edge: %s", exc)

    @staticmethod
    def find_callers(target_name: str) -> List[str]:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source FROM repo_edges WHERE target = ? AND relation = 'CALLS'",
                (target_name,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception as exc:
            logger.error("RepoGraphStore: Find callers error: %s", exc)
            return []

class LanguageAdapter:
    """Extracts symbols, definitions, decorators, and type hints from files dynamically."""
    
    @staticmethod
    def parse_python_ast(code: str, file_path: str = "") -> List[Dict[str, Any]]:
        symbols = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    symbols.append({
                        "name": node.name,
                        "type": "class",
                        "line": node.lineno,
                        "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                        "file": file_path
                    })
                elif isinstance(node, ast.FunctionDef):
                    symbols.append({
                        "name": node.name,
                        "type": "function",
                        "line": node.lineno,
                        "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)],
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "file": file_path
                    })
        except Exception as exc:
            logger.warning("LanguageAdapter failed to parse file %s: %s", file_path, exc)
        return symbols

# Run initialization during startup
RepoGraphStore.initialize_db()
