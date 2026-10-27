---
name: ruvnet-swarm
description: Multi-agent swarm orchestration and SPARC engineering workflow powered by ruflo and RuVector. Use when executing complex multi-file engineering tasks, running consensus reviews, or coordinating parallel agent swarms.
---

# RuVnet Swarm Orchestration & SPARC Workflow

This skill upgrades Aarka with **ruflo** multi-agent swarm orchestration and enforces the **SPARC** (Specification, Pseudocode, Architecture, Refinement, Completion) engineering methodology.

## 1. Swarm Topologies & Specialized Roles

Aarka dispatches tasks across specialized subagents rather than operating as an isolated linear agent:

| Role | Primary Function | Output Artifact | Verification Gate |
| :--- | :--- | :--- | :--- |
| **Supervisor** | Orchestrates the DAG task graph, manages transactional snapshots, and scores stage outputs. | `task_manifest.json` | Snapshot initialized; rollback registered. |
| **Architect** | Drafts formal specifications, invariant clauses, algorithmic pseudocode, and interface contracts. | `SPEC.md`, `PSEUDO.md`, `ARCH.ts` | Specification clauses verified; contracts compile via `tsc`. |
| **Implementer** | Generates production-grade, type-safe implementation logic conforming to architecture contracts. | `src/*.ts` | Zero stubs or placeholders; compiles with zero type errors. |
| **Verifier** | Formulates unit/property tests, measures coverage, and runs linters. | `tests/*.test.ts` | 100% test pass rate; line coverage $\ge 85\%$. |
| **Security Sentinel** | Audits changes against Rule 8 Zero-Discovery boundaries and capability permissions. | Audit Report | Passes capability token validation; 0 path escapes. |

## 2. SPARC Autonomous Execution Pipeline

Every significant engineering task executed by Aarka must progress through five verified stages:

```
+----------------------------------------------------------------------------------------------------+
|                                    AARKA SPARC PIPELINE                                            |
+----------------------------------------------------------------------------------------------------+
  [Stage 1: SPECIFICATION] ──► Requires explicit PRECONDITIONS, POSTCONDITIONS, INVARIANTS, BOUNDARIES.
             │
             ▼
  [Stage 2: PSEUDOCODE]    ──► Requires ALGORITHM, asymptotic bounds O(...), and LOOP INVARIANTS.
             │
             ▼
  [Stage 3: ARCHITECTURE]  ──► Interface contracts, module seams, and acyclic dependency graphs.
             │
             ▼
  [Stage 4: REFINEMENT]    ──► TDD execution, unit test pass rate = 100%, coverage >= 85%, lint clean.
             │
             ▼
  [Stage 5: COMPLETION]    ──► Verifies composite score >= 8.5/10. Rollback triggered on any failure.
```

## 3. Invocation Protocol

When Aarka executes a complex or multi-file coding task:
1. Initialize a multi-file transaction with `TransactionalSnapshotManager`.
2. Retrieve context via the `HybridMemoryRouter` combining symbolic MCP graph constraints and RuVector associative code embeddings.
3. Advance sequentially through the SPARC stages. If any stage fails, roll back the working tree to exact byte parity.
4. Commit the transaction only upon passing all gates with an empirical score $\ge 8.5 / 10$.
