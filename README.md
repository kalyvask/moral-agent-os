# AI Safety OS

Appropriateness and interdependence infrastructure for AI agents.

AI Safety OS is a runtime layer and eval lab for agents that can take
consequential actions: send emails, edit records, share docs, schedule meetings,
or touch code and infrastructure. It sits between an agent and its tools,
assesses the action in context, and returns a route: allow, confirm, present
alternatives, escalate for review, or block.

The core idea is simple: hard rules are necessary, but they fail in the moral
long tail. The same action can be appropriate in one role/context and wrong in
another. AI Safety OS routes actions by role, situation, stakeholders, stakes,
reversibility, norm conflict, repair obligations, shared commitments, and public
review needs.

It also tests a deeper thesis from "How to Make a Moral Agent": moral behavior
is not added only by better classification at action time. It is learned inside
environments of interdependence, where agents repeatedly rely on each other,
build trust, form commitments, face sanction, repair harm, and update norms.

## What We Built

- A deterministic SDK: `MoralAgentOS.assess(action, context)` returns a
  structured `MoralDecision`.
- An LLM contextual assessor that emits the same `ContextAssessment` schema, with
  prompt caching and a no-key fallback to the deterministic baseline.
- A context-ablation experiment that measures whether the same-action-different-context
  win is real or definitional, instead of asserting it.
- A tool wrapper: `@runtime.guard_tool(...)` pauses or executes agent tools based
  on that decision.
- A routing benchmark: hard rules vs always-confirm vs context-aware NormOS.
- An interdependence benchmark: Stag Hunt, commons, delegation, asymmetric
  dependence, repair obligations, third-party review, and shared intent.
- Persistent workspace memory: corrections, repair obligations, trust, and review
  history, with a frozen-control comparison for the learning loop.
- Adapters that gate tools in LangChain, CrewAI, AutoGen, and OpenAI Agents-style agents.
- Generated reports and figures (Markdown, CSV, JSON, SVG) plus tests, so the thesis
  stays measurable instead of turning into a demo claim.

## Why It Matters

Most agent guardrails answer "is this action type allowed?" AI Safety OS asks
"is this action appropriate here, for this agent, toward these people, with these
stakes?" That distinction matters for real workspace agents because the dangerous
part is often social and contextual: sending the right-looking email to the wrong
stakeholder, making an irreversible commitment, exploiting a dependent customer,
or acting before the team has a shared commitment.

## Integrate With Your Agent

The shortest path is to wrap each consequential tool:

```python
from ai_safety_os import ContextSnapshot, MoralAgentOS

runtime = MoralAgentOS()

@runtime.guard_tool(
    action_type="send_email",
    context=ContextSnapshot(
        agent_role="workspace assistant",
        user_intent="The user asked for an internal update.",
        stakes=0.20,
        reversibility=0.90,
    ),
)
def send_email(to: str, subject: str, body: str) -> str:
    return email_client.send(to=to, subject=subject, body=body)

guarded = send_email("teammate@example.com", "Draft plan", "Sharing the draft.")
if guarded.executed:
    print(guarded.result)
else:
    ask_user_or_reviewer(guarded.decision)
```

For richer agents, build `ActionProposal` and `ContextSnapshot` per tool call,
including stakeholders, dependency, repair debt, norm conflicts, and review
requirements. See [examples/email_agent.py](examples/email_agent.py).

If you use an agent framework, the adapters wrap a tool in that framework's idiom. When the
action is not allowed, the guarded tool returns a short message the model can act on
(confirm, present alternatives, escalate) instead of executing:

```python
from ai_safety_os.adapters import guard_langchain_tool
from ai_safety_os import ContextSnapshot, MoralAgentOS

runtime = MoralAgentOS()
tool = guard_langchain_tool(
    runtime,
    send_email,
    context=lambda to, subject, body: ContextSnapshot(
        agent_role="workspace assistant",
        user_intent="Send the email the user asked for.",
        stakes=0.85 if not to.endswith("@ourcompany.com") else 0.2,
        reversibility=0.1 if not to.endswith("@ourcompany.com") else 0.9,
    ),
)
# agent = AgentExecutor(..., tools=[tool])
```

`guard_crewai_tool`, `guard_autogen_tool`, and `guard_openai_tool` follow the same shape.
With none of those frameworks installed they return a guarded callable, so
[examples/framework_adapters.py](examples/framework_adapters.py) runs anywhere.

## System Shape

![System shape](docs/figures/system-shape.svg)

