import unittest
import os
import sys

# Ensure modules directory path can be resolved correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from modules import goal_planner
from modules import supervisor
from modules import task_memory
from modules import execution_engine
import database

class TestAutonomousAgentPlatform(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Build mock database tables
        database.init_db()
        
    def test_planner_cache_hit(self):
        query = "Research NVIDIA corporate indicators"
        cache_dag = goal_planner.check_cache(query)
        self.assertIsNotNone(cache_dag)
        self.assertEqual(cache_dag["goal"], "Conduct detailed analysis on NVIDIA")
        self.assertEqual(len(cache_dag["tasks"]), 4)

    def test_supervisor_loop_prevention(self):
        super_inst = supervisor.Supervisor()
        task_id = "t1"
        tool_name = "WebSearch"
        params = {"query": "NVIDIA financial numbers"}
        
        # Simulating consecutive requests
        self.assertFalse(super_inst.check_loop(task_id, tool_name, params))
        self.assertFalse(super_inst.check_loop(task_id, tool_name, params))
        self.assertFalse(super_inst.check_loop(task_id, tool_name, params))
        self.assertTrue(super_inst.check_loop(task_id, tool_name, params))

    def test_persistence_task_lifecycle(self):
        plan = {
            "goal": "Test lifecycle",
            "tasks": [
                {
                    "id": "t1",
                    "name": "General Execution Task",
                    "description": "Read file",
                    "tool_hint": "FileReadTool",
                    "dependencies": [],
                    "exit_criteria": "Task execution output received",
                    "retry_budget": 2,
                    "approval_required": False,
                    "status": "pending"
                }
            ]
        }
        
        gid = task_memory.save_goal("test_user", "default_session", "Test lifecycle", plan)
        self.assertGreater(gid, 0)
        
        goal_data = task_memory.get_goal(gid)
        self.assertEqual(goal_data["status"], "pending")
        
        # Test engine completion tracking (mocking tool results)
        res = execution_engine.execute(plan, gid, "test_user", "default_session")
        self.assertIsNotNone(res)

if __name__ == "__main__":
    unittest.main()
