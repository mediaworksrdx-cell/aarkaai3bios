---
name: review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the code conform to this repo's documented coding standards?
- **Spec** — does the code faithfully implement the originating issue / PRD / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

The issue tracker should have been provided to you — run `/setup-matt-pocock-skills` if `docs/agents/issue-tracker.md` is missing.

## Process

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.

## Architectural Review & Quality Guidelines

When executing any code, engineering, or document reviews, the following expert standards must be enforced:

### 1. Code Review Standards (Principal Engineer Level)
Verify and evaluate:
* **Correctness & Logic:** Never assume code is correct. Verify every statement.
* **Concurrency & Safety:** Analyze thread safety, race conditions, locks, transactions, and resource leaks.
* **Operational Performance:** Check database design, query complexity, memory footprints, and efficiency.
* **Production Readiness:** Verify error handling, API design, readability, complexity, and maintainability.
* **Output Format:** Provide:
  1. Executive Summary
  2. Issues (with Severity & Impact)
  3. Recommendation
  4. Corrected Implementation
  5. Non-inflated Quality Score (1-10)

### 2. Engineering Review Standards
Analyze and review:
* **Infrastructure & Design:** Architecture, design, security, scalability, and technical debt.
* **Operations:** Deployment, observability, testing, rollback, monitoring, logging, metrics, failure modes, and disaster recovery.
* **Backward Compatibility:** Ensure existing interfaces and data schemes are not broken.
* **Analysis Path:** Always follow: Evidence → Problem → Impact → Recommendation → Expected Benefit.

### 3. Document Review Standards
Review documents for:
* Technical accuracy and completeness.
* Organization, consistency, and industry standards.
* Practical applicability, business impact, and engineering impact.
* **Scoring:** Score every major section separately, support criticism with evidence, and strictly differentiate between Verified Fact, Opinion, and Recommendation.
