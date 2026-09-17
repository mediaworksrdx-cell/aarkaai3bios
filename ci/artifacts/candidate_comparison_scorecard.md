# Stage 1 Container Sandbox — Empirical Candidate Comparison Scorecard
**Evaluation Timestamp**: 2026-09-17T01:49:06.218448+00:00  
**Host Docker Available**: `False`  
**Selected Winner**: `None`  

## Comparative Evaluation Matrix

| Candidate ID | Name | Resolved Immutable Digest | Gate 1 (Isolation) | Gate 2 (Linkage) | Gate 3 (Trivy) | Image Size | Packages | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `candidate_a_debian_slim` | **Debian 12 Slim Baseline** | `sha256:90f879553617...` | 0/15 P, 1 S, 0 F | SKIPPED | SKIPPED (0C/0H) | 0.0 MB | 0 | **PENDING** |
| `candidate_b_wolfi_python` | **Chainguard / Wolfi Minimal Python** | `resolving...` | 0/15 P, 1 S, 0 F | SKIPPED | SKIPPED (0C/0H) | 0.0 MB | 0 | **PENDING** |
| `candidate_c_distroless_python` | **Distroless Python 3 (Debian 12)** | `resolving...` | 0/15 P, 1 S, 0 F | SKIPPED | SKIPPED (0C/0H) | 0.0 MB | 0 | **PENDING** |
| `candidate_d_ubuntu_minimal` | **Ubuntu 24.04 LTS Minimal Python** | `resolving...` | 0/15 P, 1 S, 0 F | SKIPPED | SKIPPED (0C/0H) | 0.0 MB | 0 | **PENDING** |

## Selection Rationale
> All candidates failed functional isolation (Gate 1) or linkage compatibility (Gate 2).
