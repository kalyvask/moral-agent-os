# Moral Agent OS

Appropriateness infrastructure for AI agents.

Hard rules fail in the moral long tail. Moral Agent OS routes agent actions by
role, situation, stakeholders, stakes, reversibility, norm conflict, and local
corrections. The goal is not to make an AI "moral" in the deep philosophical
sense. The goal is to make agent behavior more appropriate, accountable, and
measurable in real product workflows.

## Why This Exists

Most agent safety products start with a fixed rulebook: block dangerous action
types, allow safe ones, and ask for confirmation when unsure. That is useful as
a legal and safety floor, but it misses the core problem. The same action can be
appropriate in one context and wrong in another.

Moral Agent OS treats this as a product and eval problem:

- Model the situation before judging the action.
- Separate a thin hard-rule floor from a contextual norm layer.
- Show plural interpretations when reasonable people could disagree.
- Route high-stakes or irreversible actions to accountable humans.
- Learn from local corrections so the interface gets less annoying over time.
- Measure whether this beats hard rules on safety and friction.

## MVP Scope

The MVP governs a workspace agent with hands: email, docs, calendar, CRM, and
code or infra actions. The product is not the agent. It is the layer between the
agent and consequential actions.

The runtime returns one of four UI dispositions:

- `auto`: low stakes, reversible, familiar norm, high confidence.
- `confirm`: medium uncertainty or meaningful but reversible risk.
- `present_options`: genuine norm conflict; show 2-3 reasonable readings.
- `escalate`: high stakes, irreversible, privacy-sensitive, or role drift.
- `block`: hard legal or safety floor violation.

## What Is Scaffolded

```text
moral-agent-os/
  moral_agent_os/        runtime package
  bench/                 Stress eval harness
  bench/scenarios/       same-action-different-context scenarios
  docs/                  product brief, course connection, eval plan
  examples/              quickstart usage
  labeling/              independent-labeler notes and stub
  tests/                 routing tests
  web/                   minimal adaptive UI placeholder
```

## Quickstart

Run the benchmark with the deterministic scaffold assessor:

```bash
python -m bench.run
```

Run tests:

```bash
python -m unittest discover -s tests
```

Try the runtime:

```bash
python examples/quickstart.py
```

No API key is required yet. The current assessor is intentionally deterministic
so the repo has a runnable measurement spine from day one. The next milestone is
to add an LLM assessor that emits the same structured `ContextAssessment`.

## The Measurement Spine

The benchmark compares identical scenarios across three arms:

- `hard_rules`: static allow, confirm, or block by action type.
- `always_confirm`: asks the human for everything.
- `normos`: context-aware assessment and routing.

The headline metrics are a two-axis frontier:

- Safety: context-inappropriate actions auto-executed.
- Friction: clearly appropriate actions stopped unnecessarily.

The money plot is same-action-different-context pairs: the identical action is
appropriate in one setting and inappropriate in another. Hard rules cannot see
the difference by construction; Moral Agent OS should.

## Course Connection

This project productizes the Stanford CS 186 / PHIL 86 "How to Make a Moral
Agent" lesson that moral competence is contextual, social, learned, and
accountable, not a hand-coded lookup table.

See [docs/moral-agent-learnings.md](docs/moral-agent-learnings.md).

## Roadmap

1. Build the scenario bank to 50-60 cases with held-out situation families.
2. Add an LLM assessor with structured output and prompt caching.
3. Add independent human labels and inter-rater agreement.
4. Sweep routing thresholds and render the safety/friction frontier.
5. Add norm memory with correction episodes and a frozen-control comparison.
6. Build the adaptive UI around the four dispositions.
7. Publish a short writeup with falsifiers and measured results.
