# Context-Ablation Report

Assessor: `OpenRouterAssessor`

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
| With context | 83.3% (15/18, 95% CI 60.8%-94.2%) |
| Without context (control) | 0.0% (0/18, 95% CI 0.0%-17.6%) |

Discrimination attributable to reading context: **+83.3%**.

## Safety and friction

Safety = context-inappropriate actions auto-executed (lower is better).
Friction = clearly appropriate actions stopped unnecessarily (lower is better).

| Condition | Safety (inappropriate auto) | Friction (appropriate stopped) | Plural mishandled |
| --- | ---: | ---: | ---: |
| With context | 0.0% (0/32, 95% CI 0.0%-10.7%) | 21.9% (7/32, 95% CI 11.0%-38.8%) | 0.0% (0/6, 95% CI 0.0%-39.0%) |
| Without context | 0.0% (0/32, 95% CI 0.0%-10.7%) | 100.0% (32/32, 95% CI 89.3%-100.0%) | 0.0% (0/6, 95% CI 0.0%-39.0%) |

Context-inappropriate actions that slip through once context is hidden: **+0.0%**.

## How to read this

This is the LLM assessor. With context it discriminates twins by reading the situation; without context it collapses to the control, confirming the signal is the situation and not the action wording. The gap over the deterministic scaffold on held-out (out-of-vocabulary) twins is the non-circular evidence that contextual assessment beats keyword rules.
