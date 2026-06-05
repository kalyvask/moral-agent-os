# LLM Validation

This file is a historical consensus/significance snapshot from the earlier
56-scenario / 11-twin bank. The repo now has 70 scenarios and 18 same-action
twins, and [ablation-report-openrouter.md](ablation-report-openrouter.md)
contains a saved 70-scenario OpenRouter ablation run. The validation code now
uses route-behavior consistency rather than collapsing every confirm/escalate
into `inappropriate`. Rerun this report before using consensus/significance
numbers as a headline:

```bash
export OPENROUTER_API_KEY=...
python -m bench.llm_validation --assessor openrouter
```

The current validation harness also excludes the exact assessor model from the
model-rater consensus when they overlap, so the result is less circular than the
historical run below.

## Historical Result

Assessor: `OpenRouterAssessor`.

| Router | vs consensus | vs author |
| --- | ---: | ---: |
| Deterministic scaffold | 77.1% | 78.6% |
| Contextual model | 87.5% | 85.7% |

On the clear-inappropriate actions, the scaffold was right and the model wrong on
0; the model was right and the scaffold wrong on 5. Two-sided exact McNemar
p = **0.062**.

Twin discrimination over 3 repeated runs was 100.0%, 100.0%, 100.0%.
