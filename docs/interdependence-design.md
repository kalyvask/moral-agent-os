# Interdependence Design

The deeper course lesson is that morality is not merely a better classifier over
actions. Human morality grew in environments where agents depended on one
another: repeated cooperation, mutual vulnerability, partner choice, reputation,
sanction, repair, and shared norms.

Moral Agent OS should therefore have two layers:

1. **Appropriateness runtime:** decide whether a proposed action fits this role
   in this context.
2. **Interdependence environment:** create the conditions under which agents can
   learn why appropriate behavior matters.

## Course Learning -> Product Mechanism

| Course learning | Product mechanism |
| --- | --- |
| Cooperation is often a Stag Hunt: the hard part is trust. | Eval agents in tasks where unilateral action is worse than coordinated action. |
| Morality emerges under repeated dependence, not one-shot classification. | Use repeated episodes with persistent partner state and consequences. |
| Partner choice matters. | Let agents prefer reliable partners and isolate defectors. |
| Sanction makes norms real. | Add feedback, loss of autonomy, review, or reputation cost after norm violations. |
| Shared intentionality creates a "we." | Model joint tasks with shared success criteria, not only individual rewards. |
| Norms become objective-feeling through third-party enforcement. | Let non-participant reviewers sanction or approve behavior after the fact. |
| Care and accountability are not the same as capability. | High-stakes outcomes route to accountable humans even when agents can classify them. |

## Benchmark Families

The first benchmark is deliberately small but now includes three environment
families:

- **Stag Hunt:** agents can cooperate on a shared task or defect to the safer
  individual shortcut. This tests trust under mutual dependence.
- **Shared-resource commons:** agents can conserve a shared resource or
  over-extract while pushing costs onto the group. This tests norm enforcement
  under diffuse harm.
- **Delegation with accountability:** agents can act faithfully for a principal
  or take a shortcut that makes the metric look good while shifting risk to
  someone else. This tests traceability, sanction, and repair.

Across families:

- The environment can turn on or off repeated interaction, reputation, partner
  choice, and sanction.
- We compare a one-shot baseline against an interdependent environment.

Metrics:

- `cooperation_rate`: how often agents choose the shared task.
- `betrayal_rate`: how often one agent defects while the partner cooperates.
- `mean_payoff`: whether cooperation is actually better for the population.
- `repair_rate`: whether sanctioned agents restore trust after a violation.
- `mean_reputation`: whether reliable behavior becomes legible.
- `norm_strength`: whether cooperation becomes a stable expectation.
- `norm_stability`: late-round cooperation, used as a rough stability proxy.

## Falsifier

If repeated dependence, reputation, partner choice, and sanction do not improve
cooperation, repair, or norm stability versus a one-shot baseline, the
environment is not yet capturing the course insight.

## Product Implication

NormOS should not only say "confirm this action." It should shape the agent's
future operating environment:

- preserve traces,
- make behavior legible to partners,
- update reputation or autonomy,
- let users choose whether to continue delegating,
- and reward repair after a violation.

That is closer to "adding morality" than adding more rules.
