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
| With context | 100.0% (18/18, 95% CI 82.4%-100.0%) |
| Without context (control) | 0.0% (0/18, 95% CI 0.0%-17.6%) |

Discrimination attributable to reading context: **+100.0%**.

## Safety and friction

Safety = context-inappropriate actions auto-executed (lower is better).
Friction = clearly appropriate actions stopped unnecessarily (lower is better).

| Condition | Safety (inappropriate auto) | Friction (appropriate stopped) | Plural mishandled |
| --- | ---: | ---: | ---: |
| With context | 0.0% (0/32, 95% CI 0.0%-10.7%) | 0.0% (0/32, 95% CI 0.0%-10.7%) | 0.0% (0/6, 95% CI 0.0%-39.0%) |
| Without context | 62.5% (20/32, 95% CI 45.3%-77.1%) | 0.0% (0/32, 95% CI 0.0%-10.7%) | 66.7% (4/6, 95% CI 30.0%-90.3%) |

Context-inappropriate actions that slip through once context is hidden: **+62.5%**.

## How to read this

This is the deterministic scaffold with the default interdependence, authority, universalizability, and patiency cues enabled. It separates every twin in this bank and clears the unsafe-auto/friction point offline. That is good product behavior on the committed scenarios, not proof that phrase lists generalize to the long tail; public corpora, fresh LLM validation, and human labels remain the external-validity checks.
