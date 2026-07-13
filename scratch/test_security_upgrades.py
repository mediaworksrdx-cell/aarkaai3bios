import unittest
import sys
import os
from pathlib import Path

# Append project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.permissions import verify_permission, PermissionLevel
from modules.tools.fs import _resolve_safe_path
from modules.execution_engine import check_python_script_safety

class TestSecurityUpgrades(unittest.TestCase):

    def test_command_chaining(self):
        # Chaining operators should be strictly blocked in custom execution paths
        level, msg = verify_permission("BashTool", {"command": "python3 build.py && rm -rf /"})
        self.assertEqual(level, PermissionLevel.STRICT_BLOCK)
        # Should be blocked (either by blocklist pattern or chaining operator check)

        # Pure chaining without blocklist command — should still be blocked
        level, msg = verify_permission("BashTool", {"command": "python3 build.py && python3 other.py"})
        self.assertEqual(level, PermissionLevel.STRICT_BLOCK)
        self.assertIn("chaining", msg.lower())

        # Safe read operations with | are allowed since they match safe_bash_patterns
        level, msg = verify_permission("BashTool", {"command": "cat test.txt"})
        self.assertEqual(level, PermissionLevel.AUTO_ALLOW)

    def test_symlink_traversal(self):
        # Set up safe workspace dir representation
        from config import SAFE_WORK_DIR
        # Creating a temporary file that is outside the workspace to simulate symlink target
        outside_file = SAFE_WORK_DIR.parent / "outside_secret.txt"
        outside_file.write_text("secret_data")
        
        # Creating a symlink inside the workspace pointing to the outside file
        symlink_path = SAFE_WORK_DIR / "unsafe_link.txt"
        if not symlink_path.exists():
            try:
                os.symlink(outside_file, symlink_path)
            except Exception:
                # Windows might require admin privileges for symlinks, skip if failed
                pass

        if symlink_path.exists():
            # Reading the symlink should fail due to blocked symlinks
            with self.assertRaises(ValueError):
                _resolve_safe_path("unsafe_link.txt")
            
            # Cleanup
            os.remove(symlink_path)
            
        if outside_file.exists():
            os.remove(outside_file)

    def test_ast_script_safety(self):
        from config import SAFE_WORK_DIR
        
        # Write a dangerous python script with nested subprocess call
        danger_script = SAFE_WORK_DIR / "danger.py"
        danger_script.write_text("import subprocess\nsubprocess.run(['ls'])")
        
        # Check safety
        ok, msg = check_python_script_safety("python danger.py")
        self.assertFalse(ok)
        self.assertIn("Blocked import: 'subprocess'", msg)
        
        # Write a safe python script
        safe_script = SAFE_WORK_DIR / "safe_run.py"
        safe_script.write_text("print('Hello World')")
        
        ok, msg = check_python_script_safety("python safe_run.py")
        self.assertTrue(ok)
        
        # Cleanup
        if danger_script.exists():
            os.remove(danger_script)
        if safe_script.exists():
            os.remove(safe_script)

if __name__ == "__main__":
    # Ensure workspace directory exists for testing
    from config import SAFE_WORK_DIR
    SAFE_WORK_DIR.mkdir(parents=True, exist_ok=True)
    unittest.main()
