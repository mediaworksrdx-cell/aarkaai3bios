import psutil
import time
from typing import Dict, Any
from modules.tools.base import Tool

class MonitorTool(Tool):
    name = "MonitorTool"
    description = (
        "Retrieve runtime telemetry statistics (CPU load, memory allocation, active processes)."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 150

    def execute(self, params: Dict[str, Any]) -> str:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage(".")
            
            stats = (
                f"System Monitor Metrics:\n"
                f"CPU Utilization: {cpu}%\n"
                f"Memory: {mem.percent}% (Used: {mem.used // 1024 // 1024}MB / Total: {mem.total // 1024 // 1024}MB)\n"
                f"Disk: {disk.percent}% (Free: {disk.free // 1024 // 1024 // 1024}GB)\n"
                f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return stats
        except Exception as e:
            return f"Error retrieving metrics telemetry: {e}"
