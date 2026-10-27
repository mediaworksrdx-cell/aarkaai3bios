"""
Ruflo Integration & Swarm Coordinator Verification Test Suite.
Verifies runtime probe, blocker reporting, safe adapter isolation,
subprocess argument array safety, and zero mislabeling of custom coordinators.
"""

from unittest.mock import patch, MagicMock
import pytest
from modules.sparc.ruflo_adapter import (
    probe_ruflo_runtime,
    RufloIntegrationMode,
    RufloCoordinator,
    OrchestratorFactory,
)
from modules.sparc.coordinator import AarkaNativeSparcCoordinator


def test_ruflo_runtime_probe_missing():
    """Verifies that missing ruflo executable reports UNINTEGRATED_FALLBACK and exact blocker."""
    with patch("shutil.which", return_value=None):
        status = probe_ruflo_runtime()
        assert not status.is_installed
        assert status.mode == RufloIntegrationMode.UNINTEGRATED_FALLBACK
        assert status.executable_path is None
        assert "ruflo@3.63.4" in status.blocker_reason
        assert "UNVERIFIED / UNINTEGRATED" in status.blocker_reason


def test_ruflo_runtime_probe_installed():
    """Verifies detection and version extraction when ruflo executable is discovered."""
    mock_run = MagicMock()
    mock_run.stdout = "3.63.4\n"
    mock_run.stderr = ""
    mock_run.returncode = 0

    with patch("shutil.which", return_value="C:\\Tools\\ruflo.cmd"):
        with patch("subprocess.run", return_value=mock_run):
            status = probe_ruflo_runtime()
            assert status.is_installed
            assert status.mode == RufloIntegrationMode.NATIVE_RUFLO
            assert status.executable_path == "C:\\Tools\\ruflo.cmd"
            assert "3.63.4" in status.package_version


def test_orchestrator_factory_delegates_to_native_when_unintegrated():
    """Verifies that factory safely selects AarkaNativeSparcCoordinator without mislabeling."""
    with patch("shutil.which", return_value=None):
        orchestrator = OrchestratorFactory.get_orchestrator()
        assert isinstance(orchestrator, AarkaNativeSparcCoordinator)
        # Verify it is not masquerading as Ruflo
        assert "Ruflo" not in orchestrator.__class__.__name__


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
        assert cmd_list[0] == "C:\\mock\\ruflo"
        assert cmd_list[1] == "swarm"
        assert cmd_list[2] == "run"
        assert "--task" in cmd_list
        assert "--roles" in cmd_list
        assert "--json" in cmd_list
        # Ensure shell=False is implied by not passing shell=True
        assert kwargs.get("shell") is not True
