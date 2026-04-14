from modules.tools.base import Tool
from modules.web_search import get_web_context

class WebSearchTool(Tool):
    name = "WebSearch"
    description = "Search the internet (DuckDuckGo + Wikipedia) for up-to-date information, documentation, or to solve errors. Provide a search 'query' in the Action Input JSON."

    def execute(self, params: dict) -> str:
        query = params.get("query")
        if not query:
            return "Error: 'query' parameter is required in Action Input."
        
        try:
            result = get_web_context(query)
            if not result:
                return f"No useful results found on the web for: {query}"
            return result
        except Exception as e:
            return f"Error executing WebSearch: {e}"
