import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.technical
import modules.finance

logger = logging.getLogger(__name__)

class TechnicalAnalysisTool(Tool):
    """
    Technical analysis tool for indicators, patterns, and signals.
    """
    name = "TechnicalAnalysisTool"
    description = "Technical analysis: RSI, MACD, Bollinger Bands, moving averages, ATR, candlestick patterns. Actions: indicators, signal, patterns, extended"
    risk_level = "SAFE"
    latency_weight = 1.3
    cost_weight = 0.3
    base_confidence = 0.94
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 1500

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        symbol = params.get("symbol", "")
        if not symbol and action != "default":
            return "Error: 'symbol' is required for technical analysis."
            
        period = params.get("period", "1y")

        try:
            if action == "indicators":
                indicators = modules.technical.compute_indicators(symbol, period)
                signal_data = ""
                if hasattr(modules.technical, "get_signal"):
                    signal_data = modules.technical.get_signal(indicators)
                return modules.technical.format_technical_summary(symbol, indicators, signal_data)
                
            elif action == "signal":
                indicators = modules.technical.compute_indicators(symbol, period)
                if hasattr(modules.technical, "get_signal"):
                    return f"Trading Signal for {symbol}: {str(modules.technical.get_signal(indicators))}"
                return f"Signal data available within indicators output for {symbol}."
                
            elif action == "patterns":
                if hasattr(modules.technical, "detect_candlestick_patterns"):
                    df = params.get("df", None)
                    if df is None:
                        # Attempt to fetch basic dataframe if not provided
                        df = modules.finance.get_ohlcv_history(symbol, period, "1d")
                    res = modules.technical.detect_candlestick_patterns(df)
                    return f"Candlestick Patterns for {symbol}:\n{str(res)}"
                else:
                    return f"Candlestick pattern detection is currently unavailable for {symbol}."
                    
            elif action == "extended":
                if hasattr(modules.technical, "compute_extended_indicators"):
                    res = modules.technical.compute_extended_indicators(symbol, period)
                else:
                    res = modules.technical.compute_indicators(symbol, period)
                return f"Extended Technical Indicators for {symbol}:\n{str(res)}"
                
            elif action == "default" and symbol:
                indicators = modules.technical.compute_indicators(symbol, period)
                signal_data = ""
                if hasattr(modules.technical, "get_signal"):
                    signal_data = modules.technical.get_signal(indicators)
                return modules.technical.format_technical_summary(symbol, indicators, signal_data)

            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in TechnicalAnalysisTool: {str(e)}")
            return f"Error: {e}"
