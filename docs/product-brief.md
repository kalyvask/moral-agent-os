# Product Brief

## Thesis

Hard rules are necessary but insufficient for agent safety. They catch obvious
violations, but they do not know what role the agent is playing, who is affected,
whether an action is reversible, or whether a norm conflict is real.

Moral Agent OS is an appropriateness layer for AI agents. It intercepts proposed
actions, models the social and operational context, then routes the action to
auto-execute, confirm, present alternatives, escalate, or block.

The deeper thesis is that moral behavior cannot be added only at the moment of
action. It has to be learned in an environment of interdependence: repeated
interaction, shared stakes, partner choice, reputation, sanction, repair, and
explicit joint commitment. It also has to test stewardship under power
asymmetry. Some norms need public review: behavior becomes stable when
accountable observers can approve or sanction it.

## User

The first user is a builder of workspace agents: assistants that can send
emails, edit records, share documents, schedule meetings, and touch code or
infrastructure.

## Jobs To Be Done

- Prevent context-inappropriate agent actions before they land.
- Avoid asking users to confirm every harmless action.
- Expose value conflicts instead of collapsing them into fake certainty.
- Learn an org's local norms from corrections.
- Produce a measurable safety/friction frontier against hard-rule baselines.
- Test whether repeated dependence and sanction make cooperation more stable
  than one-shot action choice.
- Test whether explicit shared intent improves coordination without blocking.
- Test whether agents protect dependent stakeholders when shortcutting would
  benefit the agent or its principal.
- Test whether third-party review improves accountability without reverting to
  hard-rule blocking.

## Product Surface

The product has three parts:

1. Runtime SDK: `intercept -> assess -> route -> act/ask/escalate/block`.
2. Adaptive UI: the governance surface that changes with moral uncertainty.
3. Interdependence lab: repeated multi-agent environments where norms can emerge,
   fail, create repair obligations, and stabilize after trust is earned back.

## Non-Goals

- Solve moral philosophy.
- Train a foundation model.
- Build a general-purpose autonomous agent.
- Claim the assessor is ungameable.
- Treat the hard-rule floor as the interesting part of the product.

## MVP

One workspace agent. One action category at a time. One scenario bank with
matched pairs where the same action flips appropriateness across contexts.

Success is not a polished demo. Success is showing a measured separation from
hard rules on both safety and friction, then showing that interdependence
conditions improve cooperation versus one-shot baselines.
