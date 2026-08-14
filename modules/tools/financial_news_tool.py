import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.web_search

logger = logging.getLogger(__name__)

class FinancialNewsTool(Tool):
    """
    Financial news tool for market news and regulatory updates.
    """
    name = "FinancialNewsTool"
    description = "Financial news, company announcements, RBI/SEBI regulatory updates. Actions: market_news, company_news, regulatory_updates"
    risk_level = "SAFE"
    latency_weight = 1.8
    cost_weight = 0.5
    base_confidence = 0.88
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 2500

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        
        try:
            if action == "market_news":
                query = params.get("query", "latest market news")
                if hasattr(modules.web_search, "search_financial_news"):
                    return str(modules.web_search.search_financial_news(query))
                else:
                    return str(modules.web_search.get_web_context(query + ' financial news'))
                    
            elif action == "company_news":
                symbol = params.get("symbol", "")
                if not symbol:
                    return "Error: 'symbol' is required for company_news."
                if hasattr(modules.web_search, "search_company_announcements"):
                    return str(modules.web_search.search_company_announcements(symbol))
                else:
                    return str(modules.web_search.get_web_context(symbol + ' latest news announcements'))
                    
            elif action == "regulatory_updates":
                query = params.get("query", "")
                if hasattr(modules.web_search, "search_regulatory_updates"):
                    return str(modules.web_search.search_regulatory_updates(query))
                else:
                    return str(modules.web_search.get_web_context(query + ' RBI SEBI regulatory update'))
                    
            elif action in ("search", "default", "news"):
                query = params.get("query", "")
                symbol = params.get("symbol", "")
                if symbol:
                    if hasattr(modules.web_search, "search_company_announcements"):
                        return str(modules.web_search.search_company_announcements(symbol))
                    return str(modules.web_search.get_web_context(symbol + ' latest news announcements'))
                q = query if query else "latest financial and stock market news"
                if hasattr(modules.web_search, "search_financial_news"):
                    return str(modules.web_search.search_financial_news(q))
                return str(modules.web_search.get_web_context(q + ' financial news'))

            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in FinancialNewsTool: {str(e)}")
            return f"Error: {e}"
