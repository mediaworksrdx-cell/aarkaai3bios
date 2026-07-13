import unittest
import sys
import os

# Append project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.context_compaction import clean_ansi_escapes, truncate_source_code_buffers, semantic_deduplicate
from modules.permissions import verify_permission, PermissionLevel

class TestContextCompaction(unittest.TestCase):
    def test_clean_ansi_escapes(self):
        text = "Hello \x1b[31mRed\x1b[0m World! [========>] 50%"
        self.assertEqual(clean_ansi_escapes(text).strip(), "Hello Red World!")

    def test_truncate_source_code_buffers(self):
        # 10 lines
        lines = [f"Line {i}" for i in range(10)]
        text = "\n".join(lines)
        truncated = truncate_source_code_buffers(text, max_lines=4)
        self.assertIn("Truncated", truncated)
        self.assertEqual(len(truncated.splitlines()), 5) # 2 start + 1 message + 2 end

    def test_semantic_deduplicate(self):
        text = "line1\nline1\nline2\nline2\nline3"
        self.assertEqual(semantic_deduplicate(text), "line1\nline2\nline3")

class TestPermissionVerification(unittest.TestCase):
    def test_auto_allow(self):
        # FileReadTool should be auto-allowed
        level, msg = verify_permission("FileReadTool", {"path": "test.txt"})
        self.assertEqual(level, PermissionLevel.AUTO_ALLOW)

        # Safe bash commands should be auto-allowed
        level, msg = verify_permission("BashTool", {"command": "git status"})
        self.assertEqual(level, PermissionLevel.AUTO_ALLOW)

    def test_strict_block(self):
        # Destructive commands should be strictly blocked
        level, msg = verify_permission("BashTool", {"command": "rm -rf /"})
        self.assertEqual(level, PermissionLevel.STRICT_BLOCK)

        level, msg = verify_permission("BashTool", {"command": "git push origin main"})
        self.assertEqual(level, PermissionLevel.STRICT_BLOCK)

    def test_user_confirm(self):
        # Modifying files or custom scripts should require confirm
        level, msg = verify_permission("FileEditTool", {"path": "test.py", "content": "print(1)"})
        self.assertEqual(level, PermissionLevel.USER_CONFIRM)

        level, msg = verify_permission("BashTool", {"command": "python3 script.py"})
        self.assertEqual(level, PermissionLevel.USER_CONFIRM)

if __name__ == "__main__":
    unittest.main()
