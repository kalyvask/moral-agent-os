# LLM Validation

This is a historical OpenRouter validation snapshot. It was generated before the default
router enabled the interdependence, authority, universalizability, and patiency gates. Use
it as evidence that a contextual model can judge the bank, not as the current
model-vs-scaffold comparison.

Current default-router agreement is tracked in
[label-agreement.md](label-agreement.md): route behavior matches author labels **100.0%**
and model consensus **98.6%** on the 70-scenario bank.

## Historical Snapshot

Assessor: `OpenRouterAssessor`. Consensus excluded `anthropic/claude-sonnet-4.6` because it
was also the assessor model; remaining raters were `openai/gpt-5` and
`google/gemini-2.5-pro`.

| Router | vs consensus | vs author |
| --- | ---: | ---: |
| Deterministic scaffold, before default-gate expansion | 71.4% | 74.3% |
| Contextual model | 90.0% | 92.9% |

On clear-inappropriate actions, the old scaffold was right and the model wrong on 0; the
model was right and the old scaffold wrong on 12. Two-sided exact McNemar p was **0.000**.

Twin discrimination over 3 repeated model runs was 88.9%, 83.3%, 88.9%; mean **87.0%**,
standard deviation 2.6%.

## Next Rerun

Rerun `python -m bench.llm_validation --assessor openrouter` after setting the OpenRouter
API key to produce an apples-to-apples comparison against the current default router.
