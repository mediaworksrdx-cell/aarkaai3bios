from typing import Any, Dict
from modules.tools.base import Tool
from modules import rag

class KnowledgeSearchTool(Tool):
    name = "KnowledgeSearchTool"
    description = "Search internal knowledge base and financial documents via RAG. Actions: search, store"
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.3
    base_confidence = 0.90
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 800

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        try:
            if action == "search":
                return self._handle_search(params)
            elif action == "store":
                return self._handle_store(params)
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"

    def _handle_search(self, params: Dict[str, Any]) -> str:
        query = params.get("query")
        if not query:
            return "Error: 'query' parameter is required for search action."
        user_id = params.get("user_id", "default")
        top_k = params.get("top_k", 3)
        return str(rag.retrieve(query, user_id, top_k))

    def _handle_store(self, params: Dict[str, Any]) -> str:
        topic = params.get("topic")
        content = params.get("content")
        user_id = params.get("user_id")
        source = params.get("source", "user")
        if not topic or not content or not user_id:
            return "Error: 'topic', 'content', and 'user_id' parameters are required for store action."
        result = rag.store_knowledge(topic, content, source, user_id)
        return str(result)
