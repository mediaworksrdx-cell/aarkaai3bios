import unittest
import os
import sys

# Ensure modules package can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cvr_pipeline import StaticAnalyzer, SecurityScanner, PerformanceAnalyzer, CandidateTournament, DynamicPlanner

class TestCVRPipeline(unittest.TestCase):
    
    def test_syntax_analyzer(self):
        valid_code = "def hello():\n    return 'world'"
        invalid_code = "def hello(\n    return 'world'"
        
        self.assertTrue(StaticAnalyzer.verify_syntax(valid_code)["valid"])
        self.assertFalse(StaticAnalyzer.verify_syntax(invalid_code)["valid"])
        
    def test_security_scanner(self):
        unsafe_code = "import subprocess\nsubprocess.run('ls', shell=True)"
        safe_code = "print('Hello World')"
        
        self.assertTrue(len(SecurityScanner.scan(unsafe_code)) > 0)
        self.assertEqual(len(SecurityScanner.scan(safe_code)), 0)
        
    def test_performance_analyzer(self):
        nested_loops = "for i in range(10):\n    for j in range(10):\n        for k in range(10):\n            print(i, j, k)"
        simple_code = "print('Fast')"
        
        self.assertTrue(PerformanceAnalyzer.analyze(nested_loops)["nested_loop_depth"] >= 3)
        self.assertEqual(PerformanceAnalyzer.analyze(simple_code)["nested_loop_depth"], 0)

    def test_dynamic_planner(self):
        config_complex = DynamicPlanner.plan_complexity("Optimize SQL queries and refactor the code")
        config_simple = DynamicPlanner.plan_complexity("Print syntax layout structure")
        
        self.assertEqual(config_complex["candidate_budget"], 4)
        self.assertEqual(config_simple["candidate_budget"], 1)

    def test_verifier_cvr_integration(self):
        from modules.agents.verifier import verify_response
        import sqlite3
        
        # Proposed response with synthetic code block and a security leak (shell=True)
        response_input = (
            "Here is the code output:\n"
            "```python\n"
            "import subprocess\n"
            "subprocess.run('ls', shell=True)\n"
            "```"
        )
        
        # Execute verification pass
        verify_response("Refactor and optimize the execution logic", response_input)
        
        # Verify a record was entered in SQLite trajectories
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aarkaai.db")
        self.assertTrue(os.path.exists(db_path))
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT query, code, success, logs FROM cvr_trajectories ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertIn("optimize", row[0].lower())
        self.assertEqual(row[2], 0) # Failed CVR security check
        self.assertIn("Vulnerability", row[3])

if __name__ == "__main__":
    unittest.main()

