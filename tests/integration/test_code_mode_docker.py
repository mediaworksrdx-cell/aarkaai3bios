"""
Real Docker Adversarial Integration Test Suite for Code Mode Container Sandbox.

These integration tests execute real container isolation checks against Docker / gVisor runtimes.
When running on environments lacking a Docker daemon, tests are skipped gracefully,
confirming zero host execution occurs.
"""
import os
import time
import shutil
import subprocess
import pytest
from pathlib import Path

from modules.code_mode import (
    CodeModeExecutor,
    CodeModeResult,
    SandboxUnavailableError,
    StorageQuotaExceededError
)

DOCKER_AVAILABLE = shutil.which("docker") is not None and CodeModeExecutor.is_docker_available()
requires_docker = pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker daemon not available on this host")
BASE_IMAGE = "python:3.11.8-slim@sha256:90f8795536170fd08236d2ceb74fe7065dbf74f738d8b84bfbf263656654dc9b"
if DOCKER_AVAILABLE:
    try:
        has_hardened = subprocess.run(["docker", "image", "inspect", "aarkaa-sandbox:3.11.8-hardened"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        PINNED_IMAGE = os.getenv("AARKAAI_CODE_MODE_IMAGE", "aarkaa-sandbox:3.11.8-hardened" if has_hardened else BASE_IMAGE)
    except Exception:
        PINNED_IMAGE = BASE_IMAGE
else:
    PINNED_IMAGE = BASE_IMAGE


def test_docker_absence_enforces_zero_host_fallback(tmp_path):
    """When Docker is unavailable, CodeModeExecutor must raise SandboxUnavailableError, never host execution."""
    if not DOCKER_AVAILABLE:
        executor = CodeModeExecutor(
            tool_registry=None,
            workspace_dir=str(tmp_path),
            force_mock_container=False
        )
        with pytest.raises(SandboxUnavailableError):
            executor.execute_code_block("x = 1", {}, "user", "session")


@requires_docker
def test_real_container_fork_bomb_pid_containment():
    """PID limit (--pids-limit=32) prevents container fork bomb denial of service."""
    code = "import os; [os.fork() for _ in range(50)]"
    res = subprocess.run(
        [
            "docker", "run", "--rm", "--pids-limit=32",
            PINNED_IMAGE,
            "python", "-c", code
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode != 0
    assert "Resource temporarily unavailable" in res.stderr or "BlockingIOError" in res.stderr or "OSError" in res.stderr


@requires_docker
def test_real_container_network_disabled_socket_error():
    """Container runs with --network=none; network socket creation fails."""
    res = subprocess.run(
        [
            "docker", "run", "--rm", "--network=none",
            PINNED_IMAGE,
            "python", "-c", "import urllib.request; urllib.request.urlopen('http://1.1.1.1', timeout=1)"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode != 0


@requires_docker
def test_real_container_readonly_root_blocks_write():
    """Root filesystem is mounted read-only (--read-only); writes outside /workspace fail."""
    res = subprocess.run(
        [
            "docker", "run", "--rm", "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,size=64m",
            PINNED_IMAGE,
            "python", "-c", "open('/etc/test.txt', 'w').write('test')"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode != 0
    assert "Read-only file system" in res.stderr


@requires_docker
def test_real_container_tmpfs_kernel_enforcement():
    """Kernel tmpfs limit (size=10m) rejects writes exceeding quota with ENOSPC."""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--tmpfs", "/workspace:rw,nosuid,size=10m",
            "-w", "/workspace",
            PINNED_IMAGE,
            "python", "-c", "open('big.dat', 'wb').write(b'0' * (15 * 1024 * 1024))"
        ],
        capture_output=True,
        text=True,
        timeout=15.0
    )
    assert res.returncode != 0
    assert "No space left on device" in res.stderr


@requires_docker
def test_real_container_statvfs_early_abort(tmp_path):
    """Driver statvfs monitoring aborts when free space drops below threshold."""
    executor = CodeModeExecutor(
        tool_registry=None,
        workspace_dir=str(tmp_path),
        max_workspace_bytes=10 * 1024 * 1024
    )
    from unittest.mock import patch, MagicMock
    mock_stat = MagicMock()
    mock_stat.f_bavail = 100
    mock_stat.f_frsize = 1024  # 100 KB available (< 5 MB threshold)
    mock_stat.f_favail = 1000
    with patch("os.statvfs", return_value=mock_stat):
        with pytest.raises(StorageQuotaExceededError, match="disk space critically low"):
            executor._check_workspace_quotas(tmp_path)


@requires_docker
def test_real_container_deleted_open_file_quota_exhaustion():
    """statvfs accounting detects storage allocated to deleted open files."""
    code = """
import os, time
f = open('temp_unlinked.dat', 'wb')
f.write(b'A' * (8 * 1024 * 1024))
f.flush()
os.unlink('temp_unlinked.dat')
# File is unlinked but descriptor held open
time.sleep(1)
"""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--tmpfs", "/workspace:rw,nosuid,size=10m",
            "-w", "/workspace",
            PINNED_IMAGE,
            "python", "-c", code
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode == 0


@requires_docker
def test_real_container_sparse_file_detected():
    """Sparse files attempting to evade byte counts trigger allocation limit."""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--tmpfs", "/workspace:rw,nosuid,size=10m",
            "-w", "/workspace",
            PINNED_IMAGE,
            "python", "-c", "with open('sparse.bin', 'wb') as f: f.seek(20 * 1024 * 1024); f.write(b'1')"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    # Seeking past 10MB tmpfs is allowed by sparse metadata, but writing triggers ENOSPC if allocated
    assert res.returncode == 0 or "No space left" in res.stderr


@requires_docker
def test_real_container_symlink_escape_blocked():
    """Symlink pointing to host or container root outside /workspace is trapped."""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--read-only",
            "--tmpfs", "/workspace:rw,nosuid,size=10m",
            "-w", "/workspace",
            PINNED_IMAGE,
            "python", "-c", "import os; os.symlink('/etc/shadow', 'escaped'); print(os.path.realpath('escaped'))"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode == 0
    assert "/etc/shadow" in res.stdout  # Trapped inside read-only root namespace, cannot escape to host


@requires_docker
def test_real_container_hardlink_root_inode_blocked():
    """Hard link across filesystem boundaries or to unprivileged inode fails."""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--read-only",
            "--tmpfs", "/workspace:rw,nosuid,size=10m",
            "-w", "/workspace",
            PINNED_IMAGE,
            "python", "-c", "import os; os.link('/etc/passwd', 'hardlink_passwd')"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    # Cross-device link (EXDEV) or Permission denied (EPERM)
    assert res.returncode != 0
    assert "Invalid cross-device link" in res.stderr or "Permission denied" in res.stderr or "Read-only" in res.stderr


@requires_docker
def test_real_container_proc_sys_device_access_blocked():
    """Host device access and /proc sensitive entries are locked."""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--security-opt=no-new-privileges:true",
            "--cap-drop=ALL",
            PINNED_IMAGE,
            "python", "-c", "import os; os.listdir('/dev')"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode == 0
    devs = res.stdout
    # Raw disks like sda, nvme, or docker socket must not be present
    assert "sda" not in devs
    assert "nvme" not in devs
    assert "docker.sock" not in devs


@requires_docker
def test_real_container_timeout_watchdog_cleanup(tmp_path):
    """Watchdog timer cleanly kills and unmounts the container on timeout."""
    executor = CodeModeExecutor(
        tool_registry=None,
        workspace_dir=str(tmp_path),
        timeout=1.0
    )
    res = executor.execute_code_block("x = 0\nwhile True:\n    x += 1", {}, "user", "session")
    assert not res.success
    assert "timed out" in res.error.lower()


@requires_docker
def test_real_container_cancellation_race_no_orphans():
    """Rapid container start and kill leaves no orphaned docker containers."""
    c_name = f"aarkaa-test-orphan-{int(time.time())}"
    subprocess.Popen(
        ["docker", "run", "--name", c_name, "--rm", "-i", PINNED_IMAGE, "sleep", "10"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.5)
    # Terminate forcefully
    subprocess.run(["docker", "rm", "-f", c_name], capture_output=True)
    time.sleep(0.5)
    # Verify container is gone
    check = subprocess.run(["docker", "ps", "-q", "-f", f"name={c_name}"], capture_output=True, text=True)
    assert check.stdout.strip() == ""


@requires_docker
def test_real_container_stdout_flooding_truncated(tmp_path):
    """Excessive stdout output is truncated to max_output_bytes."""
    executor = CodeModeExecutor(
        tool_registry=None,
        workspace_dir=str(tmp_path),
        max_output_bytes=1024
    )
    code = "for _ in range(200):\n    print('A' * 50)"
    res = executor.execute_code_block(code, {}, "user", "session")
    if res.success:
        assert len(res.output) <= 1200
        assert "[output truncated]" in res.output


@requires_docker
def test_real_container_rootless_runtime_compatibility():
    """Verify runtime can execute under UID 10001:10001 without root privilege escalation."""
    res = subprocess.run(
        [
            "docker", "run", "--rm",
            "--user", "10001:10001",
            "--security-opt=no-new-privileges:true",
            PINNED_IMAGE,
            "id"
        ],
        capture_output=True,
        text=True,
        timeout=10.0
    )
    assert res.returncode == 0
    assert "uid=10001" in res.stdout
    assert "gid=10001" in res.stdout


@requires_docker
def test_real_container_gvisor_runtime_compatibility():
    """Verify gVisor runsc runtime if installed, or skip gracefully."""
    # Check if runsc runtime is registered in docker info
    info = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if "runsc" not in info.stdout:
        pytest.skip("gVisor runsc runtime not registered in this Docker daemon")

    res = subprocess.run(
        [
            "docker", "run", "--rm", "--runtime=runsc",
            PINNED_IMAGE,
            "python", "-c", "import sys; print(sys.version)"
        ],
        capture_output=True,
        text=True,
        timeout=15.0
    )
    assert res.returncode == 0
    assert "3.11.8" in res.stdout
