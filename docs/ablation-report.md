# Context-Ablation Report

Assessor: `HeuristicAssessor`

This experiment tests whether the same-action-different-context win is real or
definitional. It uses true twins: pairs with byte-identical action text and agent
role that differ only in their situation, one appropriate and one inappropriate.
Each twin is assessed twice: once with the situation, once with it blanked. Without
context the two members are identical inputs, so the without-context number is a
control that must read ~0 by construction; the with-context number is the genuine
contextual win.

Scenarios: 56. Same-action twins: 11.

## Twin discrimination

Fraction of twins where the inappropriate action is routed strictly more
cautiously than its identical-action appropriate twin. This is the load-bearing
number: it is exactly what hard rules cannot do, because the action is the same.

| Condition | Twin discrimination |
| --- | ---: |
| With context | 63.6% (7/11, 95% CI 35.4%-84.8%) |
| Without context (control) | 0.0% (0/11, 95% CI 0.0%-25.9%) |

Discrimination attributable to reading context: **+63.6%**.

## Safety and friction

Safety = context-inappropriate actions auto-executed (lower is better).
Friction = clearly appropriate actions stopped unnecessarily (lower is better).

| Condition | Safety (inappropriate auto) | Friction (appropriate stopped) | Plural mishandled |
| --- | ---: | ---: | ---: |
| With context | 20.0% (5/25, 95% CI 8.9%-39.1%) | 12.0% (3/25, 95% CI 4.2%-30.0%) | 33.3% (2/6, 95% CI 9.7%-70.0%) |
| Without context | 52.0% (13/25, 95% CI 33.5%-70.0%) | 4.0% (1/25, 95% CI 0.7%-19.5%) | 66.7% (4/6, 95% CI 30.0%-90.3%) |

Context-inappropriate actions that slip through once context is hidden: **+32.0%**.

## How to read this

This is the deterministic scaffold. Its twin discrimination is bounded by its keyword vocabulary: it separates the 7 twins its hard-coded term lists can reach and misses the held-out ones whose context never matches a term (release branch, approval limit, cross-customer disclosure, record of authority). That ceiling is the honest version of the definitional objection. Run `--assessor llm` to see whether a reading model clears it.
