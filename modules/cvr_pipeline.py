import ast
import json
import logging
import re
import time
import subprocess
import os
import sys
from typing import Dict, Any, List, Optional
import sqlite3

logger = logging.getLogger(__name__)

# Constants
SAFE_WORK_DIR = os.getcwd()
DB_PATH = os.path.join(SAFE_WORK_DIR, "aarkaai.db")

class RepoIndex:
    """Provides basic AST dependency tracking and import maps for verification."""
    @staticmethod
    def analyze_imports(code: str) -> List[str]:
        try:
            tree = ast.parse(code)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            return imports
        except Exception:
            return []

class StaticAnalyzer:
    """Checks AST structure and alerts on syntax failures."""
    @staticmethod
    def verify_syntax(code: str) -> Dict[str, Any]:
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": {
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text,
                    "msg": e.msg
                }
            }

class SecurityScanner:
    """Scans code for common vulnerability signatures (injection, leaks) using AST analysis."""
    @staticmethod
    def scan(code: str) -> List[str]:
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Analyze Call nodes
                if isinstance(node, ast.Call):
                    # Resolve function name / module name
                    func_name = ""
                    module_name = ""
                    if isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                        if isinstance(node.func.value, ast.Name):
                            module_name = node.func.value.id
                    elif isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    
                    # Detect subprocess calls
                    if (module_name == "subprocess" or func_name in ["subprocess", "Popen", "call", "check_call", "check_output", "run"]) and func_name in ["run", "Popen", "call", "check_call", "check_output"]:
                        # Look for shell=True kwarg
                        for kw in node.keywords:
                            if kw.arg == "shell":
                                if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    issues.append(f"Vulnerability: subprocess.{func_name} call with shell=True is dangerous.")
                                elif isinstance(kw.value, ast.Name) and kw.value.id == "True":
                                    issues.append(f"Vulnerability: subprocess.{func_name} call with shell=True is dangerous.")
                    
                    # Detect os.system and os.popen
                    if module_name == "os" and func_name in ["system", "popen"]:
                        issues.append(f"Vulnerability: os.{func_name} call is dangerous and prone to command injection.")
                    elif func_name in ["system", "popen"] and not module_name:
                        issues.append(f"Vulnerability: {func_name} call is dangerous and prone to command injection.")
        except Exception as e:
            # Fallback to regex if parsing fails due to syntax error in the intermediate step
            if re.search(r"subprocess\.(run|Popen|call|check_call|check_output)\(.*shell\s*=\s*True", code) or "shell=True" in code:
                issues.append("Vulnerability: subprocess call with shell=True is dangerous.")
            if re.search(r"os\.(system|popen)\(", code) or re.search(r"\b(system|popen)\(", code):
                issues.append("Vulnerability: os command execution call is dangerous.")
                
        # Check basic SQL injection
        if re.search(r"execute\s*\(\s*['\"].*%\s*\w+['\"]", code) or re.search(r"execute\s*\(\s*f['\"].*\{\w+\}", code):
            if "select" in code.lower() or "insert" in code.lower() or "update" in code.lower():
                issues.append("Vulnerability: Potential raw SQL injection detected.")
        # Check hardcoded secrets
        if re.search(r"(api_key|password|secret_key|token)\s*=\s*['\"][a-zA-Z0-9_-]{16,}['\"]", code, re.IGNORECASE):
            issues.append("Vulnerability: Hardcoded credential or API secret key pattern found.")
        return issues

class PerformanceAnalyzer:
    """Statically checks for high complexity, large loops, or redundant string splits."""
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        nested_depth = 0
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    depth = 1
                    parent = node
                    # Walk up or find nested loop nodes
                    for child in ast.walk(parent):
                        if child is not parent and isinstance(child, (ast.For, ast.While)):
                            depth += 1
                    nested_depth = max(nested_depth, depth)
        except Exception:
            pass
        
        score = 100 - (nested_depth * 10)
        return {
            "complexity_score": max(50, score),
            "nested_loop_depth": nested_depth,
            "warnings": ["Performance: Nested loops may impact performance."] if nested_depth > 2 else []
        }

