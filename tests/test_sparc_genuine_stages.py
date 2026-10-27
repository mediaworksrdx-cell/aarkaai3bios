"""
SPARC Orchestration Stage Verification & Failure Propagation Test Suite.
Verifies genuine Specification, Pseudocode, Architecture, Refinement, and Completion gates,
real test execution metrics, and strict downstream failure propagation.
Zero hardcoded scores or fake coverage.
"""

import os
import pytest
from modules.sparc.coordinator import (
    AarkaNativeSparcCoordinator,
    SparcSwarmCoordinator,
    StageState,
    StageResult,
    SparcPipelineResult,
)


@pytest.fixture
def sparc_workspace(tmp_path):
    ws = tmp_path / "sparc_ws"
    ws.mkdir()

    # 1. Valid specification
    spec_text = (
        "# SPECIFICATION: Binary Search\n"
        "## PRECONDITIONS\nInput array A must be sorted in ascending order.\n"
        "## POSTCONDITIONS\nReturns index i such that A[i] == target, or -1 if target not in A.\n"
        "## INVARIANTS\nSearch range [low, high] always bounds target if present.\n"
        "## BOUNDARIES\nArray length from 0 to 10^7 elements.\n"
    )

    # 2. Valid pseudocode
    pseudo_text = (
        "# PSEUDOCODE: Binary Search\n"
        "## ALGORITHM\n"
        "while low <= high:\n"
        "    mid = low + (high - low) // 2\n"
        "    if A[mid] == target: return mid\n"
        "## COMPLEXITY\n"
        "Time Complexity: O(log n)\n"
        "Space Complexity: O(1)\n"
        "## LOOP INVARIANT\n"
        "If target is in A, target is in A[low..high].\n"
    )

    # 3. Valid architecture file
    arch_file = ws / "module_arch.py"
    arch_file.write_text(
        "from typing import Protocol, List\n"
        "class SearchInterface(Protocol):\n"
        "    def search(self, a: List[int], target: int) -> int:\n"
        "        pass\n",
        encoding="utf-8"
    )

    # 4. Source file
    src_file = ws / "search_impl.py"
    src_file.write_text(
        "def binary_search(arr, target):\n"
        "    low, high = 0, len(arr) - 1\n"
        "    while low <= high:\n"
        "        mid = (low + high) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        elif arr[mid] < target:\n"
        "            low = mid + 1\n"
        "        else:\n"
        "            high = mid - 1\n"
        "    return -1\n",
        encoding="utf-8"
    )

    # 5. Passing test file
    test_file = ws / "test_search.py"
    test_file.write_text(
        "import unittest\n"
        "from search_impl import binary_search\n"
        "class TestSearch(unittest.TestCase):\n"
        "    def test_found(self):\n"
        "        self.assertEqual(binary_search([1, 2, 3, 4, 5], 3), 2)\n"
        "    def test_not_found(self):\n"
        "        self.assertEqual(binary_search([1, 2, 3, 4, 5], 99), -1)\n"
        "    def test_empty(self):\n"
        "        self.assertEqual(binary_search([], 1), -1)\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n",
        encoding="utf-8"
    )

    return {
        "ws": str(ws),
        "spec_text": spec_text,
        "pseudo_text": pseudo_text,
        "arch_file": str(arch_file),
        "src_file": str(src_file),
        "test_file": str(test_file),
    }


def test_specification_gate_genuine_success(sparc_workspace):
    """Verifies valid 4-clause specification passes with PASS state."""
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.verify_specification(
        task_id="task_spec_pass",
        description=sparc_workspace["spec_text"]
    )
    assert res.state == StageState.PASS
    assert res.passed is True
    assert res.score >= 8.5
    assert len(res.blockers) == 0


def test_specification_gate_missing_clause_fails(sparc_workspace):
    """Verifies that missing INVARIANTS clause results in FAIL state."""
    bad_spec = (
        "# SPECIFICATION\n## PRECONDITIONS\nValid input.\n"
        "## POSTCONDITIONS\nDone.\n## BOUNDARIES\nArray size bounded.\n"
    )
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.verify_specification(
        task_id="task_spec_fail",
        description=bad_spec
    )
    assert res.state == StageState.FAIL
    assert res.passed is False
    assert any("invariants" in b.lower() for b in res.blockers)


def test_specification_gate_empty_input_blocks(sparc_workspace):
    """Verifies that empty specification inputs result in BLOCKED state."""
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.verify_specification(
        task_id="task_spec_blocked",
        description=""
    )
    assert res.state == StageState.BLOCKED
    assert res.passed is False


def test_pseudocode_gate_genuine_success(sparc_workspace):
    """Verifies pseudocode with algorithm, asymptotic bounds, and invariant passes."""
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.verify_pseudocode(
        task_id="task_pseudo_pass",
        description=sparc_workspace["pseudo_text"]
    )
    assert res.state == StageState.PASS
    assert res.passed is True
    assert res.score >= 8.5


def test_pseudocode_gate_missing_asymptotic_bound_fails(sparc_workspace):
    """Verifies that missing O(...) complexity bound causes FAIL state."""
    bad_pseudo = "# PSEUDOCODE\n## ALGORITHM\nDo loop.\n## LOOP INVARIANT\ni <= n\n"
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.verify_pseudocode(
        task_id="task_pseudo_fail",
        description=bad_pseudo
    )
    assert res.state == StageState.FAIL
    assert res.passed is False
    assert any("complexity" in b.lower() for b in res.blockers)


def test_architecture_gate_genuine_ast_validation(sparc_workspace):
    """Verifies architecture contracts validated with Python AST."""
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.verify_architecture(
        task_id="task_arch_pass",
        files=[sparc_workspace["arch_file"]]
    )
    assert res.state == StageState.PASS
    assert res.passed is True

    # Test syntax error in architecture file
    bad_arch = os.path.join(sparc_workspace["ws"], "syntax_err.py")
    with open(bad_arch, "w", encoding="utf-8") as f:
        f.write("def broken_syntax(:\n")

    bad_res = coord.verify_architecture(
        task_id="task_arch_syntax_err",
        files=[bad_arch]
    )
    assert bad_res.state == StageState.FAIL
    assert bad_res.passed is False


def test_refinement_gate_genuine_test_execution(sparc_workspace):
    """Verifies refinement executes genuine tests with real pass rate."""
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    res = coord.execute_refinement(
        task_id="task_refine_pass",
        files=[sparc_workspace["src_file"], sparc_workspace["test_file"]]
    )
    assert res.state == StageState.PASS
    assert res.passed is True
    assert res.score >= 8.5


def test_failure_propagation_blocks_downstream_stages(sparc_workspace):
    """Verifies that an early stage failure immediately blocks all downstream stages."""
    coord = AarkaNativeSparcCoordinator(workspace_root=sparc_workspace["ws"])
    bad_spec = "Not enough contract clauses"

    result = coord.execute_pipeline(
        task_id="task_fail_prop",
        description=bad_spec,
        target_files=[sparc_workspace["src_file"], sparc_workspace["test_file"]]
    )
    assert result.status == "FAILED"
    stage_map = {s.stage_name: s for s in result.stages}

    assert stage_map["Specification"].state == StageState.FAIL
    # Verify all subsequent stages are explicitly BLOCKED
    assert stage_map["Pseudocode"].state == StageState.BLOCKED
    assert stage_map["Architecture"].state == StageState.BLOCKED
    assert stage_map["Refinement"].state == StageState.BLOCKED
    assert stage_map["Completion"].state == StageState.BLOCKED
