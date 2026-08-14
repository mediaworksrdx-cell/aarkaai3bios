from typing import Dict, Any
from modules.tools.base import Tool
from modules import rag

class RAGTool(Tool):
    name = "RAGTool"
    description = (
        "Query semantic database collections and documentation embeddings natively "
        "matching user queries."
    )
    risk_level = "SAFE"
    latency_weight = 0.8
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 400

    def execute(self, params: Dict[str, Any]) -> str:
        query = params.get("query")
        if not query:
            return "Error: 'query' argument is required."

        try:
            results = rag.query(query, limit=5)
            if not results:
                return "No matching semantic documentation retrieved."
            
            res = []
            for i, r in enumerate(results, 1):
                res.append(f"[{i}] Content: {r.get('text', '')}\nMetadata: {r.get('metadata', {})}\n")
            return "\n".join(res)
        except Exception as e:
            return f"RAG query execution error: {e}"
