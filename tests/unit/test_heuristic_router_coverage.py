import sys
from modules.tool_router import _heuristic_route

test_cases = {
    "MarketDataTool/price": [
        "What is the current price of TCS?",
        "Show me RELIANCE share price",
        "AAPL stock quote",
        "How much is Infosys trading at?",
        "HDFC Bank market cap",
        "current price of NVDA",
        "TSLA stock"
    ],
    "MarketDataTool/ohlcv": [
        "Show TCS price history",
        "RELIANCE chart data",
        "INFY candle data"
    ],
    "MarketDataTool/options_chain": [
        "NIFTY options chain",
        "TCS option chain"
    ],
    "FinancialDataTool": [
        "TCS balance sheet",
        "INFY income statement",
        "HDFC Bank PE ratio",
        "Reliance earnings",
        "TCS company profile"
    ],
    "FinancialCalculatorTool": [
        "Calculate CAGR of 100000 to 250000 over 5 years",
        "SIP of 5000 at 12% for 10 years",
        "EMI for 5000000 at 8.5% for 240 months",
        "risk reward 100 120 95",
        "position size 1000000 2 500 480"
    ],
    "TechnicalAnalysisTool": [
        "RSI of TCS",
        "MACD for Reliance",
        "Show VWAP for INFY",
        "Bollinger bands for HDFC",
        "TCS candlestick pattern"
    ],
    "MarketDateTimeTool": [
        "Is the NSE market open?",
        "Next expiry date",
        "Trading holidays 2025"
    ],
    "PortfolioTool": [
        "Show my portfolio",
        "My holdings",
        "My watchlist"
    ]
}

def run_tests():
    total_passed = 0
    total_failed = 0
    
    for category, queries in test_cases.items():
        print(f"\\n--- Testing {category} ---")
        expected_tool = category.split('/')[0]
        expected_action = category.split('/')[1] if '/' in category else None
        
        for query in queries:
            try:
                intents = _heuristic_route(query)
                
                if not intents:
                    print(f"FAIL: '{query}' -> No intents returned")
                    total_failed += 1
                    continue
                
                intent = intents[0]
                
                passed = True
                fail_reason = []
                
                if intent.tool_name != expected_tool:
                    passed = False
                    fail_reason.append(f"ToolName: {intent.tool_name} != {expected_tool}")
                    
                if intent.confidence < 0.9:
                    passed = False
                    fail_reason.append(f"Confidence: {intent.confidence} < 0.9")
                    
                if expected_action and intent.action != expected_action:
                    # Specific actions
                    passed = False
                    fail_reason.append(f"Action: {intent.action} != {expected_action}")
                
                if passed:
                    print(f"PASS: '{query}' -> [{intent.tool_name}/{intent.action}] (conf: {intent.confidence})")
                    total_passed += 1
                else:
                    print(f"FAIL: '{query}' -> [{intent.tool_name}/{intent.action}] (conf: {intent.confidence}) - Reasons: {', '.join(fail_reason)}")
                    total_failed += 1
                    
            except Exception as e:
                print(f"FAIL: '{query}' -> Exception: {str(e)}")
                total_failed += 1
                
    print(f"\\nTotal Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")

if __name__ == '__main__':
    run_tests()