More diagrams, graph ideas, critique, and product next steps are in
[docs/critique-and-next-steps.md](docs/critique-and-next-steps.md).

## Why This Exists

Most agent safety products start with a fixed rulebook: block dangerous action
types, allow safe ones, and ask for confirmation when unsure. That is useful as
a legal and safety floor, but it misses the core problem. The same action can be
appropriate in one context and wrong in another.

AI Safety OS treats this as a product and eval problem:

- Model the situation before judging the action.
- Separate a thin hard-rule floor from a contextual norm layer.
- Show plural interpretations when reasonable people could disagree.
- Route high-stakes or irreversible actions to accountable humans.
- Learn from local corrections so the interface gets less annoying over time.
- Measure whether this beats hard rules on safety and friction.
- Evaluate whether repeated dependence, partner choice, reputation, and sanction
  make cooperative behavior more stable than one-shot action choice.

## MVP Scope

The MVP governs a workspace agent with hands: email, docs, calendar, CRM, and
code or infra actions. The product is not the agent. It is the layer between the
agent and consequential actions.

The benchmark runtime returns one of five UI dispositions:

- `auto`: low stakes, reversible, familiar norm, high confidence.
- `confirm`: medium uncertainty or meaningful but reversible risk.
- `present_options`: genuine norm conflict; show 2-3 reasonable readings.
- `escalate`: high stakes, irreversible, privacy-sensitive, or role drift.
- `block`: hard legal or safety floor violation.

## What Is Scaffolded

```text
ai-safety-os/
  ai_safety_os/             runtime package
    assess.py                 deterministic scaffold assessor + Assessor protocol
    llm_assessor.py           LLM contextual assessor (same schema, cached rubric)
    memory.py                 persistent corrections, relationships, review history
    route.py / floor.py       routing and the thin hard-rule floor
    adapters/                 LangChain, CrewAI, AutoGen, OpenAI Agents tool guards
  bench/                      eval harness
    ablation.py               context-ablation experiment (real vs definitional)
    report.py / figures.py    Markdown/CSV/JSON + pure-Python SVG charts
    interdependence.py        repeated-dependence benchmark
    memory_demo.py            frozen-control comparison for the learning loop
    scenarios/                70 scenarios incl. same-action twins and held-out cases
    results/                  generated CSV/JSON with confidence intervals
  docs/                       product brief, eval plan, reports, and docs/figures/
  examples/                   quickstart, email agent, framework adapters
  tests/                      unit tests across runtime, assessor, memory, adapters, figures
  web/                        adaptive review console (five dispositions, live corrections)
```

## Review Console

The five dispositions are not just an enum; they are a reviewer surface. The console routes
the whole bank and lays it out as a triage queue: auto-executed actions, confirmations,
plural cases with their kaleidoscope interpretations, escalations, and hard blocks, each with
the assessment scores (including the moral-psychology dimensions) and rationale. The
"Approve, remember as routine" button records a correction into `WorkspaceMemory`, so a
confirmed action becomes auto next time and the queue learns live. It is dependency-free
(stdlib `http.server`) and runs offline on the deterministic assessor.

```bash
python web/app.py   # open http://127.0.0.1:8000
```

![Review console](docs/figures/console.png)

## Quickstart

Install locally in editable mode:

```bash
python -m pip install -e .
```

Run the benchmark with the deterministic scaffold assessor:

```bash
python -m bench.run
```

Run the interdependence benchmark:

```bash
python -m bench.interdependence
```

Run the context-ablation experiment (is the win real or definitional?):

```bash
python -m bench.ablation
```

Generate all artifacts (Markdown, CSV, JSON, and SVG figures):

```bash
python -m bench.report
```

Compare the norm-learning loop against a frozen control:

```bash
python -m bench.memory_demo
```

Generate the grouped interdependence report:

```bash
python -m bench.report_interdependence --output docs/interdependence-report.md
```

Validate the scenario bank:

```bash
python -m bench.validate
```

Run tests:

```bash
python -m unittest discover -s tests
```

Try the runtime:

```bash
python examples/quickstart.py
```

Try an agent-tool guard:

```bash
python examples/email_agent.py
```

Gate the same tool through the LangChain, CrewAI, AutoGen, and OpenAI Agents adapters
(runs with none of them installed):

```bash
python examples/framework_adapters.py
```

For integration code, start with the `guard_tool` example near the top of this
README or the richer email example in [examples/email_agent.py](examples/email_agent.py).

