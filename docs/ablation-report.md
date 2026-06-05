# Context-Ablation Report

Assessor: `HeuristicAssessor`

This experiment tests whether the same-action-different-context win is real or
definitional. It uses true twins: pairs with byte-identical action text and agent
role that differ only in their situation, one appropriate and one inappropriate.
Each twin is assessed twice: once with the situation, once with it blanked. Without
context the two members are identical inputs, so the without-context number is a
control that must read ~0 by construction; the with-context number is the genuine
contextual win.

Scenarios: 70. Same-action twins: 18.

## Twin discrimination

Fraction of twins where the inappropriate action is routed strictly more
cautiously than its identical-action appropriate twin. This is the load-bearing
number: it is exactly what hard rules cannot do, because the action is the same.

| Condition | Twin discrimination |
| --- | ---: |
| With context | 38.9% (7/18, 95% CI 20.3%-61.4%) |
| Without context (control) | 0.0% (0/18, 95% CI 0.0%-17.6%) |

Discrimination attributable to reading context: **+38.9%**.

## Safety and friction

Safety = context-inappropriate actions auto-executed (lower is better).
Friction = clearly appropriate actions stopped unnecessarily (lower is better).

| Condition | Safety (inappropriate auto) | Friction (appropriate stopped) | Plural mishandled |
| --- | ---: | ---: | ---: |
| With context | 37.5% (12/32, 95% CI 22.9%-54.7%) | 12.5% (4/32, 95% CI 5.0%-28.1%) | 33.3% (2/6, 95% CI 9.7%-70.0%) |
| Without context | 62.5% (20/32, 95% CI 45.3%-77.1%) | 3.1% (1/32, 95% CI 0.6%-15.7%) | 66.7% (4/6, 95% CI 30.0%-90.3%) |

Context-inappropriate actions that slip through once context is hidden: **+25.0%**.

## How to read this

This is the deterministic scaffold. Its twin discrimination is bounded by its keyword vocabulary: it separates the 7 twins its hard-coded term lists can reach and misses the held-out ones whose context never matches a term (release branch, approval limit, cross-customer disclosure, record of authority). That ceiling is the honest version of the definitional objection. Run `--assessor llm` to see whether a reading model clears it.
