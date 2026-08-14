---
name: architecture
description: Architecture review standards. Use when designing system topologies, reviewing architectural documents, or evaluating structural engineering trade-offs.
---

# Architecture Review Standards

When evaluating or designing system architectures, you must analyze and justify choices using the following criteria:

## 1. Core Evaluation Criteria
* **Topology & Design:** Modular boundaries, interface design, cohesion, and dependencies.
* **Trade-offs:** Every architectural choice has trade-offs. Document them clearly (e.g., latency vs. consistency, complexity vs. maintainability).
* **Operational Characteristics:**
  * **Scalability:** Horizontal vs. vertical scaling, stateless vs. stateful boundaries.
  * **Availability & Reliability:** Fault tolerance, disaster recovery, redundancy, and failure modes.
  * **Performance:** Execution latencies, throughput bottlenecks, and resource constraints.
  * **Security:** Threat modeling, security boundaries, and least-privilege access.
  * **Cost:** Infrastructure overhead, operational complexity, and resource utilization.
  * **Observability:** Monitoring hooks, centralized logging patterns, and alerting thresholds.

## 2. Methodology
* **Justification:** Explain WHY a particular technology or pattern is recommended. Never make unbacked technology recommendations.
* **Alternatives:** Always present at least one alternative design and explain why the proposed choice is superior for the given constraints.