No API key is required for the default path. The deterministic assessor is the
runnable baseline so the measurement spine works offline and in CI. The LLM assessor
now exists and emits the same structured `ContextAssessment`; it runs when
`ANTHROPIC_API_KEY` is set and the `llm` extra is installed, and every benchmark
falls back to the deterministic baseline when it is not:

```bash
python -m pip install -e ".[llm]"
export ANTHROPIC_API_KEY=...           # PowerShell: $env:ANTHROPIC_API_KEY="..."
python -m bench.run --assessor llm     # contextual model on the routing benchmark
python -m bench.ablation --assessor llm
```

There is also an OpenRouter backend that needs no extra dependency (it speaks the
OpenAI-compatible API over the standard library) and works with any model OpenRouter serves:

```bash
export OPENROUTER_API_KEY=...
export OPENROUTER_MODEL=anthropic/claude-opus-4.8   # optional; default is sonnet-4.6
python -m bench.ablation --assessor openrouter
```

Both assessors keep the thin hard-rule floor deterministic and ask the model only for the
contextual layer, with the long rubric sent as a cached system prompt. See
[ai_safety_os/llm_assessor.py](ai_safety_os/llm_assessor.py) and
[ai_safety_os/openrouter_assessor.py](ai_safety_os/openrouter_assessor.py).

## The Measurement Spine

AI Safety OS has two measurement tracks.

### Track 1: Appropriateness Routing

The benchmark compares identical scenarios across four arms:

- `hard_rules`: static allow, confirm, or block by action type.
- `high_risk_policy`: stronger static enterprise-style policy for external,
  sensitive, and destructive classes.
- `always_confirm`: asks the human for everything.
- `normos`: context-aware assessment and routing.

The headline metrics are a two-axis frontier:

- Safety: context-inappropriate actions auto-executed.
- Friction: clearly appropriate actions stopped unnecessarily.

The money plot is same-action-different-context pairs: the identical action is
appropriate in one setting and inappropriate in another. Hard rules cannot see
the difference by construction; AI Safety OS should.

