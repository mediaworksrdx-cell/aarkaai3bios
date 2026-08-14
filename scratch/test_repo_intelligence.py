import unittest
import os
import sys
import shutil

# Ensure modules package can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.repo_indexer import WorkspaceSnapshot, RepoGraphStore, LanguageAdapter
from modules.repair_agents import RepairConfidenceScorer, ChainedRepairController

class TestRepoIntelligence(unittest.TestCase):
    
    def test_workspace_snapshot(self):
        # Create a mock file
        test_file = "cvr_runner_tmp.py"
        test_path = os.path.join(os.getcwd(), test_file)
        
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("print('original content')")
            
        snapshot_id = "snap_test_run"
        # Snapshot the file
        self.assertTrue(WorkspaceSnapshot.create_snapshot(snapshot_id, [test_file]))
        
        # Modify the mock file
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("print('modified content')")
            
        # Restore snapshot
        self.assertTrue(WorkspaceSnapshot.restore_snapshot(snapshot_id))
        
        # Assert content was reverted
        with open(test_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "print('original content')")
        
        # Cleanup mock file and discard snapshot
        if os.path.exists(test_path):
            os.remove(test_path)
        WorkspaceSnapshot.discard_snapshot(snapshot_id)

    def test_repo_graph_store(self):
        RepoGraphStore.initialize_db()
        RepoGraphStore.add_node("cvr_pipeline", "module")
        RepoGraphStore.add_node("verifier", "module")
        RepoGraphStore.add_edge("verifier", "cvr_pipeline", "CALLS")
        
        callers = RepoGraphStore.find_callers("cvr_pipeline")
        self.assertIn("verifier", callers)

    def test_language_adapter_python(self):
        py_code = (
            "@decorator_test\n"
            "class MyTestClass:\n"
            "    pass\n\n"
            "def test_func() -> str:\n"
            "    return 'test'\n"
        )
        symbols = LanguageAdapter.parse_python_ast(py_code, "test.py")
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0]["name"], "MyTestClass")
        self.assertEqual(symbols[1]["name"], "test_func")

    def test_chained_repair_logic(self):
        # Snippet containing a syntax failure (missing closed bracket)
        broken_syntax_code = "def buggy_func():\n    return 'test'("
        res = ChainedRepairController.attempt_chained_repair("fix functional logic", broken_syntax_code, "assert True", max_iterations=2)
        self.assertTrue(res["success"])
        self.assertIn("buggy_func()", res["repaired_code"])


if __name__ == "__main__":
    unittest.main()
