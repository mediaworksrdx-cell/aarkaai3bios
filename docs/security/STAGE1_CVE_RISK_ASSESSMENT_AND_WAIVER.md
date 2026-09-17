# Stage 1 Container Sandbox — Security Assessment & CVE Risk Waiver

**Document Version**: 1.1  
**Target Milestone**: Stage 1 Controlled Staging Gating  
**Artifact Evaluated**: `aarkaa-sandbox:3.11.8-hardened` (CI Run ID `35168199406`, Commit `2228f58`)  
**Base Image**: `python:3.11.8-slim@sha256:90f8795536170fd08236d2ceb74fe7065dbf74f738d8b84bfbf263656654dc9b`  
**Governance Scope**: Controlled Staging Only (**NOT General Production**)

---

## 1. Executive Summary & Gating Posture

> [!CAUTION]
> **CVE Status is NOT Empirically Cleared**:
> Vulnerability scanning on the hardened image (`aarkaa-sandbox:3.11.8-hardened`) confirms that all fixable CVEs have been remediated, but **5 CRITICAL** and **59 HIGH** vulnerabilities remain unpatched in upstream Debian packages (`Fixed: None`). The strict prerequisite of 0 HIGH and 0 CRITICAL vulnerabilities **has not been met**.
> 
> This document details the technical isolation rationale for risk acceptance, but **does not constitute formal acceptance**. Controlled staging enablement remains **blocked** pending countersignature by the security owner. General production deployment remains **not approved**.

---

## 2. Empirical Scan Findings (`ci/artifacts/trivy_report.json`)

* **Artifact Name**: `aarkaa-sandbox:3.11.8-hardened` (debian 12.15)
* **Python Language Packages**: **0 Vulnerabilities** (`setuptools`, `wheel`, and `pip` purged).
* **Debian OS Packages**:
  * **CRITICAL**: **5** (All unfixable upstream: `libsqlite3-0`, `perl-base`, `zlib1g`).
  * **HIGH**: **59** (All unfixable upstream: `bsdutils`, `coreutils`, `tar`).
  * **MEDIUM / LOW**: 0.

---

## 3. Technical Exploitability Analysis & Compensating Controls

| Package & Remaining CVEs | Inherent Risk | Compensating Kernel Isolation Control | Residual Exploitability |
| :--- | :--- | :--- | :--- |
| **`libsqlite3-0`** (CVE-2025-7458) | Memory corruption via crafted SQLite database file | SQLite databases accessed in sandbox are ephemeral and created locally; container runs as non-root (`10001:10001`) with `--cap-drop=ALL` and memory cap (512 MB). | **Negligible** |
| **`perl-base`** (CVE-2026-13221, CVE-2026-42496, CVE-2026-8376) | Code execution via malformed Perl script execution | Code Mode executes Python scripts only via `/usr/local/bin/python`; Perl interpreter is never invoked. | **Non-Invoked / Inert** |
| **`zlib1g`** (CVE-2023-45853) | Buffer overflow via crafted compressed stream | Container has `--network=none` (no external streams can be ingested); memory watchdog aborts at 512 MB. | **Zero External Ingress** |
| **`bsdutils`, `coreutils`, `tar`** (Multiple HIGH CVEs) | Privilege escalation / file system manipulation | Root filesystem is mounted `--read-only`. All Linux capabilities dropped (`--cap-drop=ALL`). `--user 10001:10001` enforced. Device and host filesystems are unmounted. | **Non-Exploitable** (System files cannot be modified). |

---

## 4. Defense-in-Depth Empirical Verification Matrix

The following controls were empirically verified on an Ubuntu 24.04 LTS host with Docker 28.0.4 in GitHub Actions run `35168199406`:

- [x] **Zero Host Fallback**: `SandboxUnavailableError` raised when Docker is unreachable; execution never falls back to host.
- [x] **PID Containment**: Fork bomb stopped at 32 processes (`pids-limit=32`).
- [x] **Socket Denial**: Raw and TCP/UDP sockets raise `[Errno 101] Network is unreachable`.
- [x] **Read-Only Root**: Writes outside `/workspace` raise `[Errno 30] Read-only file system` or `[Errno 13] Permission denied`.
- [x] **Storage Quotas**: 10 MB tmpfs cap strictly enforced (`[Errno 28] No space left on device`).
- [x] **Early Abort**: Dynamic `statvfs` early abort triggers before kernel exhaustion.
- [x] **Symlink Traversal**: Escape outside `/workspace` strictly blocked.
- [x] **Non-Root Context**: Enforces UID/GID `10001:10001` with `no-new-privileges:true`.

---

## 5. Formal Security-Owner Waiver Sign-Off Template

### A. Mandatory Waiver Constraints
1. **Environment Restriction**: Valid strictly for **Controlled Staging**. Invalid for production.
2. **Network Lock**: `--network=none` must remain enforced at all times.
3. **Safe Fallback**: Coordinator must fall back strictly to `SAFE_FALLBACK_TOOLS = {"FileReadTool", "SearchTool", "ASTTool", "LSPTool"}`.
4. **Distroless Re-baselining**: Platform team must evaluate distroless or scratch-based containerization before production review.

### B. Formal Sign-Off Table

```
+---------------------------------------------------------------------------------------+
| ROLE                           | NAME / TITLE                   | STATUS    | DATE    |
+---------------------------------------------------------------------------------------+
| Lead Security Architect        | ______________________________ | [PENDING] | _______ |
| Principal Solutions Engineer   | Aarkaa Platform Lead           | [SIGNED]  | 2026-09 |
| Head of Infrastructure / SRE   | ______________________________ | [PENDING] | _______ |
+---------------------------------------------------------------------------------------+
```

Controlled staging activation will remain gated (`CODE_MODE_ENABLED=False`, `MCP_ENABLED=False`) until this waiver is countersigned by the Lead Security Architect.
