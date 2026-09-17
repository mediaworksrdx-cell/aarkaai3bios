# Stage 1 Container Sandbox — Remediation & Validation Record

**Document Version**: 2.0  
**Target Milestone**: Stage 1 Controlled Staging Gating (Experimental Remediation)  
**Branch**: `remediation/cve-hardened-sandbox`  
**Governance Scope**: Controlled Staging Only (**NOT General Production**)  
**Gating Posture**: Controlled Staging **BLOCKED** pending empirical comparison evidence and formal security-owner sign-off.

---

## 1. Executive Summary & Governance Posture

> [!IMPORTANT]
> **Mandatory Governance Posture Statement**:
> **“Security-hardened by design and pending empirical validation; production readiness remains unverified pending empirical security and reliability evidence.”**
>
> * **Staging Activation**: Strictly **BLOCKED**. Both feature flags remain disabled:
>   `CODE_MODE_ENABLED = False`  
>   `MCP_ENABLED = False`  
> * **Remediation Method**: Automated, one-pass empirical comparison across candidate base images (Debian 12 slim baseline, Wolfi/Chainguard minimal Python, Distroless Python 3, and Ubuntu 24.04 minimal).
> * **Selection Principle**: The winning base image is selected strictly through a defined 5-gate elimination algorithm based on empirical evidence, not base-image labels.
> * **Certification Timing**: This document serves strictly as a **Remediation & Validation Record**. No hardening certification will be issued until all required integration tests pass, raw scan results are reviewed, residual risks are documented, and the Lead Security Architect countersigns.

---

## 2. Strict 5-Gate Selection Hierarchy

Candidates are evaluated through a strict hierarchical elimination order:

1. **Gate 1 — Functional & Isolation Integrity**:
   - Must achieve 15/15 passed executable Docker adversarial tests (0 failures allowed).
   - Test reporting must state exactly: `15 passed, 1 skipped — gVisor unavailable/unverified on host, 0 failed`.
   - Any failure in executable tests results in immediate disqualification.
2. **Gate 2 — Dynamic Linkage & Native Dependency Compatibility**:
   - Must cleanly load and execute: `zlib`, `pyexpat`, `sqlite3`, `ctypes`, `uuid`, `hashlib`.
   - Missing SQLite constitutes an incompatibility failure unless the application is explicitly proven not to require it.
   - Verified non-root UID/GID `10001:10001` permissions in `/workspace` and `/tmp`.
3. **Gate 3 — Security & Vulnerability Threshold**:
   - Evaluated under three unambiguous states:
     - `PASS`: Exactly 0 High and 0 Critical findings.
     - `WAIVER_REQUIRED`: Findings remain with `FixedVersion: None`; requires documented security-owner waiver.
     - `FAIL`: Unapproved Critical findings, scanner failure, or masked/suppressed findings.
4. **Gate 4 — Supply Chain Evidence Completeness**:
   - Authentic Syft SPDX 2.3 JSON and CycloneDX 1.7 JSON generated.
   - Cryptographic Cosign attestation and SLSA Level 2 provenance generated and bound to exact image digest.
5. **Gate 5 — Operational & Metric Ranking**:
   - Ranking order: Trivy Status (`PASS` > `WAIVER_REQUIRED`) → Lowest residual CVE count → Smallest container attack surface (image size & package count) → Startup latency benchmark.
   - *Core Rule*: A candidate with fewer CVEs **cannot win** if it fails Gate 1 or Gate 2.

---

## 3. Empirical Candidate Evaluation Matrix

