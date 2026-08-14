from typing import Any, Dict
from modules.tools.base import Tool
from modules import document_parser

class DocumentParserTool(Tool):
    name = "DocumentParserTool"
    description = "Parse PDFs, annual reports, financial statements. Actions: parse, extract_tables, extract_figures, summarize"
    risk_level = "SAFE"
    latency_weight = 1.5
    cost_weight = 0.5
    base_confidence = 0.90
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 2000

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        try:
            if action == "parse":
                file_path = params.get("file_path")
                return str(document_parser.parse_pdf(file_path))
            elif action == "extract_tables":
                file_path = params.get("file_path")
                return str(document_parser.parse_financial_tables(file_path))
            elif action == "extract_figures":
                text = params.get("text")
                return str(document_parser.extract_key_figures(text))
            elif action == "summarize":
                file_path = params.get("file_path")
                max_chars = params.get("max_chars")
                return str(document_parser.summarize_document(file_path, max_chars))
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"
