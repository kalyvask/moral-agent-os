# LLM Validation

Assessor: `OpenRouterAssessor`. Three Tier-1 numbers the repo was missing.

## Does the model match the shared judgment?

Routing labels (auto = appropriate, present-options = plural, otherwise inappropriate) compared to the three-rater model consensus and the author.

| Router | vs consensus | vs author |
| --- | ---: | ---: |
| Deterministic scaffold | 77.1% | 78.6% |
| Contextual model | 87.5% | 85.7% |

The contextual model matches the independent consensus 10% more often than the keyword scaffold. The cases the scaffold misses are exactly the ones the consensus calls inappropriate, which is the keyword-blindness ceiling again, now measured against shared judgment rather than the author alone.

## Is the safety advantage significant? (McNemar exact)

On the clear-inappropriate actions, the scaffold is right and the model wrong on 0; the model is right and the scaffold wrong on 5. Two-sided exact McNemar p = **0.062**.

The advantage trends in the model's favor but is not significant at p < 0.05 on this bank: the discordant set is small. This is the honest case for growing the scenario bank (more held-out families) so the test has power, not a sign the effect is absent.

## How stable is the twin-discrimination number?

Twin discrimination over 3 repeated runs: 100.0%, 100.0%, 100.0%. Mean **100.0%**, standard deviation 0.0%.

A stochastic model gives a distribution, not a point. Reporting the spread keeps the headline honest.