Automated comparison results from Linux CI (Run `35172519153`, commit `ea37f93`) recorded in [`ci/artifacts/candidate_comparison_scorecard.json`](file:///c:/Users/daarv/.gemini/antigravity/scratch/aarkaai3b/ci/artifacts/candidate_comparison_scorecard.json):

| Candidate ID | Name | Resolved Immutable Digest | Gate 1 (Isolation) | Gate 2 (Linkage) | Gate 3 (Trivy) | Image Size | Packages | Selection Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `candidate_a_debian_slim` | **Debian 12 Slim (Baseline)** | `sha256:90f8795536170fd08236...` | 15P, 1S, 0F | PASS | WAIVER_REQ (5C / 59H) | 183.3 MB | 108 | **REJECTED** (Gate 3 CVEs) |
| `candidate_b_wolfi_python` | **Chainguard / Wolfi Python** | `sha256:c8e464ca00c86bd80498...` | SKIPPED | FAIL (Path/Entrypoint) | SKIPPED | 63.4 MB | N/A | **REJECTED** (Gate 2 Linkage) |
| `candidate_c_distroless_python` | **Distroless Python 3** | `sha256:2fdb05402a2cf21cf78f...` | SKIPPED | FAIL (Path/Entrypoint) | SKIPPED | 50.6 MB | N/A | **REJECTED** (Gate 2 Linkage) |
| `candidate_d_ubuntu_minimal` | **Ubuntu 24.04 Minimal** | `sha256:69cecf4bbf72d2d44a9e...` | **15P, 1S, 0F** | **PASS** (`zlib 1.3`, `expat 2.6.1`, `sqlite 3.45.1`) | **PASS (0 Crit / 0 High)** | **111.4 MB** | **107** | **SELECTED WINNER** |

*Selection Rationale*: `candidate_d_ubuntu_minimal` was the sole candidate to pass Gate 1 (15 passed, 1 skipped - gVisor unverified, 0 failed), pass Gate 2 (all native C-extensions functional under non-root UID 10001:10001), and pass Gate 3 with **zero Critical and zero High vulnerabilities** detected by Trivy.

---

## 4. Adversarial Isolation & Defense-in-Depth Matrix

The following controls are verified across all qualifying candidates:

- [x] **Zero Host Fallback**: `SandboxUnavailableError` raised when Docker is unreachable; execution never falls back to host.
- [x] **PID Containment**: Fork bomb stopped at 32 processes (`--pids-limit=32`).
- [x] **Socket Denial**: Raw and TCP/UDP sockets raise `[Errno 101] Network is unreachable` (`--network=none`).
- [x] **Read-Only Root**: Writes outside `/workspace` raise `[Errno 30] Read-only file system` or `[Errno 13] Permission denied`.
- [x] **Storage Quotas**: 10 MB tmpfs cap strictly enforced (`[Errno 28] No space left on device`).
- [x] **Early Abort**: Dynamic `statvfs` early abort triggers before kernel exhaustion.
- [x] **Symlink Traversal**: Escape outside `/workspace` strictly trapped inside read-only container root namespace.
- [x] **Non-Root Context**: Enforces UID/GID `10001:10001` with `no-new-privileges:true`.
- [x] **Output Flood Protection**: Truncates stream at maximum configured byte limit.
- [ ] **gVisor System Call Virtualization**: Recorded as **UNVERIFIED / SKIPPED** on hosts lacking `runsc`.

---

## 5. Formal Security-Owner Review & Sign-Off Template

### Mandatory Constraints for Staging Enablement
1. **Scope Restriction**: Approval is strictly limited to **Controlled Staging**. General production release remains **NOT APPROVED**.
2. **Network Lock**: Container `--network=none` must remain enforced at all times.
3. **Safe Fallback**: Coordinator fallback is strictly confined to `SAFE_FALLBACK_TOOLS = {"FileReadTool", "SearchTool", "ASTTool", "LSPTool"}`.
4. **Digest Binding**: Sign-off binds strictly and exclusively to the final selected and independently scanned image digest.

### Sign-Off Table

```
+---------------------------------------------------------------------------------------+
| ROLE                           | NAME / TITLE                   | STATUS    | DATE    |
+---------------------------------------------------------------------------------------+
| Lead Security Architect        | ______________________________ | [PENDING] | _______ |
| Principal Solutions Engineer   | Aarkaa Platform Lead           | [SIGNED]  | 2026-09 |
| Head of Infrastructure / SRE   | ______________________________ | [PENDING] | _______ |
+---------------------------------------------------------------------------------------+
```

Controlled staging activation will remain gated (`CODE_MODE_ENABLED=False`, `MCP_ENABLED=False`) until this record is countersigned by the Lead Security Architect upon review of the fresh CI evidence package.
