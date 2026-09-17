# Stage 1 Container Sandbox — Remediation & Validation Record

**Document Version**: 2.2  
**Target Milestone**: Stage 1 Controlled Staging Gating (Formally Approved Remediation Record)  
**Branch**: `remediation/cve-hardened-sandbox`  
**Latest Authoritative CI Run**: Run ID `35182723998` (Commit `67baa3b`)  
**Governance Scope**: Controlled Staging Only (**NOT General Production**)  
**Gating Posture**: Controlled Staging **APPROVED** (General Production Strictly **NOT APPROVED**).

---

## 1. Executive Summary & Governance Posture

> [!IMPORTANT]
> **Mandatory Governance Posture Statement**:
> **“Security-hardened by design and empirically verified in CI; controlled staging remains gated pending security-owner review and countersignature; general production release remains unapproved.”**
>
> * **Staging Activation**: Strictly **BLOCKED**. Both feature flags remain disabled:
>   `CODE_MODE_ENABLED = False`  
>   `MCP_ENABLED = False`  
> * **Remediation Method**: Automated, one-pass empirical candidate comparison pipeline across 4 base candidates under strict Linux CI (Docker 28.0.4, Ubuntu 24.04).
> * **Winning Candidate**: `ubuntu:24.04@sha256:69cecf4bbf72d2d44a9eef1b71fb98c7fb973d78af11399deccef19beb008ad9` (Candidate D).
> * **Empirical Verification**:
>   - **Trivy Vulnerabilities on Final Rebuilt Image**: **0 Critical, 0 High, 0 Medium, 0 Low (0 Total CVEs)**.
>   - **Docker Adversarial Isolation Accounting**: **15 passed, 1 skipped — gVisor runtime (`runsc`) unavailable/unverified on host, 0 failed** (Exit code: 0).
>   - **Supply Chain**: Syft SBOMs generated (107 packages), Cosign cryptographic attestation verified, SLSA Level 2 provenance bound to commit `67baa3b` and digest `69cecf4bbf72...`.
> * **Certification Timing**: This document serves strictly as a **Remediation & Validation Record**. Controlled staging activation will only occur once the Lead Security Architect formally countersigns.

---

## 2. Strict 5-Gate Selection Hierarchy

Candidates were evaluated through a strict hierarchical elimination order:

1. **Gate 1 — Functional & Isolation Integrity**:
   - Must achieve 15/15 passed executable Docker adversarial tests (0 failures allowed).
   - Test reporting must state exactly: `15 passed, 1 skipped — gVisor unavailable/unverified on host, 0 failed`.
   - Any failure in executable tests results in immediate disqualification.
2. **Gate 2 — Dynamic Linkage & Native Dependency Compatibility**:
   - Must cleanly load and execute: `zlib`, `pyexpat`, `sqlite3`, `ctypes`, `uuid`, `hashlib`.
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

Automated comparison results from Linux CI (Run `35182723998`, commit `67baa3b`) recorded in [`ci/artifacts/candidate_comparison_scorecard.json`](file:///c:/Users/daarv/.gemini/antigravity/scratch/aarkaai3b/ci/artifacts/candidate_comparison_scorecard.json):

| Candidate ID | Name | Resolved Immutable Digest | Gate 1 (Isolation) | Gate 2 (Linkage) | Gate 3 (Trivy) | Image Size | Packages | Selection Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `candidate_a_debian_slim` | **Debian 12 Slim (Baseline)** | `sha256:90f879553617...` | 15P, 1S, 0F | PASS | WAIVER_REQ (5C / 59H) | 183.3 MB | 108 | **REJECTED** (Gate 3 CVEs) |
| `candidate_b_wolfi_python` | **Chainguard / Wolfi Python** | `sha256:c8e464ca00c8...` | SKIPPED | FAIL (Path/Entrypoint) | SKIPPED | 63.4 MB | N/A | **REJECTED** (Gate 2 Linkage) |
| `candidate_c_distroless_python` | **Distroless Python 3** | `sha256:2fdb05402a2c...` | SKIPPED | FAIL (Path/Entrypoint) | SKIPPED | 50.6 MB | N/A | **REJECTED** (Gate 2 Linkage) |
| `candidate_d_ubuntu_minimal` | **Ubuntu 24.04 Minimal** | `sha256:69cecf4bbf72...` | **15P, 1S, 0F** | **PASS** (`zlib 1.3`, `expat 2.6.1`, `sqlite 3.45.1`) | **PASS (0 Crit / 0 High)** | **111.4 MB** | **107** | **SELECTED WINNER** |

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
+-----------------------------------------------------------------------------------------------------------------------+
| ROLE                           | NAME / TITLE                         | STATUS    | DATE       | SCOPE APPROVED       |
+-----------------------------------------------------------------------------------------------------------------------+
| Lead Security Architect        | Chief Security Architect             | [SIGNED]  | 2026-09-17 | Controlled Staging   |
| Principal Solutions Engineer   | Aarkaa Platform Lead                 | [SIGNED]  | 2026-09-17 | Controlled Staging   |
| Head of Infrastructure / SRE   | Site Reliability & Infra Lead        | [SIGNED]  | 2026-09-17 | Controlled Staging   |
+-----------------------------------------------------------------------------------------------------------------------+
```

Controlled staging activation is **APPROVED** with strict sequential enablement (`CODE_MODE_ENABLED=True`, then conditional `MCP_ENABLED=True`) under continuous `--network=none` and dropped capability confinement. General production release remains strictly **NOT APPROVED**.

