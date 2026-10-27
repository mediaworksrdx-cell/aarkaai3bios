"""
Ruflo Integration & Swarm Coordinator Verification Test Suite.
Verifies live runtime probe against real installed CLI (ruflo v3.63.4), real health checks,
fallback isolation when absent, and zero mislabeling of custom coordinators.
"""

import os
from unittest.mock import patch, MagicMock
import pytest

from modules.sparc.ruflo_adapter import (
    probe_ruflo_runtime,
    RufloIntegrationMode,
    RufloCoordinator,
    OrchestratorFactory,
)
from modules.sparc.coordinator import AarkaNativeSparcCoordinator


def test_live_ruflo_runtime_probe_and_execution():
    """
    LIVE INTEGRATION TEST (Zero mocks):
    Verifies that the actual local Ruflo CLI is discovered, reports version 3.63.4,
    and runs system health diagnostics. If Ruflo is not installed in the environment,
    skips gracefully reporting the authoritative blocker reason.
    """
    status = probe_ruflo_runtime()
    if not status.is_installed:
        pytest.skip(f"Ruflo runtime unavailable in this environment: {status.blocker_reason}")

    assert status.is_installed is True
    assert status.mode == RufloIntegrationMode.NATIVE_RUFLO
    assert status.executable_path is not None
    assert os.path.exists(status.executable_path)
    assert "3.63.4" in (status.package_version or "")

    # Execute real RufloCoordinator methods against real binary
    coord = RufloCoordinator(executable_path=status.executable_path)
    ver = coord.get_version()
    assert "3.63.4" in ver

    # Run real ruflo doctor diagnostic
    doctor_res = coord.run_doctor()
    assert doctor_res["exit_code"] == 0
    assert "RuFlo Doctor" in doctor_res["stdout"]
    assert "System diagnostics" in doctor_res["stdout"]


def test_ruflo_runtime_probe_missing_reports_blocker():
    """Verifies that missing ruflo executable reports UNINTEGRATED_FALLBACK and exact blocker."""
    with patch("shutil.which", return_value=None):
        with patch("os.path.exists", return_value=False):
            status = probe_ruflo_runtime()
            assert not status.is_installed
            assert status.mode == RufloIntegrationMode.UNINTEGRATED_FALLBACK
            assert status.executable_path is None
            assert "ruflo@3.63.4" in status.blocker_reason
            assert "UNVERIFIED / UNINTEGRATED" in status.blocker_reason


def test_orchestrator_factory_delegates_to_native_when_forced_or_missing():
    """Verifies that factory safely selects AarkaNativeSparcCoordinator without mislabeling."""
    with patch("shutil.which", return_value=None):
        with patch("os.path.exists", return_value=False):
            orchestrator = OrchestratorFactory.get_orchestrator()
            assert isinstance(orchestrator, AarkaNativeSparcCoordinator)
            assert "Ruflo" not in orchestrator.__class__.__name__

    # Force native mode even when Ruflo is present
    forced_native = OrchestratorFactory.get_orchestrator(force_native=True)
    assert isinstance(forced_native, AarkaNativeSparcCoordinator)


def test_orchestrator_factory_selects_ruflo_when_present():
    """Verifies factory returns genuine RufloCoordinator when Ruflo is installed, or native coordinator when absent."""
    status = probe_ruflo_runtime()
    orchestrator = OrchestratorFactory.get_orchestrator()
    if status.is_installed:
        assert isinstance(orchestrator, RufloCoordinator)
        assert os.path.exists(orchestrator.executable_path)
    else:
        assert isinstance(orchestrator, AarkaNativeSparcCoordinator)
        assert "Ruflo" not in orchestrator.__class__.__name__

    # Also verify positive branch via mock probe so factory selection is guaranteed tested
    from modules.sparc.ruflo_adapter import RufloRuntimeStatus
    mock_status = RufloRuntimeStatus(
        is_installed=True,
        mode=RufloIntegrationMode.NATIVE_RUFLO,
        executable_path=os.path.abspath(__file__),
        package_version="3.63.4"
    )
    with patch("modules.sparc.ruflo_adapter.probe_ruflo_runtime", return_value=mock_status):
        active_orch = OrchestratorFactory.get_orchestrator()
        assert isinstance(active_orch, RufloCoordinator)
        assert active_orch.executable_path == os.path.abspath(__file__)


def test_ruflo_coordinator_subprocess_argument_safety():
    """Verifies that RufloCoordinator uses argument arrays and structured JSON flags."""
    coord = RufloCoordinator(executable_path="C:\\mock\\ruflo")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = '{"status": "completed", "stages": 5}'

    with patch("subprocess.run", return_value=mock_proc) as mock_run:
        result = coord.execute_swarm(
            task_description="Build parser",
            agent_roles=["Architect", "Implementer"],
            workspace_dir="./workspace"
        )
        assert result["status"] == "completed"

        # Verify call arguments
        args, kwargs = mock_run.call_args
        cmd_list = args[0]
        assert cmd_list[0] == os.path.abspath("C:\\mock\\ruflo")
        assert cmd_list[1] == "swarm"
        assert cmd_list[2] == "run"
        assert "--task" in cmd_list
        assert "--roles" in cmd_list
        assert "--json" in cmd_list
        # Ensure shell=False is implied by not passing shell=True
        assert kwargs.get("shell") is not True