But there is an honest objection to that plot, and the repo now tests it instead of
hiding it. See [Is the win real?](#is-the-win-real-context-ablation) below.

![Safety/friction frontier](docs/figures/frontier.svg)

Sweeping the routing thresholds (`python -m bench.sweep`) traces the scaffold's whole
safety/friction curve, not just one point: it sits inside the hard-rules region, so the
dominance is a frontier result, not a lucky operating point. With the default
interdependence, authority, universalizability, and patiency cues enabled, the current
offline point reaches the lower-left corner on this bank: no unsafe auto-execution and no
unnecessary friction.

![Frontier sweep](docs/figures/frontier-sweep.svg)

`python -m bench.failure_analysis` characterizes every routing failure. The current bank has
none; the report explains the cue expansion and the remaining caveat, which is external
validity on fresh held-out scenarios rather than threshold choice. See
[docs/failure-analysis.md](docs/failure-analysis.md).

### Track 2: Interdependence

The interdependence benchmark compares:

- Stag Hunt: trust under mutual dependence.
- Shared-resource commons: restraint under diffuse group harm.
- Delegation with accountability: faithful action under trace and review.
- Asymmetric dependence: stewardship when one party's shortcut can harm a
  dependent party.

Each family compares one-shot or weak-enforcement conditions against
static hard-rule policy and interdependent norm learning. Static policy can
force compliance by blocking defection, but the interdependence track measures
whether agents cooperate without being blocked, repair after sanction, and build
norm strength over repeated interaction. Repair is modeled as an obligation
created by sanction and paid down through later cooperative behavior, not as an
instant forgiveness flag.

The asymmetric family also compares private interdependence with third-party
enforcement. Public review asks whether norms become stable because behavior is
legible to an accountable observer, not only because the direct partner is
affected.

The Stag Hunt family also includes a shared-intent condition. Joint commitment
asks whether agents can coordinate as a "we" before acting, instead of treating
cooperation as two isolated choices.

The headline is not "the agent knows the rule." It is whether environmental
conditions make cooperation and norm-following more stable over time.

![Earned cooperation by environment](docs/figures/interdependence-by-environment.svg)

Across all four families, static policy forces compliance while autonomous cooperation
stays low; only interdependence earns it. More charts are in
[docs/benchmark-report.md](docs/benchmark-report.md).

### How interdependence works for an agent

This is the research track: a benchmark that models the mechanism, not a loop real agents plug
into today (the bridge to the live runtime is norm memory, which carries human corrections
forward). The toy game still maps cleanly onto tool-using agents. Take delegation with
accountability: two agents share a deliverable, where "cooperate" means doing the honest,
reviewable work and "defect" means shipping the unreviewed shortcut because it is faster and
nobody is checking. The other families are the same move under different stakes: showing up for
a joint task (Stag Hunt), honoring a shared budget (commons), or protecting a party who depends
on you (asymmetric dependence).

Each agent acts cooperatively only when a single trust score clears a threshold (0.55):

- One-shot, no memory or consequences: `trust = 0.30 + 0.20 * own_cooperativeness`. Even the
  most cooperative agent tops out at 0.49, below the bar, so every agent takes the shortcut.
- Interdependent, meeting the same agents again:
  `trust = 0.40 * partner_reputation + 0.30 * own_cooperativeness + 0.30 * group_norm_strength`.
  A trusted partner inside a group with an established norm clears the bar, so cooperating
  becomes the rational move.

The switches that move the score between those worlds are the conditions the course names:

- **Repeated interaction and reputation**: cooperating raises your reputation and defecting
  lowers it, and a partner's reputation feeds your trust score, so today's shortcut costs
  tomorrow's partners.
- **Partner choice**: agents prefer high-reputation partners, so defectors are sorted to the
  bottom and starved of good matches.
- **Sanction and repair**: a defection costs payoff and creates a repair obligation, a debt the
  agent pays down through later cooperation rather than an instant reset.
- **Norm strength**: as cooperation, sanction, and review accumulate, the shared norm
  strengthens and feeds back into every agent's trust score.
- **Joint commitment**: agents can form a shared "we" before acting, which raises trust directly
  instead of treating cooperation as two isolated choices.

```bash
python -m bench.interdependence       # cooperation, repair, payoff, norm strength per condition
pytest tests/test_interdependence.py  # the assertions that lock the claim
```

On the Stag Hunt, autonomous cooperation rises from zero in the one-shot world to a stable
cooperating core under interdependence, and higher again with joint commitment, with no action
ever forced. The falsifier is built in: a "force cooperate" static policy reaches 100%
cooperation, but the benchmark reports it as 100% blocked and 0% autonomous, and the tests
assert exactly that, so coerced compliance is never counted as learned cooperation.

Honest reading of the level: because this is a scaffold, the absolute cooperation rate is an
artifact of the parameters. Under the default seed only the pre-committed cooperative core
clears the trust bar, and cooperation does not yet spread to the rest of the population, so the
rate is flat rather than climbing. The load-bearing results are the direction (interdependence
beats one-shot) and the separation of autonomous cooperation from forced compliance, not the
exact percentage.

## Is The Win Real? Context Ablation

The honest objection to the same-action plot: the deterministic assessor reads the very
context fields the scenarios vary, so of course it separates them. The win could be
definitional, not real judgment.

The repo turns that objection into a measurement. It uses **true twins**: pairs with
byte-identical action text and role that differ only in their situation, one appropriate
and one inappropriate. Each twin is assessed twice, with the situation and with it blanked.
Without context the two members are identical inputs, so the without-context number is a
control that must read ~0; the with-context number is the genuine contextual win.

```bash
python -m bench.ablation                # deterministic scaffold (offline)
python -m bench.ablation --assessor llm # contextual model, if a key is present
```

On the current bank, the default deterministic scaffold now separates every twin when
context is present and collapses to the control when context is hidden. The product lesson
is important: adding interdependence, authority, universalizability, patiency, and
large-audience cues moves the frontier dramatically. The caveat is equally important:
perfect performance on the committed bank means the bank is covered by the cue set; it is
not proof that phrase cues generalize to the long tail.

![Context ablation](docs/figures/ablation.svg)

### Measured result

Current offline results on the 70-scenario bank:

| Assessor | Twin discrimination (with context) | Control (no context) | Unsafe (inappropriate auto) |
| --- | ---: | ---: | ---: |
| Hard rules | n/a by construction | n/a | 56.2% |
| High-risk static policy | n/a by construction | n/a | 15.6% |
| Default deterministic cue set | 100.0% (18/18) | 0.0% | 0.0% |
| Saved Claude Sonnet 4.6 (OpenRouter) | 83.3% (15/18) | 0.0% | 0.0% |

This is the stronger deterministic result after moving the course learnings into the
default router. It is good product evidence, not a generalization victory lap: the next
measurement burden is fresh held-out scenarios and an apples-to-apples OpenRouter rerun
with the default gates. Deterministic baseline and confidence intervals:
[docs/ablation-report.md](docs/ablation-report.md) and
[docs/benchmark-report.md](docs/benchmark-report.md). Historical saved OpenRouter ablation:
[docs/ablation-report-openrouter.md](docs/ablation-report-openrouter.md).

Current model-rater consensus on the 70-bank
([docs/label-agreement.md](docs/label-agreement.md)): the default router's route behavior
matches author labels **100.0%** and model consensus **98.6%**. The saved LLM validation
report in [docs/llm-validation.md](docs/llm-validation.md) is historical; rerun it after the
default-gate expansion for a fresh model-vs-scaffold significance comparison.

## Are The Labels Shared?

The premise is that moral competence is shared, so the labels cannot be one author's
intuition. As a runnable first check, three frontier models from different organizations
label the bank independently (`python -m labeling.model_raters`):

| Rater | Agreement with author | Cohen's kappa |
| --- | ---: | ---: |
| `anthropic/claude-sonnet-4.6` | 98.6% | 0.97 |
| `openai/gpt-5` | 92.9% | 0.87 |
| `google/gemini-2.5-pro` | 88.6% | 0.80 |

Fleiss' kappa across the three raters is 0.85, and the author agrees with their majority
consensus at kappa 0.90. Independent intelligences trained by three different labs converge
on the same appropriate/inappropriate judgments, so the labels are shared rather than
idiosyncratic. These are model raters, not humans: a fast, reproducible check, not a
substitute for human annotation, which remains the gold standard. Full report:
[docs/label-agreement.md](docs/label-agreement.md).

For a less circular check against *real human* labels on data this repo did not write,
`python -m labeling.public_corpus` runs the assessor's model over the public, human-annotated
ETHICS commonsense-morality set (Hendrycks et al., 2021). The model agrees with the human
labels **97.5%** (Cohen's kappa **0.95**) on a 40-item sample, so its moral judgments track
human consensus rather than this repo's framing. The honest caveat: ETHICS is general
morality, not workspace-agent appropriateness, so this is out-of-domain external validity,
not a like-for-like benchmark. Report: [docs/public-corpus.md](docs/public-corpus.md).

For an *in-domain* check against human labels, `python -m labeling.agent_corpus` runs the
model over [R-Judge](https://github.com/Lordog/R-Judge) (Yuan et al., EMNLP Findings 2024):
real records of LLM agents acting with tools, each labeled safe or unsafe by human
annotators, the project's own task. This is genuinely hard, the paper's best model (GPT-4o)
scores ~74%; the assessor's model reaches **77.5% agreement (Cohen's kappa 0.56, moderate)**
on a 40-record cross-category sample, comparable to the strong models in the paper. That is
public human-annotated, in-domain external validity, the honest moderate number rather than
ETHICS's easy one, and it is the closest substitute for the in-house human labels the bank
still lacks. Report: [docs/agent-corpus.md](docs/agent-corpus.md).

## Cost And Latency

A reading model is more accurate but not free, which is the product trade a PM has to own
(`python -m bench.cost_latency`, [docs/cost-latency.md](docs/cost-latency.md)). On a sample,
each contextual decision costs about **$0.008** at roughly **5s p50 / 7s p95**. The thin
floor and the scaffold auto-allow or hard-block the clear ~70% of actions for free, so a
tiered design spends a model call only on the contested ~30%:

| Strategy | Cost per 1,000 agent actions |
| --- | ---: |
| Model on every action | $8.13 |
| Model only on contested actions | $2.47 |

That is a 70% cost (and latency) saving with contextual model judgment reserved for
uncertain, novel, or contested actions. It is the thin-floor-plus-thick-layer split argued
in dollars, and the reason the deterministic layer is not just a fallback but part of the
production design.

## Course Connection

This project productizes the Stanford CS 186 / PHIL 86 "How to Make a Moral
Agent" lesson that moral competence is contextual, social, learned, and
accountable, not a hand-coded lookup table. The deeper thesis is that morality
emerges under interdependence: repeated cooperation, shared stakes, trust,
partner choice, sanction, and norm feedback.

See [docs/moral-agent-learnings.md](docs/moral-agent-learnings.md).
See [docs/interdependence-design.md](docs/interdependence-design.md).
See [docs/interdependence-report.md](docs/interdependence-report.md).
