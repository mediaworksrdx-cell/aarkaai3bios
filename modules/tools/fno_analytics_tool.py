import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.fno_analytics
import modules.finance

logger = logging.getLogger(__name__)

class FnOAnalyticsTool(Tool):
    """
    Futures and Options analytics tool for greeks, max pain, PCR, etc.
    """
    name = "FnOAnalyticsTool"
    description = "F&O analytics: option Greeks, Max Pain, PCR, IV analysis, OI analysis. Actions: greeks, max_pain, pcr, iv_analysis, oi_analysis"
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.5
    base_confidence = 0.93
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 1000

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        
        try:
            if action == "greeks":
                spot = float(params.get("spot", 0.0))
                strike = float(params.get("strike", 0.0))
                time_to_expiry = float(params.get("time_to_expiry", 0.0))
                risk_free_rate = float(params.get("risk_free_rate", 0.065))
                volatility = float(params.get("volatility", 0.0))
                option_type = params.get("option_type", "call")
                
                result = modules.fno_analytics.compute_greeks(
                    spot, strike, time_to_expiry, risk_free_rate, volatility, option_type
                )
                return modules.fno_analytics.format_greeks_context(result)
                
            elif action == "max_pain":
                symbol = params.get("symbol", "")
                chain = params.get("options_chain", None)
                if not chain and symbol:
                    chain = modules.finance.get_options_chain(symbol)
                result = modules.fno_analytics.compute_max_pain(chain)
                return f"Max Pain Analysis:\n{str(result)}"
                
            elif action == "pcr":
                symbol = params.get("symbol", "")
                chain = params.get("options_chain", None)
                if not chain and symbol:
                    chain = modules.finance.get_options_chain(symbol)
                result = modules.fno_analytics.compute_pcr(chain)
                return f"PCR Analysis:\n{str(result)}"
                
            elif action == "iv_analysis":
                iv_history = params.get("iv_history", [])
                current_iv = float(params.get("current_iv", 0.0))
                result = modules.fno_analytics.compute_iv_percentile(iv_history, current_iv)
                return f"IV Percentile Analysis:\n{str(result)}"
                
            elif action == "oi_analysis":
                symbol = params.get("symbol", "")
                chain = params.get("options_chain", None)
                if not chain and symbol:
                    chain = modules.finance.get_options_chain(symbol)
                result = modules.fno_analytics.oi_analysis(chain)
                return f"Open Interest Analysis:\n{str(result)}"
                
            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in FnOAnalyticsTool: {str(e)}")
            return f"Error: {e}"