class ToolRouter:
    """Standardized entry point for running generated unit tests in a subprocess."""
    @staticmethod
    def run_test_script(code_to_test: str, test_code: str) -> Dict[str, Any]:
        # Intercept and block commands if they look like unauthenticated remote git calls
        git_auth_patterns = [
            "permission denied (publickey)",
            "could not read from remote repository",
            "repository not found"
        ]
        
        # Statically inspect code for problematic git operations prior to execution
        lower_code = code_to_test.lower()
        if "git" in lower_code and any(p in lower_code for p in ["clone", "push", "pull"]):
            # Run quick dry check logic
            logger.info("ToolRouter: Intercepting git network command. Running credential check.")
            
        runner_content = f"{code_to_test}\n\n{test_code}"
        temp_file = os.path.join(SAFE_WORK_DIR, "cvr_runner_tmp.py")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(runner_content)
            
            py_exe = sys.executable
            sub_env = os.environ.copy()
            sub_env["PYTHONPATH"] = SAFE_WORK_DIR
            
            start_time = time.time()
            result = subprocess.run(
                [py_exe, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                cwd=SAFE_WORK_DIR,
                env=sub_env
            )
            duration = time.time() - start_time
            
            # Intercept stdout/stderr for git credential failures
            combined_out = (result.stdout + "\n" + result.stderr).lower()
            for pattern in git_auth_patterns:
                if pattern in combined_out:
                    return {
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": f"Authentication Failure: Git connection failed. Please register your GitHub SSH keys or configure a Personal Access Token (PAT). Details: {result.stderr.strip()}",
                        "duration": duration,
                        "passed": False,
                        "requires_credentials": True
                    }
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "passed": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Error: Execution timed out after 10 seconds.",
                "duration": 10.0,
                "passed": False
            }
        except Exception as exc:
            return {
                "exit_code": -2,
                "stdout": "",
                "stderr": f"Error: {exc}",
                "duration": 0.0,
                "passed": False
            }
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass


class CandidateTournament:
    """Evaluates multiple candidates against AST syntax, security, performance, and testing benchmarks."""
    @classmethod
    def evaluate_candidates(cls, candidates: List[str], test_suite: str) -> List[Dict[str, Any]]:
        scored_candidates = []
        for index, code in enumerate(candidates):
            syntax_check = StaticAnalyzer.verify_syntax(code)
            sec_issues = SecurityScanner.scan(code)
            perf = PerformanceAnalyzer.analyze(code)
            
            # Default scoring criteria weights
            syntax_score = 100 if syntax_check["valid"] else 0
            sec_score = max(0, 100 - (len(sec_issues) * 35))
            perf_score = perf["complexity_score"]
            
            # Execute test suite run
            test_run = {"passed": False, "duration": 0.0, "stderr": "No execution (failed syntax check)"}
            if syntax_check["valid"] and test_suite.strip():
                test_run = ToolRouter.run_test_script(code, test_suite)
                
            test_score = 100 if test_run["passed"] else 0
            overall_score = (syntax_score * 0.3) + (sec_score * 0.25) + (perf_score * 0.15) + (test_score * 0.3)
            
            scored_candidates.append({
                "candidate_index": index,
                "code": code,
                "syntax_valid": syntax_check["valid"],
                "security_issues": sec_issues,
                "performance": perf,
                "test_passed": test_run["passed"],
                "test_stderr": test_run.get("stderr", ""),
                "score": overall_score
            })
            
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates

class TrajectoryLogger:
    """Observability logger recording evaluation parameters directly to SQLite database."""
    @staticmethod
    def log_trajectory(query: str, code: str, success: bool, score: float, logs: str) -> None:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cvr_trajectories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    query TEXT,
                    code TEXT,
                    success INTEGER,
                    score REAL,
                    logs TEXT
                )
            """)
            cursor.execute(
                "INSERT INTO cvr_trajectories (query, code, success, score, logs) VALUES (?, ?, ?, ?, ?)",
                (query, code, 1 if success else 0, score, logs)
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error("Failed to write to learning database: %s", exc)

class DynamicPlanner:
    """Analyzes query complexity to determine the execution budget and toggle pipeline stages."""
    @staticmethod
    def plan_complexity(query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        if "refactor" in query_lower or "optimize" in query_lower or "performance" in query_lower:
            return {"candidate_budget": 4, "run_security": True, "run_perf": True}
        if "simple" in query_lower or "syntax" in query_lower or "format" in query_lower:
            return {"candidate_budget": 1, "run_security": False, "run_perf": False}
        # Default fallback config
        return {"candidate_budget": 2, "run_security": True, "run_perf": True}
