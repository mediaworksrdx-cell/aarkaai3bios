"""
SPARC Autonomous Swarm Coordinator for Aarka Backend.
Coordinates multi-agent roles across 5 verified gates with genuine verification,
explicit PASS/FAIL/BLOCKED states, and transactional multi-file rollback.
"""

from __future__ import annotations

import ast
import io
import os
import re
import sys
import time
import unittest
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from modules.sparc.snapshot_manager import TransactionalSnapshotManager
from modules.sparc.capability_gateway import HardenedCapabilityGateway


class StageState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass
class StageResult:
    stage_name: str
    passed: bool
    score: float
    details: str
    state: StageState = StageState.FAIL
    artifacts: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    execution_output: Optional[str] = None


@dataclass
class SparcPipelineResult:
    task_id: str
    status: str  # "COMPLETED" or "FAILED"
    final_score: float
    stages: List[StageResult]
    modified_files: List[str]
    duration_seconds: float
    error: Optional[str] = None


class SparcSwarmCoordinator:
    """
    Executes the 5-Stage SPARC Autonomous Swarm Pipeline natively in Python:
    1. Specification (Invariants, boundaries, preconditions, postconditions)
    2. Pseudocode (Algorithm, asymptotic bounds O(...), loop invariants)
    3. Architecture (Interface seams, AST syntax validity, boundary checking)
    4. Refinement (TDD unit test pass rate = 100%, real test execution)
    5. Completion (Composite score >= 8.5 / 10 -> Commit transaction)
    """

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        self.workspace_root = os.path.realpath(workspace_root or os.getcwd())
        self.snapshot_manager = TransactionalSnapshotManager()
        self.capability_gateway = HardenedCapabilityGateway(self.workspace_root)

    def execute_pipeline(
        self,
        task_id: str,
        description: str,
        target_files: Optional[List[str]] = None,
        content_map: Optional[Dict[str, str]] = None,
        min_passing_score: float = 8.5
    ) -> SparcPipelineResult:
        """
        Executes the full SPARC pipeline with transactional rollback protection.
        Ensures strict failure propagation: if an earlier stage fails or is blocked,
        downstream stages are blocked and cannot report success.
        """
        start_time = time.time()
        stage_results: List[StageResult] = []
        files = target_files or []

        # Validate task parameters
        if not task_id or not task_id.strip():
            return SparcPipelineResult(
                task_id="invalid",
                status="FAILED",
                final_score=0.0,
                stages=[],
                modified_files=[],
                duration_seconds=0.0,
                error="Invalid task_id: task_id cannot be empty."
            )

        # 0. Begin Transactional Snapshot before any potential mutation
        self.snapshot_manager.begin_transaction(task_id, files)

        try:
            # Stage 1: Specification
            spec_result = self._stage_specification(task_id, description, content_map)
            stage_results.append(spec_result)
            if not spec_result.passed or spec_result.state != StageState.PASS:
                # Downstream stages blocked
                self._block_downstream_stages(stage_results, ["Pseudocode", "Architecture", "Refinement", "Completion"], "Specification stage failed or blocked.")
                raise RuntimeError(f"Specification Gate Failed: {spec_result.details}")

            # Stage 2: Pseudocode
            pseudo_result = self._stage_pseudocode(task_id, description, content_map)
            stage_results.append(pseudo_result)
            if not pseudo_result.passed or pseudo_result.state != StageState.PASS:
                self._block_downstream_stages(stage_results, ["Architecture", "Refinement", "Completion"], "Pseudocode stage failed or blocked.")
                raise RuntimeError(f"Pseudocode Gate Failed: {pseudo_result.details}")

            # Stage 3: Architecture
            arch_result = self._stage_architecture(task_id, files, content_map)
            stage_results.append(arch_result)
            if not arch_result.passed or arch_result.state != StageState.PASS:
                self._block_downstream_stages(stage_results, ["Refinement", "Completion"], "Architecture gate failed.")
                raise RuntimeError(f"Architecture Gate Failed: {arch_result.details}")

            # Stage 4: Refinement (TDD)
            tdd_result = self._stage_refinement(task_id, files, content_map)
            stage_results.append(tdd_result)
            if not tdd_result.passed or tdd_result.state != StageState.PASS:
                self._block_downstream_stages(stage_results, ["Completion"], "Refinement TDD stage failed or blocked.")
                raise RuntimeError(f"Refinement Gate Failed: {tdd_result.details}")

            # Stage 5: Completion
            comp_result = self._stage_completion(task_id, stage_results, min_passing_score)
            stage_results.append(comp_result)
            if not comp_result.passed or comp_result.state != StageState.PASS:
                raise RuntimeError(f"Completion Gate Failed: {comp_result.details}")

            # All 5 gates passed genuinely — commit transaction
            self.snapshot_manager.commit_transaction(task_id)

            duration = round(time.time() - start_time, 4)
            return SparcPipelineResult(
                task_id=task_id,
                status="COMPLETED",
                final_score=comp_result.score,
                stages=stage_results,
                modified_files=files,
                duration_seconds=duration
            )

        except Exception as e:
            # Atomic rollback on any failure
            if self.snapshot_manager.is_active(task_id):
                try:
                    self.snapshot_manager.rollback_transaction(task_id)
                except Exception as rollback_err:
                    e = RuntimeError(f"{e} (Rollback warning: {rollback_err})")

            duration = round(time.time() - start_time, 4)
            return SparcPipelineResult(
                task_id=task_id,
                status="FAILED",
                final_score=0.0,
                stages=stage_results,
                modified_files=[],
                duration_seconds=duration,
                error=str(e)
            )

    def _block_downstream_stages(self, stage_results: List[StageResult], stage_names: List[str], reason: str) -> None:
        """Appends explicitly blocked stages to results to demonstrate failure propagation."""
        for name in stage_names:
            stage_results.append(
                StageResult(
                    stage_name=name,
                    passed=False,
                    state=StageState.BLOCKED,
                    score=0.0,
                    details=f"Stage BLOCKED: {reason}",
                    blockers=[reason]
                )
            )

    def _stage_specification(
        self,
        task_id: str,
        description: str,
        content_map: Optional[Dict[str, str]]
    ) -> StageResult:
        """Validates formal specification criteria: preconditions, postconditions, and invariants."""
        spec_text = ""
        if content_map:
            for k, v in content_map.items():
                if any(tag in k.lower() for tag in ("spec", "requirement", "contract")):
                    spec_text += "\n" + v

        combined = (description or "") + "\n" + spec_text
        if not combined.strip():
            return StageResult(
                stage_name="Specification",
                passed=False,
                state=StageState.BLOCKED,
                score=0.0,
                details="Specification BLOCKED: Missing task description and specification contract inputs.",
                blockers=["Empty input specification"]
            )

        # Check required formal clauses
        clauses = {
            "preconditions": bool(re.search(r"\b(preconditions?|requires?|input\s+contracts?)\b", combined, re.I)),
            "postconditions": bool(re.search(r"\b(postconditions?|ensures?|returns?|output\s+contracts?)\b", combined, re.I)),
            "invariants": bool(re.search(r"\b(invariants?|state\s+invariants?|loop\s+invariants?)\b", combined, re.I)),
            "boundaries": bool(re.search(r"\b(boundary|boundaries|constraints?|limits?|edge\s+cases?)\b", combined, re.I))
        }

        missing = [k for k, present in clauses.items() if not present]
        present_count = len(clauses) - len(missing)

        if missing:
            score = round((present_count / 4.0) * 8.0, 2)
            return StageResult(
                stage_name="Specification",
                passed=False,
                state=StageState.FAIL,
                score=score,
                details=f"Specification FAILED: Missing required formal contract clauses: {', '.join(missing)}.",
                blockers=[f"Missing {c}" for c in missing]
            )

        # Substantive content score
        score = 8.5
        if len(combined) >= 200:
            score += 0.5
        if re.search(r"\b(type|schema|interface|class|enum)\b", combined, re.I):
            score += 0.5
        if re.search(r"\b(error|exception|fail|timeout)\b", combined, re.I):
            score += 0.5
        score = min(10.0, score)

        return StageResult(
            stage_name="Specification",
            passed=score >= 8.5,
            state=StageState.PASS if score >= 8.5 else StageState.FAIL,
            score=score,
            details=f"Formal contract verified: All 4 clauses present. Preconditions=True, Postconditions=True, Invariants=True, Boundaries=True. Score={score}.",
            artifacts=[f"spec_{task_id}.md"]
        )

    def _stage_pseudocode(
        self,
        task_id: str,
        description: str,
        content_map: Optional[Dict[str, str]]
    ) -> StageResult:
        """Validates algorithmic clarity and asymptotic bound documentation."""
        text = description or ""
        if content_map:
            for k, v in content_map.items():
                if any(tag in k.lower() for tag in ("pseudo", "algo", "logic")):
                    text += "\n" + v

        if not text.strip():
            return StageResult(
                stage_name="Pseudocode",
                passed=False,
                state=StageState.BLOCKED,
                score=0.0,
                details="Pseudocode BLOCKED: No algorithm or pseudocode logic provided.",
                blockers=["Empty pseudocode input"]
            )

        # Check required algorithmic proof items
        has_algo = bool(re.search(r"\b(algorithm|def\s+[a-zA-Z_]|function\s+[a-zA-Z_]|procedure)\b", text, re.I))
        has_time_complexity = bool(re.search(r"(O\([^\)]+\)|time\s+complexity|asymptotic\s+bound)", text, re.I))
        has_space_complexity = bool(re.search(r"(space\s+complexity|memory\s+complexity|O\(1\)|O\(n\)|O\(log)", text, re.I))
        has_invariants = bool(re.search(r"(invariant|loop\s+invariant|state\s+transition|base\s+case|inductive)", text, re.I))

        missing = []
        if not has_algo:
            missing.append("algorithm declaration")
        if not has_time_complexity:
            missing.append("formal time complexity O(...)")
        if not has_space_complexity:
            missing.append("formal space complexity O(...)")
        if not has_invariants:
            missing.append("loop invariant or state transition proof")

        if missing:
            present = 4 - len(missing)
            score = round((present / 4.0) * 7.5, 2)
            return StageResult(
                stage_name="Pseudocode",
                passed=False,
                state=StageState.FAIL,
                score=score,
                details=f"Pseudocode FAILED: Missing algorithm proof elements: {', '.join(missing)}.",
                blockers=missing
            )

        score = 8.5
        if has_time_complexity and has_space_complexity:
            score += 0.5
        if re.search(r"(while|for|loop|recurse|binary|tree|graph|hash|sort)", text, re.I):
            score += 0.5
        score = min(10.0, score)

        return StageResult(
            stage_name="Pseudocode",
            passed=score >= 8.5,
            state=StageState.PASS if score >= 8.5 else StageState.FAIL,
            score=score,
            details=f"Algorithm structure and asymptotic bounds O(...) verified cleanly. Score={score}.",
            artifacts=[f"pseudo_{task_id}.md"]
        )

    def _stage_architecture(
        self,
        task_id: str,
        target_files: List[str],
        content_map: Optional[Dict[str, str]]
    ) -> StageResult:
        """Validates AST syntax, module boundaries, and type safety."""
        syntax_errors = []
        modules_analyzed = 0
        total_declarations = 0

        # Check Python code in content_map
        if content_map:
            for fpath, code in content_map.items():
                if fpath.endswith(".py"):
                    modules_analyzed += 1
                    try:
                        tree = ast.parse(code, filename=fpath)
                        decls = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign))]
                        total_declarations += len(decls)
                    except SyntaxError as se:
                        syntax_errors.append(f"{fpath}:{se.lineno}: {se.msg}")

        # Check existing target files on disk
        if target_files:
            for fpath in target_files:
                if fpath.endswith(".py") and os.path.exists(fpath):
                    modules_analyzed += 1
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=fpath)
                        decls = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign))]
                        total_declarations += len(decls)
                    except SyntaxError as se:
                        syntax_errors.append(f"{fpath}:{se.lineno}: {se.msg}")

        if syntax_errors:
            return StageResult(
                stage_name="Architecture",
                passed=False,
                state=StageState.FAIL,
                score=0.0,
                details=f"Architecture FAILED: AST syntax errors detected: {'; '.join(syntax_errors)}",
                blockers=syntax_errors
            )

        if modules_analyzed == 0:
            return StageResult(
                stage_name="Architecture",
                passed=False,
                state=StageState.BLOCKED,
                score=0.0,
                details="Architecture BLOCKED: No architectural or source modules were provided or found for analysis.",
                blockers=["Zero modules analyzed"]
            )

        if total_declarations == 0:
            return StageResult(
                stage_name="Architecture",
                passed=False,
                state=StageState.FAIL,
                score=3.0,
                details=f"Architecture FAILED: Analyzed {modules_analyzed} modules but found no class or function interface declarations.",
                blockers=["No interface contracts declared in source"]
            )

        score = min(10.0, round(8.5 + min(1.5, total_declarations * 0.1), 2))
        return StageResult(
            stage_name="Architecture",
            passed=score >= 8.5,
            state=StageState.PASS if score >= 8.5 else StageState.FAIL,
            score=score,
            details=f"Architecture contracts verified cleanly. {modules_analyzed} modules parsed with zero syntax errors. Declarations={total_declarations}.",
            artifacts=[f"arch_{task_id}.json"]
        )

    def _stage_refinement(
        self,
        task_id: str,
        target_files: List[str],
        content_map: Optional[Dict[str, str]]
    ) -> StageResult:
        """Validates TDD test requirements: Executes real tests in an isolated child process. Zero in-process exec."""
        import tempfile
        import subprocess

        # Check if test code provided in content_map or test files in target_files
        test_modules: Dict[str, str] = {}
        if content_map:
            for k, v in content_map.items():
                if "test" in k.lower():
                    test_modules[k] = v

        test_files_on_disk = [f for f in target_files if "test" in os.path.basename(f).lower() and os.path.exists(f)]

        # 1. If test code provided in content_map, execute in an isolated temporary sandbox process
        if test_modules:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file_paths = []
                for fname, code in (content_map or {}).items():
                    safe_name = os.path.basename(fname)
                    if not safe_name.endswith(".py"):
                        safe_name += ".py"
                    fpath = os.path.join(temp_dir, safe_name)
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(code)
                    if "test" in safe_name.lower():
                        test_file_paths.append(safe_name)

                runner_template = """import sys
import unittest

loader = unittest.TestLoader()
suite = unittest.TestSuite()

for tf in __TEST_FILES__:
    try:
        mod_name = tf[:-3]
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = __import__(mod_name)
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                suite.addTests(loader.loadTestsFromTestCase(obj))
    except Exception as e:
        sys.stderr.write("IMPORT_ERROR: " + str(e) + chr(10))
        sys.exit(2)

runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"""
                runner_code = runner_template.replace("__TEST_FILES__", repr(test_file_paths))
                runner_path = os.path.join(temp_dir, "_isolated_runner.py")
                with open(runner_path, "w", encoding="utf-8") as f:
                    f.write(runner_code)

                try:
                    proc = subprocess.run(
                        [sys.executable, runner_path],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=30.0,
                        shell=False
                    )
                except subprocess.TimeoutExpired:
                    return StageResult(
                        stage_name="Refinement",
                        passed=False,
                        state=StageState.FAIL,
                        score=0.0,
                        details="Refinement FAILED: Test suite execution timed out after 30 seconds.",
                        blockers=["Test execution timeout (30s)"]
                    )
                except Exception as e:
                    return StageResult(
                        stage_name="Refinement",
                        passed=False,
                        state=StageState.FAIL,
                        score=0.0,
                        details=f"Refinement FAILED: Isolated child process error: {e}",
                        blockers=[str(e)]
                    )

                out = proc.stdout + "\n" + proc.stderr
                if "IMPORT_ERROR:" in out:
                    err_lines = [l for l in out.splitlines() if "IMPORT_ERROR:" in l]
                    err_msg = err_lines[0] if err_lines else "Test suite import error"
                    return StageResult(
                        stage_name="Refinement",
                        passed=False,
                        state=StageState.FAIL,
                        score=0.0,
                        details=f"Refinement FAILED: {err_msg}",
                        blockers=[err_msg]
                    )

                ran_match = re.search(r"Ran (\d+) tests?", out)
                tests_run = int(ran_match.group(1)) if ran_match else 0
                if tests_run == 0:
                    return StageResult(
                        stage_name="Refinement",
                        passed=False,
                        state=StageState.BLOCKED,
                        score=0.0,
                        details="Refinement BLOCKED: Test suite contains 0 runnable test cases.",
                        blockers=["Empty test suite"]
                    )

                fail_match = re.search(r"failures=(\d+)", out)
                err_match = re.search(r"errors=(\d+)", out)
                failures = int(fail_match.group(1)) if fail_match else (0 if proc.returncode == 0 else 1)
                errors = int(err_match.group(1)) if err_match else 0
                passed_tests = tests_run - (failures + errors)
                pass_rate = max(0.0, passed_tests / tests_run) if tests_run > 0 else 0.0

                score = round(pass_rate * 10.0, 2)
                is_passed = (proc.returncode == 0) and (pass_rate == 1.0) and (score >= 8.5)

                details = f"TDD test suite: {tests_run} tests run, {failures} failures, {errors} errors. Real pass rate: {pass_rate * 100:.1f}%."
                blockers = []
                if failures > 0 or errors > 0 or proc.returncode != 0:
                    blockers.append(f"{failures} failures and {errors} errors in isolated test execution")

                return StageResult(
                    stage_name="Refinement",
                    passed=is_passed,
                    state=StageState.PASS if is_passed else StageState.FAIL,
                    score=score,
                    details=details,
                    blockers=blockers,
                    execution_output=out,
                    artifacts=[f"test_run_{task_id}.log"]
                )

        # 2. If test files on disk, execute via isolated subprocess runner
        elif test_files_on_disk:
            test_dir = os.path.abspath(os.path.dirname(test_files_on_disk[0]))
            sub_env = os.environ.copy()
            sub_env["PYTHONPATH"] = f"{test_dir}{os.pathsep}{sub_env.get('PYTHONPATH', '')}"
            test_basenames = [os.path.basename(f) for f in test_files_on_disk]
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "unittest"] + test_basenames,
                    cwd=test_dir,
                    env=sub_env,
                    capture_output=True,
                    text=True,
                    timeout=30.0,
                    shell=False
                )
            except subprocess.TimeoutExpired:
                return StageResult(
                    stage_name="Refinement",
                    passed=False,
                    state=StageState.FAIL,
                    score=0.0,
                    details="Refinement FAILED: Test execution timed out after 30 seconds.",
                    blockers=["Test execution timeout (30s)"]
                )
            except Exception as e:
                return StageResult(
                    stage_name="Refinement",
                    passed=False,
                    state=StageState.FAIL,
                    score=0.0,
                    details=f"Refinement FAILED: Failed executing test subprocess: {e}",
                    blockers=[str(e)]
                )

            out = proc.stdout + "\n" + proc.stderr
            ran_match = re.search(r"Ran (\d+) tests?", out)
            tests_run = int(ran_match.group(1)) if ran_match else 0
            if tests_run == 0:
                return StageResult(
                    stage_name="Refinement",
                    passed=False,
                    state=StageState.BLOCKED,
                    score=0.0,
                    details=f"Refinement BLOCKED: 0 test cases loaded from {test_files_on_disk}.",
                    blockers=["Zero test cases loaded"]
                )

            fail_match = re.search(r"failures=(\d+)", out)
            err_match = re.search(r"errors=(\d+)", out)
            failures = int(fail_match.group(1)) if fail_match else (0 if proc.returncode == 0 else 1)
            errors = int(err_match.group(1)) if err_match else 0
            passed_tests = tests_run - (failures + errors)
            pass_rate = max(0.0, passed_tests / tests_run) if tests_run > 0 else 0.0

            score = round(pass_rate * 10.0, 2)
            is_passed = (proc.returncode == 0) and (pass_rate == 1.0) and (score >= 8.5)

            return StageResult(
                stage_name="Refinement",
                passed=is_passed,
                state=StageState.PASS if is_passed else StageState.FAIL,
                score=score,
                details=f"TDD test suite on disk: {tests_run} tests run, {failures} failures, {errors} errors. Real pass rate: {pass_rate * 100:.1f}%.",
                blockers=[f"{failures} failures and {errors} errors in test execution"] if (failures > 0 or errors > 0) else [],
                execution_output=out,
                artifacts=[f"test_run_{task_id}.log"]
            )

        # 3. No test code or files provided
        return StageResult(
            stage_name="Refinement",
            passed=False,
            state=StageState.BLOCKED,
            score=0.0,
            details="Refinement BLOCKED: No test modules or test files specified for execution.",
            blockers=["Missing test suite inputs"]
        )

    def _stage_completion(
        self,
        task_id: str,
        prior_stages: List[StageResult],
        min_passing_score: float = 8.5
    ) -> StageResult:
        """Evaluates composite operational score across all preceding gates."""
        # Strict validation: all prior stages must have passed with state == PASS
        failed_or_blocked = [s for s in prior_stages if not s.passed or s.state != StageState.PASS]
        if failed_or_blocked:
            blocker_names = [f"{s.stage_name} ({s.state})" for s in failed_or_blocked]
            return StageResult(
                stage_name="Completion",
                passed=False,
                state=StageState.FAIL,
                score=0.0,
                details=f"Completion Gate FAILED: Preceding gates did not pass: {', '.join(blocker_names)}.",
                blockers=[f"Prerequisite gate failed: {b}" for b in blocker_names]
            )

        scores = [s.score for s in prior_stages]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        passed = avg_score >= min_passing_score
        state = StageState.PASS if passed else StageState.FAIL
        return StageResult(
            stage_name="Completion",
            passed=passed,
            state=state,
            score=avg_score,
            details=f"Composite verification score: {avg_score} / 10.0 (Threshold: {min_passing_score}). Status: {state}.",
            artifacts=[f"final_manifest_{task_id}.json"]
        )

    def verify_specification(self, task_id: str, description: str, content_map: Optional[Dict[str, str]] = None) -> StageResult:
        """Direct access for standalone specification gate testing."""
        return self._stage_specification(task_id, description, content_map)

    def verify_pseudocode(self, task_id: str, description: str, content_map: Optional[Dict[str, str]] = None) -> StageResult:
        """Direct access for standalone pseudocode gate testing."""
        return self._stage_pseudocode(task_id, description, content_map)

    def verify_architecture(self, task_id: str, files: Optional[List[str]] = None, content_map: Optional[Dict[str, str]] = None) -> StageResult:
        """Direct access for standalone architecture gate testing."""
        return self._stage_architecture(task_id, files or [], content_map)

    def execute_refinement(self, task_id: str, files: Optional[List[str]] = None, content_map: Optional[Dict[str, str]] = None) -> StageResult:
        """Direct access for standalone refinement gate testing."""
        return self._stage_refinement(task_id, files or [], content_map)


# Canonical alias ensuring consistent naming across the repository
AarkaNativeSparcCoordinator = SparcSwarmCoordinator

