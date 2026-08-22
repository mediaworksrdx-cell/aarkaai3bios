"""
AARKAAI – Direct Tool Execution & Routing Test
Verifies end-to-end flow: User → Router → Tool Execution → 7B Answer
"""
import sys
import unittest
from unittest.mock import patch

from modules.tool_router import process_with_tools, get_pipeline, _heuristic_route

class TestToolRouterExecution(unittest.TestCase):

    def test_heuristic_stock_price(self):
        intents = _heuristic_route("What is the current price of TCS?")
        self.assertTrue(len(intents) > 0)
        self.assertEqual(intents[0].tool_name, "MarketDataTool")
        self.assertEqual(intents[0].action, "price")
        self.assertEqual(intents[0].params["symbol"], "TCS.NS")
        print("  PASS: Heuristic stock price routing (TCS -> TCS.NS)")

    def test_heuristic_cagr_calc(self):
        intents = _heuristic_route("Calculate CAGR of 100000 to 250000 over 5 years")
        self.assertTrue(len(intents) > 0)
        self.assertEqual(intents[0].tool_name, "FinancialCalculatorTool")
        self.assertEqual(intents[0].action, "cagr")
        self.assertEqual(intents[0].params["initial_value"], 100000.0)
        self.assertEqual(intents[0].params["final_value"], 250000.0)
        self.assertEqual(intents[0].params["years"], 5.0)
        print("  PASS: Heuristic CAGR calculation routing")

    def test_heuristic_market_status(self):
        intents = _heuristic_route("Is the NSE market open right now?")
        self.assertTrue(len(intents) > 0)
        self.assertEqual(intents[0].tool_name, "MarketDateTimeTool")
        self.assertEqual(intents[0].action, "market_status")
        print("  PASS: Heuristic market status routing")

    def test_market_data_tool_execution(self):
        """Test direct execution of MarketDataTool on TCS.NS"""
        from modules.tools.market_data_tool import MarketDataTool
        tool = MarketDataTool()
        result = tool.execute({"action": "price", "symbol": "TCS.NS"})
        self.assertIn("TCS.NS", result)
        self.assertFalse(result.startswith("Error:"))
        safe_res = result[:150].encode('ascii', errors='replace').decode('ascii')
        print(f"  PASS: MarketDataTool live execution output:\n{safe_res}...")

    def test_pipeline_execution_tcs(self):
        """Test full pipeline execution: Router -> Permission -> Tool -> Answer"""
        # Mock 7B model for speed in unit test
        def mock_generate_answer(query, results, user_id="default", model_override=None):
            tool_data = results[0].data if results else ""
            return f"Verified Market Data:\n{tool_data}\n\nSummary: The current price of TCS is verified from MarketDataTool."

        pipeline = get_pipeline()
        with patch.object(pipeline, "generate_final_answer", side_effect=mock_generate_answer):
            res = pipeline.process("What is the current price of TCS?", user_tier="free")
            self.assertFalse(res.permission_denied)
            self.assertTrue(len(res.tool_results) > 0)
            self.assertEqual(res.tool_results[0].tool_name, "MarketDataTool")
            self.assertTrue(res.tool_results[0].is_valid)
            self.assertIn("TCS.NS", res.tool_results[0].data)
            self.assertIn("Verified Market Data", res.final_answer)
            print("  PASS: End-to-End Pipeline execution (User -> 3B/Heuristic -> MarketDataTool -> 7B Answer)")

if __name__ == "__main__":
    unittest.main()
