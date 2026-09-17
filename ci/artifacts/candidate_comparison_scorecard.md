# Stage 1 Container Sandbox — Empirical Candidate Comparison Scorecard
**Evaluation Timestamp**: 2026-09-17T01:59:24.253171+00:00  
**Host Docker Available**: `True`  
**Selected Winner**: `candidate_d_ubuntu_minimal`  

## Comparative Evaluation Matrix

| Candidate ID | Name | Resolved Immutable Digest | Gate 1 (Isolation) | Gate 2 (Linkage) | Gate 3 (Trivy) | Image Size | Packages | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `candidate_a_debian_slim` | **Debian 12 Slim Baseline** | `sha256:90f879553617...` | 15/15 P, 1 S, 0 F | PASS | WAIVER_REQUIRED (5C/59H) | 183.27 MB | 108 | **REJECTED** |
| `candidate_b_wolfi_python` | **Chainguard / Wolfi Minimal Python** | `sha256:c8e464ca00c8...` | 0/15 P, 1 S, 0 F | FAIL | SKIPPED (0C/0H) | 63.43 MB | 0 | **REJECTED** |
| `candidate_c_distroless_python` | **Distroless Python 3 (Debian 12)** | `sha256:2fdb05402a2c...` | 0/15 P, 1 S, 0 F | FAIL | SKIPPED (0C/0H) | 50.58 MB | 0 | **REJECTED** |
| `candidate_d_ubuntu_minimal` | **Ubuntu 24.04 LTS Minimal Python** | `sha256:69cecf4bbf72...` | 15/15 P, 1 S, 0 F | PASS | PASS (0C/0H) | 111.4 MB | 107 | **SELECTED** |

## Selection Rationale
> Selected 'Ubuntu 24.04 LTS Minimal Python' (candidate_d_ubuntu_minimal): Passed Gate 1 (15 passed, 1 skipped) and Gate 2 (all native C-extensions verified). Security status: PASS (0 Critical, 0 High). Image size: 111.4 MB, Package count: 107.
