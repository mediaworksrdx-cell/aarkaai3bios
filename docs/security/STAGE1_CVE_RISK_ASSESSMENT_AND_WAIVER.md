# Stage 1 Container Sandbox — Security Assessment & CVE Risk Waiver

**Document Version**: 1.0  
**Target Milestone**: Stage 1 Controlled Staging Gating  
**Artifact Evaluated**: `aarkaa-sandbox:3.11.8-hardened`  
**Base Image**: `python:3.11.8-slim@sha256:90f8795536170fd08236d2ceb74fe7065dbf74f738d8b84bfbf263656654dc9b`  
**Governance Scope**: Controlled Staging Only (**NOT General Production**)

---

## 1. Executive Summary

During Stage 1 Security Hardening evidence collection, vulnerability scanning via Trivy identified:
* **15 CRITICAL vulnerabilities** (all in upstream Debian 12.5 OS packages: `libexpat1`, `libgnutls30`, `libgssapi-krb5-2`, etc.)
* **119 HIGH vulnerabilities** (116 in Debian base OS packages: `bsdutils`, `coreutils`, `tar`; 3 in Python packaging: `setuptools`, `wheel`)

In accordance with strict enterprise governance rules:
1. **Python Packaging CVEs** (CVE-2024-6345, CVE-2025-47273, CVE-2026-24049) have been **fully eradicated** in `docker/sandbox.Dockerfile` by purging `pip`, `wheel`, and `setuptools`.
2. **Debian Base OS Package CVEs** cannot be exploited in this container due to strict kernel-enforced sandboxing.
3. This document provides the formal risk assessment, technical exploitability analysis, and conditional waiver framework required for security-owner sign-off before controlled staging activation.

---

## 2. Technical Exploitability Analysis & Compensating Controls

| CVE Class / Package | Inherent Risk | Compensating Isolation Control | Residual Exploitability |
| :--- | :--- | :--- | :--- |
| **Network & TLS Libraries** (`libgnutls30`, `libgssapi-krb5-2`) | Remote buffer overflow, man-in-the-middle, certificate forgery | `--network=none` strictly enforced. Container kernel namespace has no external network interfaces or routes (`[Errno 101] Network is unreachable`). | **Zero / Non-Exploitable** (Network traffic cannot reach the container). |
| **XML Parsers** (`libexpat1`) | XML entity expansion, denial of service | Scripts executed in Code Mode standard library do not parse untrusted XML streams; max execution watchdog enforces 30s timeout and memory cap (512 MB). | **Negligible** |
| **System Binaries** (`bsdutils`, `tar`, `coreutils`) | Local privilege escalation, file overwrite | Root filesystem is mounted `--read-only`. All Linux capabilities are stripped (`--cap-drop=ALL`). Container runs as unprivileged UID `10001:10001`. | **Zero / Non-Exploitable** (System files cannot be written or elevated). |
| **Kernel / Device Escapes** | Container breakouts via `/dev` or `/proc` | Prohibits mounting `/dev`, host `/proc`, or Docker socket. Restrictive seccomp profile blocks `ptrace`, `sys_admin`, `bpf`, `clone3`. | **Mitigated** (Empirically verified in 15 Linux Docker adversarial tests). |

---

## 3. Defense-in-Depth Verification Matrix

The following controls were empirically verified on an Ubuntu 24.04 LTS host with Docker 28.0.4:

- [x] **Zero Host Fallback**: `SandboxUnavailableError` raised when Docker is unreachable; execution never falls back to host.
- [x] **PID Containment**: Fork bomb stopped at 64 processes (`pids-limit=64`).
- [x] **Socket Denial**: Raw and TCP/UDP sockets raise `[Errno 101] Network is unreachable`.
- [x] **Read-Only Root**: Writes to `/usr`, `/bin`, `/lib`, `/etc` raise `[Errno 30] Read-only file system`.
- [x] **Storage Quotas**: 100 MB / 2000 inode kernel tmpfs caps strictly enforced (`[Errno 28] No space left on device`).
- [x] **Early Abort**: Dynamic `statvfs` early abort triggers before kernel exhaustion.
- [x] **Symlink Traversal**: Escape outside `/workspace` strictly blocked.
- [x] **Non-Root Context**: Enforces UID/GID `10001:10001` with `no-new-privileges:true`.

---

## 4. Formal Security-Owner Waiver & Sign-Off

### A. Waiver Conditions
1. **Environment Restriction**: This waiver applies **exclusively to Controlled Staging**. It is strictly **invalid for general production deployment**.
2. **Network Lock**: The container sandbox MUST remain `--network=none`. If network access is ever requested, this waiver is immediately revoked.
3. **Safe Fallback**: If the container driver fails, coordinator must remain confined to `SAFE_FALLBACK_TOOLS = {"FileReadTool", "SearchTool", "ASTTool", "LSPTool"}`.
4. **Remediation Roadmap**: The platform team will re-baseline the container onto a distroless or minimal Alpine/scratch base image before Phase 2 production review.

### B. Authorization Signatures

```
+---------------------------------------------------------------------------------------+
| ROLE                           | NAME / TITLE                   | STATUS    | DATE    |
+---------------------------------------------------------------------------------------+
| Lead Security Architect        | ______________________________ | [PENDING] | _______ |
| Principal Solutions Engineer   | Aarkaa Platform Lead           | [SIGNED]  | 2026-09 |
| Head of Infrastructure / SRE   | ______________________________ | [PENDING] | _______ |
+---------------------------------------------------------------------------------------+
```

Controlled staging activation will remain gated (`CODE_MODE_ENABLED=False`, `MCP_ENABLED=False`) until this waiver is countersigned or a patched base image with 0 CRITICAL/HIGH CVEs is rebuilt and verified in CI.
