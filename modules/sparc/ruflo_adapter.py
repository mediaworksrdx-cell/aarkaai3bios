"""
Ruflo Integration Adapter & Swarm Coordinator Interface.

Separates genuine Ruflo runtime coordination from native Aarka SPARC orchestration.
Never labels custom coordinators as Ruflo.
Probes runtime requirements (official package 'ruflo@3.63.4' / '@claude-flow/cli: 3.63.4'),
and if uninstalled, explicitly records the dependency blocker and gracefully delegates to
the native AarkaNativeSparcCoordinator.
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


def probe_ruflo_runtime() -> RufloRuntimeStatus:
    """
    Probes the host environment for genuine Ruflo binary or Node.js package.
    Authoritative package: 'ruflo@3.63.4' (MIT, published by ruvnet).
    """
    ruflo_bin = shutil.which("ruflo")
    notes: List[str] = []

    if ruflo_bin:
        try:
            # Query version
            res = subprocess.run(
                [ruflo_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False
            )
            version_str = res.stdout.strip() or res.stderr.strip()
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
            notes.append(f"Failed to execute version probe on '{ruflo_bin}': {e}")

    # Not found on PATH
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
        self.executable_path = executable_path
        self.timeout_seconds = timeout_seconds

    def execute_swarm(self, task_description: str, agent_roles: List[str], workspace_dir: str) -> Dict[str, Any]:
        """
        Delegates task to the real ruflo executable using JSON argument vectors.
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
        if proc.returncode != 0:
            raise RuntimeError(f"Ruflo execution failed with code {proc.returncode}: {proc.stderr}")

        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {
                "success": proc.returncode == 0,
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
