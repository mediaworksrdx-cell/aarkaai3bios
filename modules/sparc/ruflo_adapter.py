"""
Ruflo Integration Adapter & Swarm Coordinator Interface.

Integrates genuine Ruflo runtime CLI ('ruflo@3.63.4' / '@claude-flow/cli: 3.63.4' by ruvnet).
Discovers local and global binary installations, executes real health and diagnostics probes,
and coordinates multi-agent swarm operations using hardened argument-array execution (shell=False).
If Ruflo is not present, safely falls back to native AarkaNativeSparcCoordinator with explicit
unintegrated blocker reporting.
"""

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from modules.sparc.coordinator import (
    AarkaNativeSparcCoordinator,
    SparcSwarmCoordinator,
    StageResult,
    SparcPipelineResult,
    StageState,
)

logger = logging.getLogger(__name__)


class RufloIntegrationMode(str, Enum):
    NATIVE_RUFLO = "NATIVE_RUFLO"
    UNINTEGRATED_FALLBACK = "UNINTEGRATED_FALLBACK"


@dataclass
class RufloRuntimeStatus:
    is_installed: bool
    mode: RufloIntegrationMode
    executable_path: Optional[str] = None
    package_version: Optional[str] = None
    blocker_reason: Optional[str] = None
    verification_notes: List[str] = field(default_factory=list)


def probe_ruflo_runtime(extra_search_paths: Optional[List[str]] = None) -> RufloRuntimeStatus:
    """
    Probes the host environment for genuine Ruflo binary (global or local node_modules).
    Authoritative package: 'ruflo@3.63.4' (MIT, published by ruvnet).
    """
    notes: List[str] = []
    candidates: List[str] = []

    # 1. System PATH lookups
    for bin_name in ["ruflo", "ruflo.cmd"]:
        found = shutil.which(bin_name)
        if found:
            candidates.append(os.path.abspath(found))

    # 2. Local node_modules candidates
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_bins = [
        os.path.join(repo_root, "node_modules", ".bin", "ruflo.cmd"),
        os.path.join(repo_root, "node_modules", ".bin", "ruflo"),
        os.path.join(repo_root, "frontend", "node_modules", ".bin", "ruflo.cmd"),
        os.path.join(repo_root, "frontend", "node_modules", ".bin", "ruflo"),
    ]
    if extra_search_paths:
        local_bins.extend(extra_search_paths)

    for lb in local_bins:
        if os.path.exists(lb):
            norm = os.path.abspath(lb)
            if norm not in candidates:
                candidates.append(norm)

    # 3. Test execution of candidate binaries
    for ruflo_bin in candidates:
        try:
            res = subprocess.run(
                [ruflo_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False
            )
            version_str = (res.stdout.strip() or res.stderr.strip()).splitlines()[-1]
            notes.append(f"Discovered Ruflo executable at: {ruflo_bin} (version: {version_str})")
            return RufloRuntimeStatus(
                is_installed=True,
                mode=RufloIntegrationMode.NATIVE_RUFLO,
                executable_path=ruflo_bin,
                package_version=version_str,
                blocker_reason=None,
                verification_notes=notes
            )
        except Exception as e:
            notes.append(f"Probe attempt on '{ruflo_bin}' failed: {e}")

    # Not found in PATH or local candidate locations
    blocker = (
        "Ruflo runtime (official npm package 'ruflo@3.63.4') is not installed or not found on PATH. "
        "Native Ruflo swarm CLI coordination is unavailable. Integration status is UNVERIFIED / UNINTEGRATED. "
        "Architecture safely falls back to AarkaNativeSparcCoordinator."
    )
    notes.append(blocker)

    return RufloRuntimeStatus(
        is_installed=False,
        mode=RufloIntegrationMode.UNINTEGRATED_FALLBACK,
        executable_path=None,
        package_version=None,
        blocker_reason=blocker,
        verification_notes=notes
    )


class RufloCoordinator:
    """
    Coordinator wrapper for genuine Ruflo CLI-backed swarm orchestration.
    Only instantiated when probe_ruflo_runtime().is_installed is True.
    """

    def __init__(self, executable_path: str, timeout_seconds: float = 120.0) -> None:
        self.executable_path = os.path.abspath(executable_path)
        self.timeout_seconds = timeout_seconds

    def get_version(self) -> str:
        """Executes real ruflo --version."""
        res = subprocess.run(
            [self.executable_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False
        )
        return (res.stdout.strip() or res.stderr.strip()).splitlines()[-1]

    def run_doctor(self) -> Dict[str, Any]:
        """Runs the real ruflo doctor diagnostic suite."""
        res = subprocess.run(
            [self.executable_path, "doctor"],
            capture_output=True,
            text=True,
            timeout=30.0,
            check=False
        )
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "passed": res.returncode == 0
        }

    def execute_swarm(self, task_description: str, agent_roles: List[str], workspace_dir: str) -> Dict[str, Any]:
        """
        Delegates task to the real ruflo executable using structured JSON argument vectors.
        Uses shell=False to prevent command injection.
        """
        args = [
            self.executable_path,
            "swarm",
            "run",
            "--task", task_description,
            "--roles", ",".join(agent_roles),
            "--workspace", os.path.abspath(workspace_dir),
            "--json"
        ]
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "raw_output": proc.stdout,
                "raw_error": proc.stderr
            }


class OrchestratorFactory:
    """
    Factory creating either genuine RufloCoordinator or AarkaNativeSparcCoordinator.
    Never aliases or labels custom coordinators as Ruflo.
    """

    @staticmethod
    def get_orchestrator(force_native: bool = False) -> Any:
        status = probe_ruflo_runtime()
        if not force_native and status.is_installed and status.executable_path:
            logger.info("Using genuine Ruflo coordinator at %s", status.executable_path)
            return RufloCoordinator(executable_path=status.executable_path)
        else:
            if not status.is_installed:
                logger.warning("Ruflo dependency unintegrated: %s", status.blocker_reason)
            return AarkaNativeSparcCoordinator()
