"""
Subprocess Execution Harness with Binary Allowlist and Argument Sanitization.
Eliminates shell string injection and enforces Rule 8 anti-discovery boundaries.
"""

import os
import re
import subprocess
from typing import List, Optional


class AllowlistExecutionHarness:
    """
    Executes subprocesses strictly with array arguments and shell=False.
    Blocks unapproved binaries and flags that violate Rule 8.
    """

    ALLOWED_BINARIES = {
        "git",
        "python",
        "python3",
        "node",
        "npm",
        "npx",
        "pytest",
        "tsc"
    }

    # Prohibited recursive crawling arguments
    DISCOVERY_FLAGS = re.compile(r"^(-R|--recursive|/s|-r)$", re.IGNORECASE)

    @classmethod
    def execute(
        cls,
        binary: str,
        args: List[str],
        cwd: Optional[str] = None,
        timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """
        Executes an allowlisted binary without shell interpolation.
        """
        bin_base = os.path.basename(binary).lower()
        if bin_base.endswith(".exe"):
            bin_base = bin_base[:-4]

        if bin_base not in cls.ALLOWED_BINARIES:
            raise PermissionError(f"SECURITY ALERT: Binary '{binary}' is not permitted by execution harness.")

        # Inspect flags for recursive crawling attempts
        for arg in args:
            if cls.DISCOVERY_FLAGS.match(arg):
                raise PermissionError(f"RULE 8 VIOLATION: Recursive crawling argument '{arg}' is prohibited.")

        # Execute strictly with shell=False
        return subprocess.run(
            [binary] + list(args),
            cwd=cwd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout
        )
