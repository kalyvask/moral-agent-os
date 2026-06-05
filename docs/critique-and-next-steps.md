# Critique And Next Steps

## Graphs To Add

The repo should eventually include generated charts, not only textual benchmark
output. The best graphs are:

1. **Safety/friction frontier:** x-axis = unnecessary interventions, y-axis =
   context-inappropriate auto-executes. Plot `hard_rules`, `always_confirm`, and
   `normos`. This is the main "why this is better than rules" graph.
2. **Routing confusion matrix:** expected label vs route. This shows whether the
   runtime blocks clear bad actions, allows clear good actions, and surfaces
   plural cases as alternatives.
3. **Interdependence bar chart:** one-shot vs static policy vs interdependent
   learning across cooperation, autonomous cooperation, repair, and norm
   stability.
4. **Asymmetric dependence chart:** compare one-shot, static policy,
   interdependence, and third-party enforcement on stewardship, dependent harm,
   and public review.
5. **Shared intent chart:** compare Stag Hunt interdependence vs shared intent
   on autonomous cooperation and joint commitment.

## Runtime Diagram

```mermaid
flowchart TD
    Tool["Agent tool call"] --> Guard["guard_tool decorator"]
    Guard --> Proposal["ActionProposal"]
    Guard --> Context["ContextSnapshot"]
    Proposal --> Runtime["MoralAgentOS.assess"]
    Context --> Runtime
    Runtime --> Decision["MoralDecision"]
    Decision -->|allow| Execute["Execute tool"]
    Decision -->|confirm| User["Ask user"]
    Decision -->|alternatives| Options["Show interpretations"]
    Decision -->|escalate| Reviewer["Accountable review"]
    Decision -->|block| Stop["Do not execute"]
```

## Evaluation Diagram

```mermaid
flowchart LR
    Scenarios["Scenario bank"] --> Arms["Benchmark arms"]
    Arms --> HardRules["hard_rules"]
    Arms --> AlwaysConfirm["always_confirm"]
    Arms --> NormOS["normos"]
    HardRules --> Metrics["Safety/friction metrics"]
    AlwaysConfirm --> Metrics
    NormOS --> Metrics
    Interdependence["Interdependence environments"] --> SocialMetrics["Cooperation, repair, stewardship,<br/>public review, joint commitment"]
```

## What Is Strong

- The project has a real thesis, not just a generic guardrail: morality requires
  contextual appropriateness plus interdependent social conditions.
- The SDK is now usable: developers can call `assess()` or wrap tools with
  `guard_tool()`.
- The benchmark has falsifiers. Static policy can force compliance, but the
  report separates that from autonomous cooperation, repair, stewardship, public
  review, and shared intent.
- The deterministic scaffold is easy to run locally and in CI, which keeps the
  project legible before adding LLM complexity.

## What Is Weak

- The default assessor is heuristic. An LLM assessor now exists and emits the same schema,
  but the headline numbers are produced with the deterministic baseline unless a key is
  supplied, and the LLM's judgment quality has not been measured at scale yet.
- [improved] The scenario bank grew from 36 to 56, including same-action twins and
  held-out cases, but it still has no independent human labels or inter-rater agreement.
- The interdependence simulator is illustrative, not scientific. Its numbers are
  useful for product thinking but should not be presented as empirical proof.
- [addressed] The SDK now persists corrections, repair obligations, trust, and review
  history via `WorkspaceMemory`; `hydrate_context` fills a `ContextSnapshot` from storage.
- [addressed] The guard now integrates with LangChain, CrewAI, AutoGen, and OpenAI
  Agents-style tools through `adapters/`.

## Product Next Steps

1. **Generated reports:** add a script that writes CSV/Markdown/PNG-style chart
   artifacts from `bench.run` and `bench.interdependence`.
2. **Persistent norm memory:** store corrections, repair obligations, trust, and
   review history per stakeholder or workspace.
3. **Tool adapters:** add examples for `send_email`, `share_doc`, `update_crm`,
   `schedule_meeting`, and `run_code`.
4. **LLM assessor interface:** keep the deterministic assessor as the baseline,
   then add a structured LLM assessor that emits the same schema.
5. **Human-label workflow:** expand to 50-60 scenarios, add independent labels,
   and report inter-rater agreement.
6. **Review queue UI:** build a simple reviewer surface for escalated decisions.
7. **Agent-framework integrations:** provide wrappers for common tool-calling
   patterns so users can adopt the SDK without redesigning their agents.

## Near-Term Build Order

1. [done] `bench/report.py` generates Markdown, CSV, and JSON for the safety/friction
   benchmark, plus the confusion matrix.
2. [done] CSV and JSON outputs for both benchmark tracks in `bench/results/`.
3. [done] `docs/figures/` holds generated SVG charts (frontier, confusion matrix,
   interdependence, asymmetric, shared intent, ablation, memory).
4. [done] `ai_safety_os/memory.py` persists corrections, relationships, and review
   history, with a frozen-control comparison in `bench/memory_demo.py`.
5. [done] Tool adapters for LangChain, CrewAI, AutoGen, and OpenAI Agents in `adapters/`,
   with a runnable example. (A second multi-tool example agent is still a nice-to-have.)

## Built Since This Critique

- An LLM contextual assessor (`ai_safety_os/llm_assessor.py`) emitting the same schema.
- A context-ablation experiment (`bench/ablation.py`) that measures whether the
  same-action win is real or definitional, with the scenario bank grown to 56 including
  same-action twins and held-out, out-of-vocabulary cases.

The assessor-quality and human-label gaps (M2 at scale, M5) remain open and are stated
honestly in the README.
