import traceback

tools_to_test = [
    ("MarketDataTool", {'action': 'price', 'symbol': 'RELIANCE.NS'}, False),
    ("FinancialDataTool", {'action': 'ratios', 'symbol': 'INFY.NS'}, False),
    ("FinancialNewsTool", {'action': 'search', 'query': 'RBI policy'}, False),
    ("FinancialCalculatorTool", {'action': 'cagr', 'initial_value': 100000, 'final_value': 250000, 'years': 5}, True),
    ("PortfolioTool", {'action': 'holdings'}, False),
    ("TechnicalAnalysisTool", {'action': 'indicators', 'symbol': 'TCS.NS'}, False),
    ("FnOAnalyticsTool", {'action': 'greeks', 'spot': 2400, 'strike': 2500, 'time_to_expiry': 0.1, 'volatility': 0.25, 'risk_free_rate': 0.065, 'option_type': 'call'}, True),
    ("KnowledgeSearchTool", {'action': 'search', 'query': 'what is PE ratio'}, False),
    ("FinanceCodeTool", {'action': 'execute', 'code': 'print(2+2)'}, False),
    ("MarketDateTimeTool", {'action': 'market_status', 'exchange': 'NSE'}, True),
    ("DocumentParserTool", {'action': 'parse', 'file_path': 'test.pdf'}, False),
    ("DatabaseQueryTool", {'action': 'query', 'query': 'SELECT 1'}, False),
    ("NotificationTool", {'action': 'list'}, False),
    ("AuthPermissionTool", {'action': 'check', 'tool_name': 'MarketDataTool', 'user_tier': 'free'}, True)
]

def main():
    try:
        import modules.tools as tools_module
    except ImportError as e:
        print("Failed to import modules.tools:", e)
        return
        
    for tool_name, params, offline in tools_to_test:
        try:
            ToolClass = getattr(tools_module, tool_name)
            tool_instance = ToolClass()
            
            result = tool_instance.execute(params)
            
            result_str = str(result)
            safe_str = result_str.encode('ascii', errors='replace').decode('ascii')
            safe_str = safe_str.replace("\n", " ")
            short_str = (safe_str[:100] + '...') if len(safe_str) > 100 else safe_str
            
            if offline:
                if result_str and not result_str.startswith('Error:'):
                    print(f"PASS: {tool_name} - {short_str}")
                else:
                    print(f"FAIL: {tool_name} - {short_str}")
            else:
                if isinstance(result_str, str) and len(result_str) > 0:
                    print(f"PASS: {tool_name} - {short_str}")
                else:
                    print(f"FAIL: {tool_name} - Empty or non-string result")
        except Exception as e:
            err_str = str(e).encode('ascii', errors='replace').decode('ascii')
            print(f"FAIL: {tool_name} - Exception: {err_str[:100]}")

if __name__ == '__main__':
    main()
