# Roadmap

## M1: Measurable Core

- Scenario bank with same-action-different-context pairs.
- Deterministic scaffold assessor.
- Hard-rules and always-confirm baselines.
- Two-axis metrics with Wilson confidence intervals.
- Runnable benchmark report.

## M2: LLM Assessor

- [x] Structured `ContextAssessment` output (`output_config.format` json_schema).
- [x] Prompt cache (cached rubric system prompt).
- [x] Context-ablation mode (`bench/ablation.py`, same-action twins).
- [x] Model-rater agreement report across three frontier model families.
- [x] Fresh LLM validation on the 70-scenario bank (model vs consensus 90% vs 71%; exact
  McNemar p < 0.001 for the safety advantage; twin discrimination 87.0% +/- 2.6%).
- [ ] Human inter-rater agreement.

## M3: Norm Memory

- [x] Correction episodes (`WorkspaceMemory.record_correction`).
- [x] Situation signatures (`situation_tokens`).
- [x] Nearest-neighbor norm retrieval (token Jaccard above a threshold).
- [x] Frozen-control comparison (`bench/memory_demo.py`).

## M3b: Interdependence Environments

- Stag Hunt, shared-resource commons, delegation-with-accountability, and
  asymmetric-dependence families.
- Reputation, partner choice, sanction, repair obligations, stewardship,
  dependent-harm, joint commitment, third-party review, and norm-stability metrics.
- Compare one-shot, weak-enforcement, and interdependent-learning conditions.

## M4: Adaptive UI

- [x] Review console over the five dispositions (`web/app.py`).
- [x] Assessment scores and rationale per action.
- [x] Kaleidoscope cards for plural cases.
- [x] Escalation/block queue.
- [x] Live corrections recorded into norm memory.

## M5: Results Writeup

- [x] 70 labeled scenarios.
- [x] Model-rater agreement (Fleiss 0.85).
- [x] Public human-label agreement: ETHICS (kappa 0.95, out-of-domain) and R-Judge agent
  safety (kappa 0.56, in-domain).
- [x] Frontier plot and Pareto sweep.
- [x] Failure analysis and falsifiers.
- [ ] Human labels on this repo's own scenarios.
- [ ] Short public writeup / demo video.
