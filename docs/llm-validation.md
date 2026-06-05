# LLM Validation

Assessor: `OpenRouterAssessor`. Three Tier-1 numbers the repo was missing.
Consensus excludes `anthropic/claude-sonnet-4.6` because it is the assessor model; remaining raters: `openai/gpt-5`, `google/gemini-2.5-pro`.

## Does the model match the shared judgment?

Route behavior compared to independent labels: auto must match appropriate, non-auto must match inappropriate, and confirm/escalate/present-options all count as acceptable handling for plural cases.

| Router | vs consensus | vs author |
| --- | ---: | ---: |
| Deterministic scaffold | 71.4% | 74.3% |
| Contextual model | 90.0% | 92.9% |

The contextual model matches the independent consensus 19% more often than the keyword scaffold. The cases the scaffold misses are exactly the ones the consensus calls inappropriate, which is the keyword-blindness ceiling again, now measured against shared judgment rather than the author alone.

## Is the safety advantage significant? (McNemar exact)

On the clear-inappropriate actions, the scaffold is right and the model wrong on 0; the model is right and the scaffold wrong on 12. Two-sided exact McNemar p = **0.000**.

The model's safety advantage is statistically significant at p < 0.05: it is not sampling noise.

## How stable is the twin-discrimination number?

Twin discrimination over 3 repeated runs: 88.9%, 83.3%, 88.9%. Mean **87.0%**, standard deviation 2.6%.

A stochastic model gives a distribution, not a point. Reporting the spread keeps the headline honest.
