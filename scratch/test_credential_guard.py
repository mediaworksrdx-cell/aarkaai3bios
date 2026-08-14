import unittest
import os
import sys

# Ensure modules package can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cvr_pipeline import ToolRouter

class TestCredentialGuard(unittest.TestCase):
    
    def test_git_credential_interception(self):
        # Mock code execution that prints a simulated Git connection error to stderr
        simulated_git_err = (
            "import sys\n"
            "sys.stderr.write('ssh: connect to host github.com port 22: Connection timed out\\r\\n')\n"
            "sys.stderr.write('fatal: Could not read from remote repository.\\r\\n\\r\\n')\n"
            "sys.stderr.write('Please make sure you have the correct access rights and the repository exists.\\r\\n')\n"
            "sys.exit(1)"
        )
        
        result = ToolRouter.run_test_script(simulated_git_err, "assert True")
        self.assertFalse(result["passed"])
        self.assertTrue(result.get("requires_credentials", False))
        self.assertIn("Git connection failed", result["stderr"])
        self.assertIn("configure a Personal Access Token", result["stderr"])

if __name__ == "__main__":
    unittest.main()
