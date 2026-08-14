---
name: ai-ml
description: Review standards for AI and Machine Learning systems. Use when evaluating dataset pipelines, training methodologies, model evaluation, and inference workloads.
---

# AI & Machine Learning Review Standards

When reviewing or designing machine learning workflows, you must evaluate the system across these critical operational phases:

## 1. Dataset & Engineering
* **Data Quality:** Provenance, labeling accuracy, noise levels, and distribution characteristics.
* **Feature Engineering:** Selection, transformation, scaling, leakage prevention, and computational cost.

## 2. Training & Validation
* **Methodology:** Split strategies (e.g., cross-validation, walk-forward), regularization, and hyperparameter tuning.
* **Evaluation Metrics:** Alignment of metrics (Precision, Recall, F1, ROC-AUC, MAPE) with business objectives.

## 3. Inference & Production
* **Performance:** Latency bounds, memory footprints, hardware acceleration (CPU vs. GPU, VRAM limits), and quantization impact.
* **Model Governance:** Versioning, lineage tracking, and license compliance.
* **Monitoring & Drift:** Concept/data drift detection, performance decay tracking, and automated retraining strategies.
* **Ethics & Safety:** Explainability, bias mitigation, and safety guardrails.
