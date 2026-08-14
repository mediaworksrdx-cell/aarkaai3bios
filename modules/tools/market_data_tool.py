import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.finance

logger = logging.getLogger(__name__)

class MarketDataTool(Tool):
    """
    Market data tool for live prices, OHLCV history, and options.
    """
    name = "MarketDataTool"
    description = "Live stock/index prices, OHLCV history, options chain, OI, IV, PCR. Actions: price, ohlcv, options_chain, oi, iv, pcr"
    risk_level = "SAFE"
    latency_weight = 1.5
    cost_weight = 0.3
    base_confidence = 0.95
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 1500

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        symbol = params.get("symbol", "")
        if not symbol and action != "default":
            return "Error: 'symbol' is required for market data."

        try:
            if action == "price":
                result = modules.finance.get_market_data(query=symbol)
                if isinstance(result, dict) and result.get("summary"):
                    return result["summary"]
                elif isinstance(result, dict) and "data" in result and result["data"]:
                    return modules.finance.format_finance_context(result["data"])
                else:
                    # Fallback to direct ticker fetch if query failed to match extract_tickers
                    single_data = modules.finance._fetch_ticker_data(symbol)
                    return modules.finance.format_finance_context({symbol: single_data})
            
            elif action == "ohlcv":
                period = params.get("period", "1mo")
                interval = params.get("interval", "1d")
                data = modules.finance.get_ohlcv_history(symbol, period, interval)
                return modules.finance.format_ohlcv_context(data)
                
            elif action == "options_chain":
                data = modules.finance.get_options_chain(symbol)
                return modules.finance.format_options_context(data)
                
            elif action == "oi":
                data = modules.finance.get_open_interest_summary(symbol)
                return f"Open Interest Summary for {symbol}: {str(data)}"
                
            elif action == "iv":
                # Extracts IV data from options chain
                chain = modules.finance.get_options_chain(symbol)
                iv_data = chain.get("iv", chain.get("implied_volatility", "N/A")) if isinstance(chain, dict) else "N/A"
                return f"Implied Volatility for {symbol}: {str(iv_data)}"
                
            elif action == "pcr":
                # Extracts PCR from OI summary
                summary = modules.finance.get_open_interest_summary(symbol)
                pcr_data = summary.get("pcr", summary.get("put_call_ratio", "N/A")) if isinstance(summary, dict) else "N/A"
                return f"Put-Call Ratio (PCR) for {symbol}: {str(pcr_data)}"
                
            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in MarketDataTool: {str(e)}")
            return f"Error: {e}"
