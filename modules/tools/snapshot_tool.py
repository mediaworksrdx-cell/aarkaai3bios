import time
from typing import Dict, Any
from modules.tools.base import Tool
from modules.repo_indexer import WorkspaceSnapshot

class SnapshotTool(Tool):
    name = "SnapshotTool"
    description = (
        "Create, list, or rollback transactional backups of workspace files."
    )
    risk_level = "HIGH"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 1.0

    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 1500

    def execute(self, params: Dict[str, Any]) -> str:
        operation = params.get("operation")
        if not operation:
            return "Error: 'operation' is required ('backup', 'restore')."

        snapshot_id = params.get("snapshot_id", f"snap_{int(time.time())}")
        files = params.get("files", []) # List of relative files to backup

        try:
            if operation == "backup":
                if not files:
                    # Capture default core layout python files if none specified
                    files = ["main.py", "pipeline.py", "database.py", "config.py"]
                success = WorkspaceSnapshot.create_snapshot(snapshot_id, files)
                if success:
                    return f"Workspace snapshot created successfully. ID: {snapshot_id}"
                return "Failed to create workspace snapshot."
            elif operation == "restore":
                target_id = params.get("snapshot_id")
                if not target_id:
                    return "Error: 'snapshot_id' is required for restore operations."
                success = WorkspaceSnapshot.restore_snapshot(target_id)
                if success:
                    return f"Workspace successfully rolled back to snapshot: {target_id}"
                return f"Snapshot rollback failed for ID: {target_id}"
            else:
                return f"Unsupported snapshot operation: {operation}"
        except Exception as e:
            return f"Snapshot execution error: {e}"
