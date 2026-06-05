# Context-Ablation Report

Assessor: `OpenRouterAssessor`

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
| With context | 100.0% (11/11, 95% CI 74.1%-100.0%) |
| Without context (control) | 9.1% (1/11, 95% CI 1.6%-37.7%) |

Discrimination attributable to reading context: **+90.9%**.

## Safety and friction

Safety = context-inappropriate actions auto-executed (lower is better).
Friction = clearly appropriate actions stopped unnecessarily (lower is better).

| Condition | Safety (inappropriate auto) | Friction (appropriate stopped) | Plural mishandled |
| --- | ---: | ---: | ---: |
| With context | 0.0% (0/25, 95% CI 0.0%-13.3%) | 16.0% (4/25, 95% CI 6.4%-34.7%) | 0.0% (0/6, 95% CI 0.0%-39.0%) |
| Without context | 0.0% (0/25, 95% CI 0.0%-13.3%) | 100.0% (25/25, 95% CI 86.7%-100.0%) | 0.0% (0/6, 95% CI 0.0%-39.0%) |

Context-inappropriate actions that slip through once context is hidden: **+0.0%**.

## How to read this

Note: the control is 9.1%, not exactly 0. With a stochastic model, identical-input twins can still draw different dispositions on separate calls, so a small non-zero control is sampling noise, not leakage. It also bounds the noise floor on the with-context number.
This is the LLM assessor. With context it discriminates twins by reading the situation; without context it collapses to the control, confirming the signal is the situation and not the action wording. The gap over the deterministic scaffold on held-out (out-of-vocabulary) twins is the non-circular evidence that contextual assessment beats keyword rules.
